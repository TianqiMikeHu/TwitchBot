from twitchio.ext import commands
import random
import re
import pos
import quizstruct

from admin import *
from quiz_functions import *
from other import *
from API import *

is_POSTAG = None
appearance_list = []


class Bot(commands.Bot):

    def __init__(self):
        dotenv.load_dotenv()
        super().__init__(token=os.getenv('TWITCH_OAUTH_TOKEN'), prefix='!', initial_channels=[os.getenv('CHANNEL')])
        self.probability = float(os.getenv('PROBABILITY'))
        # The following is an example of word replacement
        # self.keyword = {'JJ': 'valid',
        #                 'JJR': 'more valid',
        #                 'JJS': 'most valid',
        #                 'VB': 'yeet',
        #                 'VBD': 'yeeted',
        #                 'VBG': 'yeeting',
        #                 'VBN': 'yeeted',
        #                 'VBP': 'yeet',
        #                 'VBZ': 'yeets'
        #                 }
        self.bot = os.getenv('BOT')
        ### MYSQL
        dbconfig = {
            "host":"localhost",
            "port":"3306",
            "user":"root",
            "password": os.getenv('DBPASS'),
            "database":"quizdb",
        }
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="pool1",
            pool_size=5,
            pool_reset_session=True,
            **dbconfig)
        self.author = ''
        self.args = []
        self.channel = None
        self.quiz = quizstruct.Quiz()
        self.scrapper = web_scrapper.Web_Scrapper()


    async def event_ready(self):
        print("bot is ready")


    # I never use this honestly
    async def word_swap(self, msg):
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
        
        if msg.author.name.lower() == self.bot:     # ignore self
            return

        if is_POSTAG:
            await self.word_swap(msg)
        

        args = msg.content.split()
        self.args = args
        self.channel = msg.channel
        command = self.args[0].lower()
        self.author = msg.author.name
        user = self.author.lower()
        trimmed = " ".join(self.args)
        lowered = trimmed.lower()


        # Is it a user seen before?
        if user not in appearance_list:
            myquery = 'SELECT * FROM bot.viewers WHERE username = %s'
            result = query(self.pool, myquery, False, (user,))
            if len(result)==0:      # new user
                # Check bot filter
                ban = filter(lowered)
                if ban:
                    await self.channel.send("/ban {0}".format(user))
                    await self.channel.send("BOP BOP BOP")
                    return
                # Okay not a follower bot
                myquery = 'INSERT INTO bot.viewers(username, messages, points, greeting, shoutout) VALUES(%s, 0, 0, \'NONE\', \'\')'
                query(self.pool, myquery, True, (user,))
                appearance_list.append(user)
            else:
                # Greet user
                greeting = result[0][3]
                if greeting != 'NONE':
                    await self.channel.send(greeting)
                appearance_list.append(user)
        # Increment message count
        myquery = 'UPDATE bot.viewers SET messages = messages+1 WHERE username = %s'
        query(self.pool, myquery, True, (user,))



        # Special Cases
        if 'nooo' in lowered or 'D:' in lowered:
            await self.channel.send("D:")
            return
        if 'good bot' in lowered:
            await self.channel.send(":D")
            return

        # Manual SQL Operation
        if command=='!sql':
            if user in ADMIN:
                try:
                    myquery = msg.content[5:]   # slicing off "!sql "

                    commit = True
                    if 'select' in myquery.lower() and 'call' not in myquery.lower():     # Set commit to false if it is a read
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
        if not re.match('^[a-zA-Z0-9\t\n\s,.~/<>?;:\"\'`!@#$%^&*()\[\]\{\}_+=|\\-]+$', msg.content):
            return

        # Some extra precautions
        for word in DENY:
            if word in lowered:
                return


        # Now retrieve commands
        myquery = 'SELECT response, access FROM bot.commands WHERE command_name = %s'
        try:
            result = query(self.pool, myquery, False, (command,))
            if len(result)>0:
                response = result[0][0]
                access = result[0][1]
                if access=='M' and user not in MODS:
                    await self.channel.send("This action is restricted to mods only.")
                    return 
                
                # EVAL special case
                index = 0
                index2 = 0
                while 1:
                    index = response.find(EVAL)
                    if index!=-1:
                        index2 = response.find(EVAL, index+1)
                        eval1 = self.redirect(response[index+len(EVAL):index2])
                        if eval1 is None:   # We have nothing to say
                            return
                        response = response[0:index]+eval1+response[index2+len(EVAL):]
                    else:
                        break

                # SUBQUERY special case
                index = 0
                index2 = 0
                while 1:
                    index = response.find(SUBQUERY, index2)
                    if index!=-1:
                        query_args = [x.lower() for x in self.args[1:]]
                        if len(query_args)==0:  # In case the user meant to target themselves
                            query_args.append(self.author)
                        index2 = response.find(SUBQUERY, index+1)
                        myquery = response[index+len(SUBQUERY):index2]
                        num_args = myquery.count('%s')
                        if num_args>0:
                            query_args = tuple(query_args[:num_args])
                        else:
                            query_args = None

                        commit = True
                        if 'select' in myquery.lower() and 'call' not in myquery.lower():     # Set commit to false if it is a read
                            commit = False
                        result = query(self.pool, myquery, commit, query_args)
                        if not commit and len(result)>0:
                            result = result[0][0]       # First thing in the result
                        else:
                            result = ''
                        response = response[0:index]+str(result)+response[index2+len(SUBQUERY):]
                        index2+=1
                    else:
                        break
                
                while 1:
                    index = response.find(SEPARATE)
                    if index!=-1:
                        await self.channel.send(response[:index])
                        response = response[index+len(SEPARATE):]
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
