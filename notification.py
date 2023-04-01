from twitchio.ext import commands
import dotenv
import os
import requests


DEVICE = 'mike-iphone'

channels = ["mike_hu_0_0", "thelastofchuck", "inabox44", "breakingpointes", "buritters", "annaagtapp", "mikkigemu", "shadowdaze"]
key_words = ["mike"]
exclude_key_words = ["mike and ike", "mike n ike", "mikehu4", "johnmike"]
key_names = []

class Bot(commands.Bot):

    def __init__(self):
        dotenv.load_dotenv()
        super().__init__(token=os.getenv('TWITCH_OAUTH_TOKEN'), prefix='!', initial_channels=channels)
        self.bot = os.getenv('BOT')
        self.app_token = os.getenv('PUSHOVER_APP_TOKEN')
        self.user_token = os.getenv('PUSHOVER_USER_TOKEN')


    async def event_ready(self):
        print("bot is ready")


    def pushover(self, message, author, channel):
        body = {
            'token': self.app_token,
            'user': self.user_token,
            'device': DEVICE,
            'title': channel,
            'message': f'{author}: {message}'
        }

        r = requests.post('https://api.pushover.net/1/messages.json', json=body)

        if r.status_code!=200:
            print(r.status_code)
        return


    def get_header(self):
        dotenv.load_dotenv(override=True)
        header = {"Client-ID": os.getenv('CLIENTID'), 
                    "Authorization":"Bearer {0}".format(os.getenv('ACCESSTOKEN')), 
                    "Content-Type":"application/json"}
        return header


    def new_access_token(self):
        token_request = f"https://id.twitch.tv/oauth2/token?client_id={os.getenv('CLIENTID')}&client_secret={os.getenv('CLIENTSECRET')}&grant_type=client_credentials"
        r = requests.post(url=token_request)
        token = (r.json()).get('access_token')
        dotenv.set_key('.env', 'ACCESSTOKEN', token)
        return token


    def channel_name(self, name):
        r = requests.get(url="https://api.twitch.tv/helix/users?login={0}".format(name), headers=self.get_header())
        if r.status_code!=200:
            if r.status_code!=401:
                return f'[ERROR]: status code is {str(r.status_code)}', 2
            else:
                print("[ERROR]: status code is 401. Getting new access token...")
                token = self.new_access_token()
                # print(f'The new access token is: {token}')
                r = requests.get(url="https://api.twitch.tv/helix/users?login={0}".format(name), headers=self.get_header())
                if r.status_code!=200:
                    return f'[ERROR]: status code is {str(r.status_code)}', 2
        data = r.json()
        if len(data.get('data'))==0:
            return "[ERROR]: User not found", 1
        channel_name = data.get('data')[0].get('display_name')
        return channel_name, 0


    async def event_message(self, msg):
        if msg.author is None:
            return
        
        if msg.author.name.lower() == self.bot:     # ignore self
            return
        

        lower_case = msg.content.lower()

        if "boring" in lower_case and msg.author.name.lower()=="mag_7798":
            await msg.channel.send("\"Anna is the opposite of boring\" - loyal viewer, mag")

        # if msg.author.name.lower() in key_names or msg.author.name.lower() == msg.channel.name:
        if msg.author.name.lower() in key_names:
            chan_name, status = self.channel_name(msg.channel.name)
            if status!=0:
                print(chan_name)
                self.pushover(msg.content, msg.author.display_name, msg.channel.name)
            else:
                self.pushover(msg.content, msg.author.display_name, chan_name)
            return

        for e in exclude_key_words:
            if e in lower_case:
                print(lower_case)
                return

        for k in key_words:
            if k in lower_case:
                chan_name, status = self.channel_name(msg.channel.name)
                if status!=0:
                    print(chan_name)
                    self.pushover(msg.content, msg.author.display_name, msg.channel.name)
                else:
                    self.pushover(msg.content, msg.author.display_name, chan_name)
                break


        return


if __name__ == "__main__":
    bot = Bot()
    bot.run()
