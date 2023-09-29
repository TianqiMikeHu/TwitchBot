from twitchio.ext import commands
import dotenv
import os
import requests
import boto3


DEVICE = 'mike-iphone'

channels = ["mike_hu_0_0", "thelastofchuck", "inabox44", "breakingpointes", "buritters", "annaagtapp", "mikkigemu", "shadowdaze"]
key_words = ["mike"]
exclude_key_words = ["mike and ike", "mike n ike", "mikehu4", "johnmike"]
key_names = []
chan_cache = {}

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


    def get_header_user(self, user_id):
        client = boto3.client("dynamodb", region_name="us-west-2")
        response = client.get_item(
            Key={
                "CookieHash": {
                    "S": user_id,
                }
            },
            TableName="CF-Cookies",
        )
        user_access_token = response["Item"]["AccessToken"]["S"]            

        header = {
            "Client-ID": os.getenv("CLIENTID"),
            "Authorization": f"Bearer {user_access_token}",
            "Content-Type": "application/json",
        }
        return header


    def channel_name(self, name):
        r = requests.get(url="https://api.twitch.tv/helix/users?login={0}".format(name), headers=self.get_header_user("681131749"))
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
            if chan_cache.get(msg.channel.name):
                chan_name = chan_cache[msg.channel.name]
                self.pushover(msg.content, msg.author.display_name, chan_name)
            else:
                chan_name, status = self.channel_name(msg.channel.name)
                if status!=0:
                    print(chan_name)
                    self.pushover(msg.content, msg.author.display_name, msg.channel.name)
                else:
                    chan_cache[msg.channel.name] = chan_name
                    self.pushover(msg.content, msg.author.display_name, chan_name)
                
            return

        for e in exclude_key_words:
            if e in lower_case:
                return

        for k in key_words:
            if k in lower_case:
                if chan_cache.get(msg.channel.name):
                    chan_name = chan_cache[msg.channel.name]
                    self.pushover(msg.content, msg.author.display_name, chan_name)
                else:
                    chan_name, status = self.channel_name(msg.channel.name)
                    if status!=0:
                        print(chan_name)
                        self.pushover(msg.content, msg.author.display_name, msg.channel.name)
                    else:
                        chan_cache[msg.channel.name] = chan_name
                        self.pushover(msg.content, msg.author.display_name, chan_name)
                break


        return


if __name__ == "__main__":
    bot = Bot()
    bot.run()
