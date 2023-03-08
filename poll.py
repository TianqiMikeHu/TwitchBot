from twitchio.ext import commands
import dotenv
import os
import random
import requests
import poll_options



dotenv.load_dotenv()

CLIENTID = os.getenv('CLIENTID')
CLIENTSECRET = os.getenv('CLIENTSECRET')



def refresh_token():
    refresh = os.getenv('REFRESH_ANNA')
    refresh = requests.utils.quote(refresh, safe='')
    token_request = f"https://id.twitch.tv/oauth2/token?client_id={CLIENTID}&client_secret={CLIENTSECRET}&grant_type=refresh_token&refresh_token="+refresh
    r = requests.post(url=token_request, headers={"Content-Type":"application/x-www-form-urlencoded"})

    print("User access token refreshed")

    token = (r.json()).get('access_token')
    refresh = (r.json()).get('refresh_token')

    dotenv.set_key('.env', 'ACCESSTOKEN_ANNA', token)
    dotenv.set_key('.env', 'REFRESH_ANNA', refresh)

    return


def get_header():
    dotenv.load_dotenv(override=True)
    header = {"Client-ID": CLIENTID, 
                "Authorization": f"Bearer {os.getenv('ACCESSTOKEN_ANNA')}", 
                "Content-Type":"application/json"}
    return header


def poll():

    options = random.sample(poll_options.OPTIONS, 4)

    body = {
        "broadcaster_id":"598261113", 
        "title":"Next Stipulation?", 
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
    r = requests.post(url="https://api.twitch.tv/helix/polls/", headers=get_header(), json=body)

    if r.status_code==401:
        print("[ERROR]: status code is 401. Getting new access token...")
        refresh_token()
        r = requests.post(url="https://api.twitch.tv/helix/polls/", headers=get_header(), json=body)

    if r.status_code!=200:
        print(f'[ERROR]: status code is {str(r.status_code)}')

    return None


class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=os.getenv('TWITCH_OAUTH_TOKEN'), prefix='!', initial_channels=['annaagtapp'])
        self.bot = os.getenv('BOT')

    async def event_ready(self):
        print("bot is ready")

    async def event_message(self, msg):
        if msg.author is None:
            return
        
        args = msg.content.split()
        command = args[0].lower()
        authorized = msg.author.is_mod

        if command == "!poll" and authorized:
            poll()


bot = Bot()
bot.run()