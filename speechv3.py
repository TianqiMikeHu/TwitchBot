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
import queue
from twitchio.ext import routines
import boto3

COOLDOWN = 90
q = queue.Queue()

class Bot(commands.Bot):
    def __init__(self, channel):
        ssm = boto3.client('ssm', region_name='us-west-2')
        response = ssm.get_parameter(
            Name='TWITCH_OAUTH_TOKEN',
            WithDecryption=True
        )
        super().__init__(response['Parameter']['Value'], prefix='!', initial_channels=[channel])
        self.channel = channel


    async def event_ready(self):
        print("CONNECTED TO TWITCH IRC")
        await self.connected_channels[0].send("bot is online")
        self.poll.start(stop_on_error=False)
        print("POLL STARTED")
        

    async def event_message(self, msg):
        if msg.author is None:
            return
        name = msg.author.name.lower()
        if name == self.channel or name == 'mike_hu_0_0':
            if msg.content.lower() == "!restart":
                await msg.channel.send("Terminating instance...")
                r = requests.get(url="http://169.254.169.254/latest/meta-data/instance-id")
                import boto3
                client = boto3.client('ec2', region_name='us-west-2')
                response = client.terminate_instances(
                    InstanceIds=[
                        r.text,
                    ]
                )
        return
    
    @routines.routine(seconds=0.1, iterations=None)
    async def poll(self):
        try:
            item = q.get(block=False)
            await self.connected_channels[0].send(item)
        except:
            pass


class audio_transcript():
    def __init__(self, channel, debug):
        self.channel = channel
        self.twitch_url = f'https://twitch.tv/{channel}'
        self.audio_grabber = None

        self.exit_event = threading.Event()
        self.debug = debug
        self.keywords = [] 
        self.load_audio_keywords()
        self.start_listening()


    def start_listening(self):
        try:
            self.audio_grabber = TwitchAudioGrabber(twitch_url=self.twitch_url,
                                       dtype=np.int16,
                                       segment_length=5,
                                       channels=1,
                                       rate=16000)
        except ValueError:
            print("Could not connect to stream")
            return


    def load_audio_keywords(self):
        ddb = boto3.client('dynamodb', region_name='us-west-2')
        response = ddb.scan(
            TableName=f'Speech-{self.channel.lower()}'
        )
        # keyword, response, count
        self.keywords = response['Items']
        for item in self.keywords:
            item['timestamp'] = {}
            item['timestamp']['N'] = 0


    def extract_transcript(self, resp: str):
        """
        Extract the first results from google api speech recognition
        Args:
            resp: response from google api speech.
        Returns:
            The more confident prediction from the api 
            or an error if the response is malformatted
        """
        if 'result' not in resp:
            raise ValueError({'Error non valid response from api: {}'.format(resp)})
        for line in resp.split("\n"):
            try:
                line_json = json.loads(line)
                out = line_json['result'][0]['alternative'][0]['transcript']
                return out
            except:
                continue


    def api_speech(self, data):
        """Call google api to get the transcript of an audio"""
            # Random header
        userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36"

        headers = {
            'Content-Type': 'audio/x-flac; rate=16000;',
            'User-Agent': userAgent,
        }
        params = (
            ('client', 'chromium'),
            ('pFilter', '0'),
            ('lang', 'en'),
            ('key', 'AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw'),
        )

        proxies = None

        if len(data) == 0:
            return

        # api call
        try:
            response = requests.post('http://www.google.com/speech-api/v2/recognize',
                                    proxies=proxies,
                                    headers=headers,
                                    params=params,
                                    data=data)
        except Exception as inst:
            print(inst)

        # Parse api response
        try:
            transcript = self.extract_transcript(response.text)
            return transcript
        except Exception as inst:
            print(inst)
            return
        
    def transcribe(self):
        while True:
            # we want the raw data not the numpy array to send it to google api
            audio_segment = self.audio_grabber.grab_raw()
            if audio_segment:
                raw = BytesIO(audio_segment)
                try:
                    raw_wav = AudioSegment.from_raw(
                        raw, sample_width=2, frame_rate=16000, channels=1)
                except CouldntEncodeError:
                    print("could not decode")
                    continue
                raw_flac = BytesIO()
                raw_wav.export(raw_flac, format='flac')
                data = raw_flac.read()
                transcript = self.api_speech(data)
                
                if self.debug:
                    print(transcript)
                if transcript is None:
                    continue       

                transcript = transcript.lower()

                for item in self.keywords:
                    if item['keyword']['S'] in transcript:
                        timestamp = time.time()
                        if timestamp-item['timestamp']['N']<COOLDOWN:
                            print(f"\nKeyword \"{item[0]}\" was throttled: delta={timestamp-item['timestamp']['N']}\n")
                            continue
                        item['timestamp']['N'] = timestamp
                        if 'count' not in item:
                            print(f"{item['response']['S']}")
                            q.put(f"{item['response']['S']}")
                            continue
                        count = int(item['count']['N'])+1
                        item['count']['N'] = str(count)
                        print(f"{item['response']['S']} (x{item['count']['N']})")
                        q.put(f"{item['response']['S']} (x{item['count']['N']})")
                        ddb = boto3.client('dynamodb', region_name='us-west-2')
                        response = ddb.update_item(
                            TableName=f'Speech-{self.channel.lower()}',
                            ExpressionAttributeNames={
                                '#C': 'count',
                            },
                            ExpressionAttributeValues={
                                ':c': {
                                    'N': item['count']['N'],
                                }
                            },
                            Key={
                                'keyword': {
                                    'S': item['keyword']['S'],
                                }
                            },
                            ReturnValues='ALL_NEW',
                            UpdateExpression='SET #C = :c'
                        )


parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true', help='debug mode')
parser.add_argument('--listen', default='mike_hu_0_0', help='channel to listen to', required=True)
parser.add_argument('--write', default='mike_hu_0_0', help='channel to send message to', required=True)
parser.set_defaults(debug=False)
opt = parser.parse_args()

audio = audio_transcript(opt.listen, opt.debug)
threading.Thread(target=audio.transcribe, daemon=True).start()



bot = Bot(opt.write)
bot.run()
