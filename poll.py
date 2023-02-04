from twitchio.ext import commands
import dotenv
import os
import random
import requests
import poll_constant
from API import *
from twitchio.ext import routines

RUNNING = True

def poll():

    options = random.sample(poll_constant.OPTIONS, 4)

    body = {
        "broadcaster_id":"160025583", 
        "title":"Next Effect?", 
        "choices":[{ 
            "title": options[0]
        },
        {
            "title": options[1]
        },
        {
            "title": options[2]
        },
        {
            "title": options[3]
        }],
        "duration": 30
    }
    r = requests.post(url="https://api.twitch.tv/helix/polls/", headers=get_header3(), json=body)
    if r.status_code!=200:
        if r.status_code!=401:
            return f'[ERROR]: status code is {str(r.status_code)}'
        else:
            print("[ERROR]: status code is 401. Getting new access token...")
            refresh_token()
            r = requests.post(url="https://api.twitch.tv/helix/polls/", headers=get_header3(), json=body)
            if r.status_code!=204:
                return f'[ERROR]: status code is {str(r.status_code)}'
    return None


class Bot(commands.Bot):

    def __init__(self):
        dotenv.load_dotenv()
        super().__init__(token=os.getenv('TWITCH_OAUTH_TOKEN'), prefix='!', initial_channels=['mike_hu_0_0'])
        self.bot = os.getenv('BOT')

    async def event_ready(self):
        print("bot is ready")
        self.run_poll.start()

    async def event_message(self, msg):
        if msg.author is None:
            return
        
        args = msg.content.split()
        command = args[0].lower()
        author = msg.author.display_name

        global RUNNING

        if command == "!pause":
            if RUNNING:
                RUNNING = False
                self.run_poll.cancel()
                await msg.channel.send("Poll routine paused.")
            else:
                return
        elif command == "!unpause":
            if RUNNING:
                return
            else:
                RUNNING = True
                self.run_poll.start()
                await msg.channel.send("Poll routine resumed.")
    
    @routines.routine(seconds=60.0, iterations=None)
    async def run_poll(self):
        poll()
    

bot = Bot()
bot.run()