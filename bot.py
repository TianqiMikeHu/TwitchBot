from twitchio.ext import commands
from twitchio.ext import routines
import random
import re
import pos
import quizstruct
import audio
import threading

from admin import *
from quiz_functions import *
from other import *
from API import *
import tools

is_POSTAG = None
appearance_list = []


class Bot(commands.Bot):
    def __init__(self):
        dotenv.load_dotenv()
        super().__init__(
            token=f"oauth:{get_bot_token()}",
            prefix="!",
            initial_channels=[os.getenv("CHANNEL")],
        )
        self.probability = float(os.getenv("PROBABILITY"))
        # The following is an example of word replacement
        # self.keyword = {'JJ': 'valid',
        #                 'JJR': 'more valid',
        #                 'JJS': 'most valid',
        #                 'VB': 'clomp',
        #                 'VBD': 'clomped',
        #                 'VBG': 'clomping',
        #                 'VBN': 'clomped',
        #                 'VBP': 'clomp',
        #                 'VBZ': 'clomps'
        #                 }
        self.bot = os.getenv("BOT")
        ### MYSQL
        dbconfig = {
            "host": "localhost",
            "port": "3306",
            "user": "root",
            "password": os.getenv("DBPASS"),
            "database": "bot",
        }
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="pool1", pool_size=5, pool_reset_session=True, **dbconfig
        )
        self.author = ""
        self.args = []
        self.channel = None
        self.quiz = quizstruct.Quiz()
        self.scrapper = web_scrapper.Web_Scrapper()
        
        # self.cooldown = {
        #     "1min": 60,
        #     "2min": 120,
        #     "5min": 300
        # }

        # self.current_schedule = {}
        # self.schedule.start(stop_on_error=False)
        self.invalidate.start(stop_on_error=False)

    async def event_ready(self):
        print("bot is ready")

    async def event_token_expired():
        print("Token expired.")
        return f"oauth:{get_bot_token()}"

    @routines.routine(minutes=60, iterations=None)
    async def invalidate(self):
        with tools.access_tokens_lock:
            tools.access_tokens = {}

    @routines.routine(seconds=15, iterations=None)
    async def schedule(self):
        for key, val in self.current_schedule.items():
            if val<=0:
                print(key)
                self.current_schedule[key] = self.cooldown[key]+random.random()*30-15 # +-15 seconds randomness
            else:
                self.current_schedule[key] -= 15

    @schedule.before_routine
    async def initialize_schedule(self):
        for key, val in self.cooldown.items():
            self.current_schedule[key] = random.random()*val
        print(self.current_schedule)

    # I never use this honestly
    async def word_swap(self, msg):
        if random.random() < (1.0 - self.probability):
            return
        args = msg.content.split(" ")
        if len(args) > 15:
            return
        pairs = pos.tag(msg.content)
        text = []
        change = False
        for sentence in pairs:
            for word in sentence:
                tag = False
                for key, value in self.keyword.items():
                    if word[1] == key:
                        if word[0].lower() not in EXCLUDE:
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
            await self.channel.send(output)
        return

    # Redirecting to the corresponding function
    def redirect(self, function_name):
        return eval(function_name)(self.__dict__)

    ###########################################################################3
    # Main function for message processing

    async def event_message(self, msg):
        if msg.author is None:
            return

        if (
            msg.author.name.lower() == self.bot and msg.content[0] != "<"
        ):  # ignore self unless it's <command>
            return

        if is_POSTAG:
            await self.word_swap(msg)

        args = msg.content.split()
        self.args = args
        self.channel = msg.channel
        command = self.args[0].lower()
        self.author = msg.author.display_name
        user = self.author.lower()
        trimmed = " ".join(self.args)
        lowered = trimmed.lower()

        # Is it a user seen before?
        if user not in appearance_list:
            myquery = "SELECT * FROM bot.viewers WHERE username = %s"
            result = query(self.pool, myquery, False, (user,))
            if len(result) == 0:  # new user
                # Check bot filter
                ban = filter(lowered)
                if ban:
                    await self.channel.send("/ban {0}".format(user))
                    await self.channel.send("BOP BOP BOP")
                    return
                # Okay not a follower bot
                myquery = "INSERT INTO bot.viewers(username, messages, points, greeting, shoutout, autoshoutout) VALUES(%s, 0, 0, 'NONE', '', 0)"
                query(self.pool, myquery, True, (user,))
                appearance_list.append(user)
            else:
                # Greet user
                greeting = result[0][3]
                if greeting != "NONE":
                    await self.channel.send(greeting)
                autoshoutout = result[0][5]
                if autoshoutout:
                    args_copy = self.args
                    self.args = ["!so", user]
                    self.redirect("so")
                    self.args = args_copy
                appearance_list.append(user)
        # Increment message count
        myquery = "UPDATE bot.viewers SET messages = messages+1 WHERE username = %s"
        query(self.pool, myquery, True, (user,))

        # Special Cases
        if "nooo" in lowered or "D:" in lowered:
            await self.channel.send("D:")
            return
        if "good bot" in lowered:
            await self.channel.send(":D")
            return

        # Manual SQL Operation
        if command == "!sql":
            if user in ADMIN:
                try:
                    myquery = msg.content[5:]  # slicing off "!sql "

                    commit = True
                    if (
                        "select" in myquery.lower() and "call" not in myquery.lower()
                    ):  # Set commit to false if it is a read
                        commit = False
                    result = query(self.pool, myquery, commit)
                    if commit:
                        await self.channel.send("Done")
                    else:
                        for row in result:
                            await self.channel.send(str(row))
                except mysql.connector.Error as e:
                    await self.channel.send("[ERROR]: MySQL")
            else:
                await self.channel.send("You are not authorized to do this.")
            return

        # regex check so that it doesn't crash later
        if not re.match(
            "^[a-zA-Z0-9\t\n\s,.~/<>?;:\"'`!@#$%^&*()\[\]\{\}_+=|\\-]+$", msg.content
        ):
            return

        # Some extra precautions
        for word in DENY:
            if word in lowered:
                return

        # Now retrieve commands
        myquery = "SELECT response, access FROM bot.commands WHERE command_name = %s"
        try:
            result = query(self.pool, myquery, False, (command,))
            if len(result) > 0:
                response = result[0][0]
                access = result[0][1]
                if access == "M" and user not in MODS:
                    await self.channel.send("This action is restricted to mods only.")
                    return

                # EVAL special case
                index = 0
                index2 = 0
                while 1:
                    index = response.find(EVAL)
                    if index != -1:
                        index2 = response.find(EVAL, index + 1)
                        eval1 = self.redirect(response[index + len(EVAL) : index2])
                        if eval1 is None:  # We have nothing to say
                            return
                        response = (
                            response[0:index] + eval1 + response[index2 + len(EVAL) :]
                        )
                    else:
                        break

                # SUBQUERY special case
                index = 0
                index2 = 0
                while 1:
                    index = response.find(SUBQUERY, index2)
                    if index != -1:
                        query_args = [x.lower() for x in self.args[1:]]
                        if (
                            len(query_args) == 0
                        ):  # In case the user meant to target themselves
                            query_args.append(user)
                        index2 = response.find(SUBQUERY, index + 1)
                        myquery = response[index + len(SUBQUERY) : index2]
                        num_args = myquery.count("%s")
                        if num_args > 0:
                            query_args = tuple(query_args[:num_args])
                        else:
                            query_args = None

                        commit = True
                        if (
                            "select" in myquery.lower()
                            and "call" not in myquery.lower()
                        ):  # Set commit to false if it is a read
                            commit = False
                        result = query(self.pool, myquery, commit, query_args)
                        if not commit and len(result) > 0:
                            result = result[0][0]  # First thing in the result
                        else:
                            result = ""
                        response = (
                            response[0:index]
                            + str(result)
                            + response[index2 + len(SUBQUERY) :]
                        )
                        index2 += 1
                    else:
                        break

                while 1:
                    index = response.find(SEPARATE)
                    if index != -1:
                        await self.channel.send(response[:index])
                        response = response[index + len(SEPARATE) :]
                    else:
                        await self.channel.send(response)
                        return
        except mysql.connector.Error as e:
            await self.channel.send("[ERROR]: MySQL")

        # Try to infer SE alias
        response = se_alias(self.__dict__)
        if response is not None:
            await self.channel.send(response)
        return


if __name__ == "__main__":
    # print("Do you wish to enable POS tagging function? [y/n]")
    # answer = input()
    # if answer.lower() is not "y":
    #     is_POSTAG = False
    # else:
    #     is_POSTAG = True
    is_POSTAG = False
    bot = Bot()
    bot.run()
