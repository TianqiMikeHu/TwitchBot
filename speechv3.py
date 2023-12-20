from twitchrealtimehandler import TwitchAudioGrabber
import numpy as np
from io import BytesIO
from pydub import AudioSegment
from pydub.exceptions import CouldntEncodeError
import json
import requests
import os
import threading
import argparse
from twitchio.ext import commands
import time
import datetime
import queue
from twitchio.ext import routines
import boto3
import sys
from collections import deque

COOLDOWN = 90
q = queue.Queue()


class Bot(commands.Bot):
    def __init__(self, channel):
        client = boto3.client("dynamodb", region_name="us-west-2")
        response = client.get_item(
            Key={
                "CookieHash": {
                    "S": "681131749",
                }
            },
            TableName="CF-Cookies",
        )
        user_access_token = response["Item"]["AccessToken"]["S"]
        super().__init__(
            token=f"oauth:{user_access_token}", prefix="!", initial_channels=[channel]
        )
        self.channel = channel

    async def event_ready(self):
        print("CONNECTED TO TWITCH IRC", flush=True)
        # await self.connected_channels[0].send("bot is online")
        self.poll.start(stop_on_error=False)
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

    async def event_message(self, msg):
        if msg.author is None:
            return
        name = msg.author.name.lower()
        if name == self.channel or name == "mike_hu_0_0":
            if msg.content.lower() == "!restart":
                await msg.channel.send("Terminating instance...")
                response, key = self.save_to_s3()
                if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                    await msg.channel.send(f"Transcript Key: {key}")
                r = requests.get(
                    url="http://169.254.169.254/latest/meta-data/instance-id"
                )
                ec2 = boto3.client("ec2", region_name="us-west-2")
                response = ec2.terminate_instances(
                    InstanceIds=[
                        r.text,
                    ]
                )
        elif name == "a_poorly_written_bot":
            if msg.content == "Stream is offline. Autoscaling in...":
                response, key = self.save_to_s3()
                if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                    await msg.channel.send(f"Transcript Key: {key}")
                autoscaling = boto3.client("autoscaling", region_name="us-west-2")
                response = autoscaling.set_desired_capacity(
                    AutoScalingGroupName=f"AutoScaling-{self.channel}",
                    DesiredCapacity=0,
                    HonorCooldown=False,
                )
                print(response)
        return

    @routines.routine(seconds=0.1, iterations=None)
    async def poll(self):
        try:
            item = q.get(block=False)
            await self.connected_channels[0].send(item)
        except:
            pass


class audio_transcript:
    def __init__(self, channel, debug):
        self.channel = channel
        self.twitch_url = f"https://twitch.tv/{channel}"
        self.audio_grabber = None
        self.audio_grabber_2 = None
        self.writer = open("output.txt", "w")

        self.exit_event = threading.Event()
        self.debug = debug
        self.keywords = []

        self.deque = deque(maxlen=3)
        self.deque_duplicate = deque(maxlen=2)

        self.item_lock = threading.Lock()
        self.write_lock = threading.Lock()

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
            self.audio_grabber_2 = TwitchAudioGrabber(
                twitch_url=self.twitch_url,
                dtype=np.int16,
                segment_length=9,
                channels=1,
                rate=16000,
            )
        except ValueError:
            print("Could not connect to stream", flush=True)

    def load_audio_keywords(self):
        ddb = boto3.client("dynamodb", region_name="us-west-2")
        response = ddb.scan(TableName=f"Speech-{self.channel.lower()}")
        # keyword, response, count
        self.keywords = response["Items"]
        for item in self.keywords:
            item["timestamp"] = {}
            item["timestamp"]["N"] = 0

    def extract_transcript(self, resp: str):
        """
        Extract the first results from google api speech recognition
        Args:
            resp: response from google api speech.
        Returns:
            The more confident prediction from the api
            or an error if the response is malformatted
        """
        if "result" not in resp:
            raise ValueError({"Error non valid response from api: {}".format(resp)})
        for line in resp.split("\n"):
            try:
                line_json = json.loads(line)
                out = line_json["result"][0]["alternative"][0]["transcript"]
                return out
            except:
                continue

    def api_speech(self, data):
        """Call google api to get the transcript of an audio"""
        # Random header
        userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36"

        headers = {
            "Content-Type": "audio/x-flac; rate=16000;",
            "User-Agent": userAgent,
        }
        params = (
            ("client", "chromium"),
            ("pFilter", "0"),
            ("lang", "en"),
            ("key", "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"),
        )

        proxies = None

        if len(data) == 0:
            return

        # api call
        try:
            response = requests.post(
                "http://www.google.com/speech-api/v2/recognize",
                proxies=proxies,
                headers=headers,
                params=params,
                data=data,
            )
        except Exception as inst:
            print(inst, flush=True)

        # Parse api response
        try:
            transcript = self.extract_transcript(response.text)
            return transcript
        except Exception as inst:
            print(inst, flush=True)
            return

    def pull_audio_segments(self):
        while True:
            audio_segment = self.audio_grabber.grab_raw()
            if audio_segment:
                self.deque.append(audio_segment)
            audio_segment = self.audio_grabber_2.grab_raw()
            if audio_segment:
                self.deque_duplicate.append(audio_segment)

    def transcribe(self):
        source_id = 0
        while True:
            if self.deque:
                raw = BytesIO(self.deque.popleft())
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
                transcript = self.api_speech(data)

                if transcript is None:
                    continue
                if self.debug:
                    with self.write_lock:
                        self.writer.write(f"Source {source_id}: {transcript}\n")
                        self.writer.flush()

                transcript = transcript.lower()

                for item in self.keywords:
                    if item["keyword"]["S"] in transcript:
                        timestamp = time.time()
                        with self.item_lock:
                            if timestamp - item["timestamp"]["N"] < COOLDOWN:
                                print(
                                    f"\nKeyword \"{item['keyword']['S']}\" was throttled: delta={timestamp-item['timestamp']['N']}\n",
                                    flush=True,
                                )
                                continue
                            item["timestamp"]["N"] = timestamp
                        if "count" not in item:
                            print(f"{item['response']['S']}", flush=True)
                            q.put(f"{item['response']['S']}")
                            continue
                        ddb = boto3.client("dynamodb", region_name="us-west-2")
                        with self.item_lock:
                            count = int(item["count"]["N"]) + 1
                            item["count"]["N"] = str(count)
                            print(
                                f"{item['response']['S']} (x{item['count']['N']})",
                                flush=True,
                            )
                            q.put(f"{item['response']['S']} (x{item['count']['N']})")
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

    def transcribe_duplicate(self):
        source_id = 1
        while True:
            if self.deque_duplicate:
                raw = BytesIO(self.deque_duplicate.popleft())
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
                transcript = self.api_speech(data)

                if transcript is None:
                    continue
                if self.debug:
                    with self.write_lock:
                        self.writer.write(f"Source {source_id}: {transcript}\n")
                        self.writer.flush()

                transcript = transcript.lower()

                for item in self.keywords:
                    if item["keyword"]["S"] in transcript:
                        timestamp = time.time()
                        with self.item_lock:
                            if timestamp - item["timestamp"]["N"] < COOLDOWN:
                                print(
                                    f"\nKeyword \"{item['keyword']['S']}\" was throttled: delta={timestamp-item['timestamp']['N']}\n",
                                    flush=True,
                                )
                                continue
                            item["timestamp"]["N"] = timestamp
                        if "count" not in item:
                            print(f"{item['response']['S']}", flush=True)
                            q.put(f"{item['response']['S']}")
                            continue
                        ddb = boto3.client("dynamodb", region_name="us-west-2")
                        with self.item_lock:
                            count = int(item["count"]["N"]) + 1
                            item["count"]["N"] = str(count)
                            print(
                                f"{item['response']['S']} (x{item['count']['N']})",
                                flush=True,
                            )
                            q.put(f"{item['response']['S']} (x{item['count']['N']})")
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
sys.stderr = open("error.txt", "w")

audio = audio_transcript(opt.listen, opt.debug)
threading.Thread(target=audio.pull_audio_segments, daemon=True).start()
threading.Thread(target=audio.transcribe, daemon=True).start()
threading.Thread(target=audio.transcribe_duplicate, daemon=True).start()


bot = Bot(opt.write)
bot.run()
