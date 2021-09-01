from twitchio.ext import commands
import math
import random
import os
from dotenv import load_dotenv
import pos


class Bot(commands.Bot):

    def __init__(self):
        load_dotenv()
        super().__init__(token=os.getenv('TWITCH_OAUTH_TOKEN'), prefix='!', initial_channels=[os.getenv('CHANNEL')])
        self.probability = float(os.getenv('PROBABILITY'))
        # self.keyword = {'JJ': 'valid',
        #                 'JJR': 'more valid',
        #                 'JJS': 'most valid',
        #                 'VB': 'shoot',
        #                 'VBD': 'shot',
        #                 'VBG': 'shooting',
        #                 'VBN': 'shot',
        #                 'VBP': 'shoot',
        #                 'VBZ': 'shoots'
        #                 }
        self.keyword = {'JJ': 'valid',
                        'JJR': 'more valid',
                        'JJS': 'most valid',
                        'VB': 'yeet',
                        'VBD': 'yeeted',
                        'VBG': 'yeeting',
                        'VBN': 'yeeted',
                        'VBP': 'yeet',
                        'VBZ': 'yeets'
                        }
        self.bot = os.getenv('BOT')
        self.exclude = ['@', '\'', '\'m', 'is', 'was', 'are', 'were', 'am', 'been', '\'s', 'does', 'do', 'i']

    async def event_ready(self):
        print('bot is ready')

    async def event_message(self, msg):
        if msg.author.name.lower() == self.bot:
            return
        if random.random() < (1.0-self.probability):
            return
        args = msg.content.split(' ')
        if (len(args) > 15):
            return
        pairs = pos.tag(msg.content)
        text = []
        change = False
        for sentence in pairs:
            for word in sentence:
                tag = False
                for key, value in self.keyword.items():
                    if word[1] == key:
                        if word[0].lower() not in self.exclude:
                            change = True
                            tag = True
                            if word[0] == word[0].upper():
                                text.append(value.upper())
                            else:
                                text.append(value)
                if not tag:
                    text.append(word[0])
        output = pos.assemble(text)
        if change:
            await msg.channel.send(output)
        return


if __name__ == "__main__":
    bot = Bot()
    bot.run()
