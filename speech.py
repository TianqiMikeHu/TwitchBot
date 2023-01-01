from twitchrealtimehandler import TwitchAudioGrabber
import numpy as np
from io import BytesIO
from pydub import AudioSegment
from pydub.exceptions import CouldntEncodeError
import json
import requests
import mysql.connector.pooling
import tools
import os
import dotenv
import threading
import argparse
import time
import dotenv
from twitchio.ext import commands
import asyncio

class Bot(commands.Bot):
    def __init__(self, channel, debug):
        dotenv.load_dotenv()
        super().__init__(token=os.getenv('TWITCH_OAUTH_TOKEN'), prefix='~', initial_channels=[channel])
        self.channel = channel
        self.audio = audio_transcript(channel, debug)


    async def event_ready(self):
        print("CONENCTED TO TWITCH IRC")
        chan = self.get_channel(self.channel)
        while True:
            # we want the raw data not the numpy array to send it to google api
            audio_segment = self.audio.audio_grabber.grab_raw()
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
                transcript = self.audio.api_speech(data)
                if self.audio.debug:
                    print(transcript)
                if transcript is None:
                    continue
                
                transcript = transcript.lower()

                for item in self.audio.keywords:
                    if item[0] in transcript:
                        item[2]+=1
                        query = 'UPDATE bot.audio_key SET count=%s where keyword=%s'
                        tools.query(self.audio.pool, query, True, (item[2],item[0]))
                        asyncio.ensure_future(chan.send(f"{item[1]} (x{item[2]})"))
                        await asyncio.sleep(0.1)


class audio_transcript():
    def __init__(self, channel, debug):
        dotenv.load_dotenv()
        self.twitch_url = f'https://twitch.tv/{channel}'
        self.audio_grabber = None
        dbconfig = {
            "host":"localhost",
            "port":"3306",
            "user":"root",
            "password": os.getenv('DBPASS'),
            "database":"bot",
        }
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="pool3",
            pool_size=5,
            pool_reset_session=True,
            **dbconfig)

        self.exit_event = threading.Event()
        self.debug = debug
        self.keywords = []  # list of [keyword, response, count]
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
        query = 'SELECT * FROM bot.audio_key'
        result = tools.query(self.pool, query, False, None)

        for item in result:
            if item[3]:
                self.keywords.append([item[0], item[1], item[2]])



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


parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true', help='debug mode')
parser.set_defaults(debug=False)
opt = parser.parse_args()
bot = Bot('mike_hu_0_0', opt.debug)
bot.run()