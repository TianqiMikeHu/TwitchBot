from twitchrealtimehandler import TwitchAudioGrabber
import numpy as np
from io import BytesIO
from pydub import AudioSegment
from pydub.exceptions import CouldntEncodeError
import threading
import argparse
from twitchio.ext import commands
import time
import datetime
import queue
from twitchio.ext import routines
import boto3
from collections import deque
from deepgram import Deepgram
import asyncio
import os
import sys
import re
import requests


COOLDOWN = 120
PAUSED = None
RECEIPT = None
VARIABLES_TABLE = "inabot-variables"
KEYWORDS = []
EXPIRATION = None
writer = open("output.txt", "a")
processing_queue = queue.Queue()
outbound_queue = queue.Queue()
new_deque = deque(maxlen=3)


def online(channel):
    header = {
        "Client-ID": "6yz6w1tnl13svb5ligch31aa5hf4ty",
        "Authorization": f"Bearer {get_acess_token()}",
        "Content-Type": "application/json",
    }
    r = requests.get(
        url=f"https://api.twitch.tv/helix/streams?user_login={channel}",
        headers=header,
    )
    return r.json()["data"]


def get_acess_token():
    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.get_item(
        Key={
            "CookieHash": {
                "S": "687759326",
            }
        },
        TableName="CF-Cookies",
    )
    return response["Item"]["AccessToken"]["S"]


class Bot(commands.Bot):
    def __init__(self, channel):
        super().__init__(
            token=f"oauth:{get_acess_token()}", prefix="!", initial_channels=[channel]
        )
        self.channel = channel

    async def event_ready(self):
        print("CONNECTED TO TWITCH IRC", flush=True)

        if not online(self.channel):
            await self.shutdown()
            sys.exit()

        self.poll.start(stop_on_error=False)
        self.scan.start(stop_on_error=False)
        print("POLL STARTED", flush=True)

    def save_to_s3(self):
        f = open("output.txt", "r")
        text = f.read().encode("utf-8")
        s3 = boto3.client("s3", region_name="us-west-2")
        title = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
        title = title.replace(":", "-")
        response = s3.put_object(
            ACL="bucket-owner-full-control",
            Body=text,
            Bucket="inabot",
            ContentType="text/plain",
            Key=f"transcribe-new/{self.channel}/{title}.txt",
        )
        return response, f"{self.channel}/{title}"

    async def shutdown(self):
        response, key = self.save_to_s3()
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            await self.connected_channels[0].send(f"Transcript Key: {key}")
        autoscaling = boto3.client("autoscaling", region_name="us-west-2")
        response = autoscaling.set_desired_capacity(
            AutoScalingGroupName=f"AutoScaling-{self.channel}",
            DesiredCapacity=0,
            HonorCooldown=False,
        )
        print(response)
    
    async def pause_feedback(self, pause):
        ddb = boto3.client("dynamodb", region_name="us-west-2")
        response = ddb.update_item(
            Key={
                "var_name": {
                    "S": "pause",
                },
                "var_type": {"S": "CUSTOM"},
            },
            TableName=VARIABLES_TABLE,
            UpdateExpression="SET var_val=:v",
            ExpressionAttributeValues={":v": {"BOOL": pause}},
        )

    async def remove_word(self, keyword):
        ddb = boto3.client("dynamodb", region_name="us-west-2")
        response = ddb.delete_item(
            Key={
                "keyword": {
                    "S": keyword,
                }
            },
            TableName=f"Speech-{self.channel}",
        )

    async def event_message(self, msg):
        global PAUSED
        global RECEIPT
        if msg.echo:
            return
        if not msg.author.is_mod:
            return
        cmd = msg.content.lower().split()[0]
        if cmd == "!pause":
            if PAUSED:
                await msg.channel.send(
                    f"Speech recognition feedback is already paused."
                )
                return
            PAUSED = True
            await self.pause_feedback(PAUSED)
            await msg.channel.send(f"Speech recognition feedback paused.")
            return
        if cmd == "!resume":
            if not PAUSED:
                await msg.channel.send(
                    f"Speech recognition feedback is already running."
                )
                return
            PAUSED = False
            await self.pause_feedback(PAUSED)
            await msg.channel.send(f"Speech recognition feedback resumed.")
            return
        if cmd == "!receipt":
            if not RECEIPT:
                await msg.channel.send("no data inaboxNo")
            else:
                await msg.channel.send(RECEIPT)
            return
        if msg.author.name == "inabot44":
            if msg.content == "Stream is offline. Autoscaling in...":
                await self.shutdown()
            if re.search(r"Adding banned word \".+\"\.\.\.", msg.content):
                print(f"Reloading for banned word")
                os.execl(sys.executable, sys.executable, *sys.argv)
        return

    @routines.routine(seconds=0.1, iterations=None)
    async def poll(self):
        try:
            item = outbound_queue.get(block=False)
            await self.connected_channels[0].send(item)
        except:
            pass

    @routines.routine(seconds=10, iterations=None)
    async def scan(self):
        global EXPIRATION
        if EXPIRATION:
            timestamp = time.time()
            if timestamp > float(EXPIRATION["expiration"]["N"]):
                print("Removing banned word...")
                summary = f"The banned word {EXPIRATION['keyword']['S']} has expired. Total count: {KEYWORDS[EXPIRATION['index']]['count']['N']}"
                await self.remove_word(EXPIRATION['keyword']['S'])
                EXPIRATION = None
                await self.connected_channels[0].send(summary)
                print(f"Reloading after banned word")
                os.execl(sys.executable, sys.executable, *sys.argv)


class audio_input:
    def __init__(self, channel):
        self.channel = channel
        self.twitch_url = f"https://twitch.tv/{channel}"
        self.audio_grabber = None

        self.exit_event = threading.Event()

        self.load_audio_keywords()
        self.start_listening()

    def start_listening(self):
        try:
            self.audio_grabber = TwitchAudioGrabber(
                twitch_url=self.twitch_url,
                dtype=np.int16,
                segment_length=5,
                channels=1,
                rate=16000,
            )
        except ValueError:
            print("Could not connect to stream", flush=True)

    def load_audio_keywords(self):
        ddb = boto3.client("dynamodb", region_name="us-west-2")
        global PAUSED
        global KEYWORDS
        global EXPIRATION
        try:
            response = ddb.get_item(
                Key={
                    "var_name": {
                        "S": f"pause",
                    },
                    "var_type": {"S": "CUSTOM"},
                },
                TableName=VARIABLES_TABLE,
            )
            PAUSED = response["Item"]["var_val"]["BOOL"]
            print(f"Current status: {PAUSED}", flush=True)
            response = ddb.scan(TableName=f"Speech-{self.channel}")
            # keyword, response, count
            KEYWORDS = response["Items"]
            for i in range(len(KEYWORDS)):
                KEYWORDS[i]["timestamp"] = {}
                KEYWORDS[i]["timestamp"]["N"] = 0
                if KEYWORDS[i].get('expiration'):
                    EXPIRATION = KEYWORDS[i]
                    EXPIRATION["index"] = i
                    print(EXPIRATION)
        except:
            return

    async def pull_audio_segments(self):
        while True:
            await asyncio.sleep(0)
            audio_segment = self.audio_grabber.grab_raw()
            if audio_segment:
                new_deque.append(audio_segment)

    async def extract_transcript(self, data):
        try:
            transcript = data["channel"]["alternatives"][0]["transcript"]
            if transcript:
                processing_queue.put(transcript)
        except:
            return

    async def process_transcript(self):
        global RECEIPT
        while True:
            await asyncio.sleep(0)
            try:
                transcript = processing_queue.get(block=False)
            except:
                continue
            writer.write(f"{transcript}\n")
            writer.flush()
            # outbound_queue.put(transcript)
            print(transcript, flush=True)
            transcript2 = transcript.lower()

            for item in KEYWORDS:
                if re.search(f"\\b{item['keyword']['S']}\\b", transcript2):
                    timestamp = time.time()

                    if PAUSED:
                        print(
                            f"\nKeyword \"{item['keyword']['S']}\" was throttled: PAUSED"
                        )
                        continue
                    if item.get('expiration'):
                        cooldown = 0
                    else:
                        cooldown = COOLDOWN
                    if timestamp - item["timestamp"]["N"] < cooldown:
                        print(
                            f"\nKeyword \"{item['keyword']['S']}\" was throttled: delta={timestamp-item['timestamp']['N']}\n",
                            flush=True,
                        )
                        continue
                    item["timestamp"]["N"] = timestamp
                    RECEIPT = transcript

                    if "count" not in item:
                        print(f"{item['response']['S']}", flush=True)
                        outbound_queue.put(f"{item['response']['S']}")
                        continue

                    ddb = boto3.client("dynamodb", region_name="us-west-2")

                    count = int(item["count"]["N"]) + 1
                    item["count"]["N"] = str(count)
                    print(
                        f"{item['response']['S']} (x{item['count']['N']})",
                        flush=True,
                    )
                    outbound_queue.put(
                        f"{item['response']['S']} (x{item['count']['N']})"
                    )
                    response = ddb.update_item(
                        TableName=f"Speech-{self.channel.lower()}",
                        ExpressionAttributeNames={
                            "#C": "count",
                        },
                        ExpressionAttributeValues={
                            ":c": {
                                "N": item["count"]["N"],
                            }
                        },
                        Key={
                            "keyword": {
                                "S": item["keyword"]["S"],
                            }
                        },
                        ReturnValues="ALL_NEW",
                        UpdateExpression="SET #C = :c",
                    )


def onclose(msg):
    print(f"Connection closed with code {msg}")
    os.execl(sys.executable, sys.executable, *sys.argv)


async def main():
    try:
        # Initialize the Deepgram SDK
        client = boto3.client("dynamodb", region_name="us-west-2")
        response = client.get_item(
            Key={
                "CookieHash": {
                    "S": "DEEPGRAM_API_KEY",
                }
            },
            TableName="CF-Cookies",
        )
        deepgram = Deepgram(response["Item"]["AccessToken"]["S"])

        # Create a websocket connection to Deepgram
        # In this example, punctuation is turned on, interim results are turned off, and language is set to UK English.
        try:
            deepgramLive = await deepgram.transcription.live(
                {
                    "smart_format": True,
                    "interim_results": False,
                    "language": "en-US",
                    "model": "nova-2",
                    "filler_words": True,
                    "endpointing": False,
                }
            )
        except Exception as e:
            print(f"Could not open socket: {e}")
            return

        # Listen for the connection to close
        deepgramLive.register_handler(deepgramLive.event.CLOSE, onclose)

        # Listen for any transcripts received from Deepgram and write them to the console
        deepgramLive.register_handler(
            deepgramLive.event.TRANSCRIPT_RECEIVED, audio.extract_transcript
        )

        # Listen for the connection to open and send streaming audio from the URL to Deepgram
        while True:
            await asyncio.sleep(0)
            if new_deque:
                raw = BytesIO(new_deque.popleft())
                try:
                    raw_wav = AudioSegment.from_raw(
                        raw, sample_width=2, frame_rate=16000, channels=1
                    )
                except CouldntEncodeError:
                    print("could not decode", flush=True)
                    continue
                raw_flac = BytesIO()
                raw_wav.export(raw_flac, format="flac")
                data = raw_flac.read()
                deepgramLive.send(data)
        # Indicate that we've finished sending data by sending the customary zero-byte message to the Deepgram streaming endpoint, and wait until we get back the final summary metadata object
        # await deepgramLive.finish()
    except:
        onclose(-1)


parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true", help="debug mode")
parser.add_argument(
    "--listen", default="mike_hu_0_0", help="channel to listen to", required=True
)
parser.add_argument(
    "--write", default="mike_hu_0_0", help="channel to send message to", required=True
)
parser.set_defaults(debug=False)
opt = parser.parse_args()

audio = audio_input(opt.listen)

threading.Thread(
    target=asyncio.run, args=(audio.pull_audio_segments(),), daemon=True
).start()
threading.Thread(
    target=asyncio.run, args=(audio.process_transcript(),), daemon=True
).start()
threading.Thread(target=asyncio.run, args=(main(),), daemon=True).start()

bot = Bot(opt.write)
bot.run()
