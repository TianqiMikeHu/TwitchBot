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
import socket


HOST = 'irc.chat.twitch.tv'
PORT = 6667
NICK = 'a_poorly_written_bot'

# HOST = 'irc-ws.chat.twitch.tv'
# PORT = 443

def say(message, channel, password):
    # password = os.getenv('TWITCH_OAUTH_TOKEN')
    # print(password)
    try:
        s = socket.socket()
    except:
        raise Exception("Socket Creation")

    try:
        s.connect((HOST, PORT))
    except:
        s.close()
        raise Exception("Connect")

    try:
        s.sendall(f"PASS {password}\r\n".encode('utf-8'))
        s.sendall(f"NICK {NICK}\r\n".encode('utf-8'))
        s.sendall(f"JOIN #{channel}\r\n".encode('utf-8'))
        s.sendall(f"PRIVMSG #{channel} : {message}\r\n".encode('utf-8'))
        s.sendall(f"PART #{channel}\r\n".encode('utf-8'))
    except:
        raise Exception("Socket Error")
    finally:
        s.shutdown(socket.SHUT_RDWR)
        s.close()



class audio_transcript():
    def __init__(self, channel, debug):
        dotenv.load_dotenv()
        self.twitch_url = f'https://twitch.tv/{channel}'
        self.channel = channel
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
        self.password = os.getenv('TWITCH_OAUTH_TOKEN')
        self.keywords = []  # list of [keyword, response, count]
        self.load_audio_keywords()
        self.start_listening()


    def start_listening(self):
        self.exit_event = threading.Event()
        try:
            self.audio_grabber = TwitchAudioGrabber(twitch_url=self.twitch_url,
                                       dtype=np.int16,
                                       segment_length=5,
                                       channels=1,
                                       rate=16000)
        except ValueError:
            print("Could not connect to stream")
            return
        # self.thread = threading.Thread(target=self.transcribe)
        # self.thread.start()
        self.transcribe()


    def stop_listening(self):
        self.exit_event.set()
        time.sleep(0.2)
        self.audio_grabber = None

    def toggle_debug(self):
        if self.debug:
            self.debug = False
            return "Debug mode off"
        else:
            self.debug = True
            return "Debug mode on"


    def load_audio_keywords(self):
        query = 'SELECT * FROM bot.audio_key_annaagtapp'
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


    # THIS IS MEANT TO BE A THREAD
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
                    if item[0] in transcript:
                        item[2]+=1
                        query = 'UPDATE bot.audio_key_annaagtapp SET count=%s where keyword=%s'
                        tools.query(self.pool, query, True, (item[2],item[0]))
                        say(f"{item[1]} (x{item[2]})", self.channel, self.password)
        # print("Stopping thread...")
        # sys.exit()


parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true', help='debug mode')
parser.set_defaults(debug=False)
opt = parser.parse_args()
audio = audio_transcript('annaagtapp', opt.debug)


# thread = threading.Thread(target=say, args=("abc", "mike_hu_0_0"))
# thread.start()
# thread.join()
# thread2 = threading.Thread(target=say, args=("def", "mike_hu_0_0"))
# thread2.start()
# thread2.join()
# thread3 = threading.Thread(target=say, args=("ghi", "mike_hu_0_0"))
# thread3.start()
# thread3.join()
# say("abc", "mike_hu_0_0")
# time.sleep(3)
# say("def", "mike_hu_0_0", 'oauth:2molxdrwam7bgu3kd82zdjoy5pgesg')
# time.sleep(3)
# say("ghi", "mike_hu_0_0")