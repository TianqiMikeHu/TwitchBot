from twitchio.ext import commands
from twitchio.ext import routines
import data
import helper
from command_handler import *
import dotenv
import access
import threading


class Bot(commands.Bot):
    def __init__(self, channel_read, channel_write):
        dotenv.load_dotenv()
        #### This is for debugging
        if channel_read == channel_write:
            initial_channels = [channel_read]
        else:
            initial_channels = [channel_read, channel_write]
        self.channel_read = channel_read
        self.channel_write = channel_write

        super().__init__(
            token=f"oauth:{helper.get_bot_token()}",
            prefix="!",
            initial_channels=initial_channels,
        )

        helper.initialize_commands()
        # self.SQS.start(stop_on_error=False)
        initialize_schedule(self.schedule)
        self.invalidate.start(stop_on_error=False)

    async def event_ready(self):
        print("inabot is ready")

    @routines.routine(minutes=60, iterations=None)
    async def invalidate(self):
        helper.invalidate()

    @routines.routine(seconds=1, iterations=None)
    async def SQS(self):
        try:
            msg = data.SQS_QUEUE.get_nowait()
            helper.ingest_message(msg)
        except:
            pass

    @routines.routine(seconds=10, iterations=None)
    async def schedule(self):
        await schedule_handler(
            self.get_channel(self.channel_read), self.get_channel(self.channel_write)
        )

    async def event_message(self, msg):
        # https://twitchio.dev/en/latest/reference.html#twitchio.Message
        # https://twitchio.dev/en/latest/reference.html#twitchio.Chatter

        if msg.echo or msg.channel.name != self.channel_read:
            return
        
        # if not access.authorization("V", msg.author):
        #     if access.url_match(msg.content):
        #         return  # TODO
        # access.url_match(msg.content)

        args = msg.content.split()
        await parse_command(
            self.get_channel(self.channel_read),
            self.get_channel(self.channel_write),
            msg.author,
            args,
        )


# threading.Thread(target=helper.read_from_SQS, daemon=True).start()
bot = Bot(channel_read="mike_hu_0_0", channel_write="mike_hu_0_0")
bot.run()
