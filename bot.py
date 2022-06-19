from twitchio.ext import commands
import math
import random
import os
from dotenv import load_dotenv
import re
import pos
import mysql.connector.pooling
import requests
import quizstruct
import difflib

# Delimiters:
EVAL = '@#'
SUBQUERY = '$%'
SEPARATE = '*SEP*'

EXCLUDE = ['@', '\'', '\'m', 'is', 'was', 'are', 'were', 'am', 'been', '\'s', 'does', 'do', 'i']
FILTER = ['famous', 'follower', 'prime', 'viewer', 'buy']

ME = "mike_hu_0_0"
BREAKING = "breakingpointes"
ADMIN = [ME, BREAKING]
MODS = [ME, "a_poorly_written_bot", BREAKING, "thelastofchuck", "ebhb1210"]
# Access Control: E - Everyone
#                 M - Mods

dbconfig = {
    "host":"localhost",
    "port":"3306",
    "user":"root",
    "password":"password",
    "database":"quizdb",
}



is_POSTAG = None
appearance_list = []




class Bot(commands.Bot):

    def __init__(self):
        load_dotenv()
        super().__init__(token=os.getenv('TWITCH_OAUTH_TOKEN'), prefix='!', initial_channels=[os.getenv('CHANNEL')])
        self.probability = float(os.getenv('PROBABILITY'))
        # The following is an example of word replacement
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
        ### MYSQL
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="pool1",
            pool_size=5,
            pool_reset_session=True,
            **dbconfig)
        self.author = ''
        self.args = []
        self.channel = None
        self.quiz = quizstruct.Quiz()
        self.header = {"Client-ID": os.getenv('CLIENTID'), 
                "Authorization":"Bearer {0}".format(os.getenv('ACCESSTOKEN')), 
                "Content-Type":"application/json"}


    async def event_ready(self):
        print("bot is ready")


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
    
    ##################################################################### Utility functions
    # Determine if a user wants to implicitly target themselves
    def my_name(self):
        if len(self.args)>1:
            if self.args[1][0]=='@':
                self.args[1] = self.args[1][1:]
            return self.args[1]
        else:
            return self.author


    def query(self, myquery, commit=False, args=None):
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        result = None
        try:
            cursor.execute(myquery, args)
            if commit:
                conn.commit()
            else:
                result = cursor.fetchall()
        except mysql.connector.Error as e:
            print(e)
        finally:
            cursor.close()
            conn.close()
            return result


    def filter(self, msg):
        count = 0
        for word in FILTER:
            if word in msg:
                count+=1
        if count>1:
            return True     # ban
        else:
            return False

    #########################################################
    # Quiz Bowl Game functions
    def quiz_reset(self):
        if self.author==self.quiz.get_player or self.author.lower()==ME:
            self.quiz.reset()
            return "Current bonus question ended."
        else:
            return "You are not the current player."

    def quiz_start(self):
        if self.quiz.get_state()!=0:
            return "A quiz is currently running. Please try !end"
        if len(self.args)<3:
            return "Incorrect number of arguments."

        self.quiz.reset()
        # Parse arguments
        category = self.args[1].lower()
        catNum = 0
        difficulty = 0
        try:
            difficulty = int(self.args[2])
        except ValueError:
            return "Difficulty must be an integer"
        if difficulty<1 or difficulty>9:
            return "Invalid difficulty"

        # Categories
        if category=='random':
            myquery = 'select leadin, text, answer from bonus_parts join (select bonus.id, leadin from (bonus join (select * from tournaments where difficulty = %s) as b on bonus.tournament_id=b.id) order by rand() limit 1) as a on bonus_parts.bonus_id=a.id'
            result = self.query(myquery, False, (difficulty,))
            if len(result)<3:
                return "Sorry, something went wrong. Try again."
            self.quiz.set_parts([result[0][0], result[0][1], result[1][1], result[2][1]])
            self.quiz.set_answers([result[0][2], result[1][2], result[2][2]])
            self.quiz.grader(None)
            self.quiz.set_player(self.author.lower())
            return self.quiz.get_parts(0) + SEPARATE + self.quiz.get_parts(1)
        
        catNum = 0
        if category=='mythology':
            catNum = 14
        elif category=='literature':
            catNum = 15
        elif category=='trash':
            catNum = 16
        elif category=='science':
            catNum = 17
        elif category=='history':
            catNum = 18
        elif category=='religion':
            catNum = 19
        elif category=='geography':
            catNum = 20
        elif category=='fine_arts':
            catNum = 21
        elif category=='social_science':
            catNum = 22
        elif category=='philosophy':
            catNum = 25
        elif category=='current_events':
            catNum = 26
        elif category=='math':
            myquery = 'select leadin, text, answer from bonus_parts join (select bonus.id, leadin from bonus where subcategory_id = 26 order by rand() limit 1) as a on bonus_parts.bonus_id=a.id'
            result = self.query(myquery, False, None)
            if len(result)<3:
                return "Sorry, something went wrong. Try again."
            self.quiz.set_parts([result[0][0], result[0][1], result[1][1], result[2][1]])
            self.quiz.set_answers([result[0][2], result[1][2], result[2][2]])
            self.quiz.grader(None)
            self.quiz.set_player(self.author.lower())
            return self.quiz.get_parts(0) + SEPARATE + self.quiz.get_parts(1)
        elif category=='cs':
            myquery = 'select leadin, text, answer from bonus_parts join (select bonus.id, leadin from bonus where subcategory_id = 23 order by rand() limit 1) as a on bonus_parts.bonus_id=a.id'
            result = self.query(myquery, False, None)
            if len(result)<3:
                return "Sorry, something went wrong. Try again."
            self.quiz.set_parts([result[0][0], result[0][1], result[1][1], result[2][1]])
            self.quiz.set_answers([result[0][2], result[1][2], result[2][2]])
            self.quiz.grader(None)
            self.quiz.set_player(self.author.lower())
            return self.quiz.get_parts(0) + SEPARATE + self.quiz.get_parts(1)
        else:
            return "Invalid category."
        
        # Launch query
        myquery = 'select leadin, text, answer from bonus_parts join (select bonus.id, leadin from (bonus join (select * from tournaments where difficulty = %s) as b on bonus.tournament_id=b.id) where category_id = %s order by rand() limit 1) as a on bonus_parts.bonus_id=a.id'
        result = self.query(myquery, False, (difficulty, catNum))
        if len(result)<3:
            return "Sorry, something went wrong. Try again."
        self.quiz.set_parts([result[0][0], result[0][1], result[1][1], result[2][1]])
        self.quiz.set_answers([result[0][2], result[1][2], result[2][2]])
        self.quiz.grader(None)
        self.quiz.set_player(self.author.lower())
        return self.quiz.get_parts(0) + SEPARATE + self.quiz.get_parts(1)


    def answer(self):
        if self.author.lower()!=self.quiz.player:
            return "You are not the current player, "+self.author
        message = " ".join(self.args[1:])
        reply, update = self.quiz.grader(message)
        if update is not None:
            if update:
                myquery = 'UPDATE bot.viewers SET points = points+%s WHERE username = %s'
                self.query(myquery, True, (self.quiz.get_score(), self.quiz.player))
        return reply

    def yes(self):
        if self.author.lower()!=self.quiz.player:
            return None
        reply, update = self.quiz.yes()
        if update is not None:
            if update:
                myquery = 'UPDATE bot.viewers SET points = points+%s WHERE username = %s'
                self.query(myquery, True, (self.quiz.get_score(), self.quiz.player))
        return reply

    def no(self):
        if self.author.lower()!=self.quiz.player:
            return None
        reply, update = self.quiz.no()
        if update is not None:
            if update:
                myquery = 'UPDATE bot.viewers SET points = points+%s WHERE username = %s'
                self.query(myquery, True, (self.quiz.get_score(), self.quiz.player))
        return reply



    ################################################    Other functions
    def updatedeath(self):
        if len(self.args)<2:
            return "Usage: !updatedeath [link]"
        myquery = 'call bot.updatedeath(%s)'
        self.query(myquery, True, (self.args[1],))
        return "Done"

    def updatepb(self):
        if len(self.args)<2:
            return "Usage: !updatepb [link]"
        myquery = 'call bot.updatepb(%s)'
        self.query(myquery, True, (self.args[1],))
        return "Done"

    def createcmd(self):
        if len(self.args)<3:
            return "Usage: !createcmd [name] [response]"
        myquery = 'select * from bot.commands where command_name=%s'
        result = self.query(myquery, False, (self.args[1],))
        if len(result)>0:
            return "This command already exists."
        myquery = 'call bot.createcmd(%s, %s)'
        self.query(myquery, True, (self.args[1], ' '.join(self.args[2:])))
        return "Done"

    def editcmd(self):
        if len(self.args)<3:
            return "Usage: !editcmd [name] [response]"
        myquery = 'select * from bot.commands where command_name=%s'
        result = self.query(myquery, False, (self.args[1],))
        if len(result)==0:
            return "This command does not exist."
        myquery = 'call bot.editcmd(%s, %s)'
        self.query(myquery, True, (self.args[1], ' '.join(self.args[2:])))
        return "Done"

    def deletecmd(self):
        if len(self.args)<3:
            return "Usage: !deletecmd [name] [response]"
        myquery = 'select * from bot.commands where command_name=%s'
        result = self.query(myquery, False, (self.args[1],))
        if len(result)==0:
            return "This command does not exist."
        myquery = 'call bot.deletecmd(%s)'
        self.query(myquery, True, (self.args[1],))
        return "Done"

    def editaccess(self):
        if len(self.args)<3:
            return "Usage: !editaccess [name] [access]"
        if self.args[2] not in ['E', 'M']:
            return "Not a valid access level"
        myquery = 'select * from bot.commands where command_name=%s'
        result = self.query(myquery, False, (self.args[1],))
        if len(result)==0:
            return "This command does not exist."
        myquery = 'call bot.editaccess(%s, %s)'
        self.query(myquery, True, (self.args[1], self.args[2]))
        return "Done"

    def getclip(self):
        if len(self.args)<3:
            return "Usage: !getclip [user] [key words]"

        # Get user ID from name
        r = requests.get(url="https://api.twitch.tv/helix/users?login={0}".format(self.args[1]), headers=self.header)
        if r.status_code!=200:
            print(r.status_code)
            return "Status code is not 200"
        data = r.json()
        if len(data.get('data'))==0:
            return "User not found"
        id = data.get('data')[0].get('id')


        key = ' '.join(self.args[2:])
        keyL = key.lower().split()
        limit = 20      # We're only gonna search 20*50 = 1000 clips

        # Get top clips
        r = requests.get(url="https://api.twitch.tv/helix/clips?broadcaster_id={0}&first=50".format(id), headers=self.header)
        while 1:
            if r.status_code!=200:
                print(r.status_code)
                return "Status code is not 200"
            data = r.json()
            pagination = data.get('pagination').get('cursor')
            if pagination is None or pagination=='':
                return "No result (end of pages)"

            # Put into a dictionary
            clips = {}
            for item in data.get('data'):
                title = item.get('title')
                link = item.get('url')
                if title is None or link is None:
                    continue
                clips[title] = link


            # Check if the key words are all present
            for title in list(clips.keys()):
                titleL = title.lower()
                passed = True
                for k in keyL:
                    if k not in titleL:
                        passed = False
                        break
                if passed:
                    return "Best match: {0}".format(clips.get(title))

            
            # Use difflib if still inconclusive
            result = difflib.get_close_matches(key, list(clips.keys()))

            if len(result)!=0:
                 return "Best match: {0}".format(clips.get(result[0]))

            limit-=1
            if limit==0:
                return "No result (limit reached)"

            # Continue from pagination index
            r = requests.get(url="https://api.twitch.tv/helix/clips?broadcaster_id={0}&first=50&after={1}".format(id, pagination), headers=self.header)
        


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
            result = self.query(myquery, False, (user,))
            if len(result)==0:      # new user
                # Check bot filter
                ban = self.filter(lowered)
                if ban:
                    await self.channel.send("\/ban {0}".format(user))
                    await self.channel.send("BOP BOP BOP")
                    return
                # Okay not a follower bot
                myquery = 'INSERT INTO bot.viewers(username, messages, points, greeting, shoutout) VALUES(%s, 0, 0, \'NONE\', \'\')'
                self.query(myquery, True, (user,))
                appearance_list.append(user)
            else:
                # Greet user
                greeting = result[0][3]
                if greeting != 'NONE':
                    await self.channel.send(greeting)
                appearance_list.append(user)
        # Increment message count
        myquery = 'UPDATE bot.viewers SET messages = messages+1 WHERE username = %s'
        self.query(myquery, True, (user,))



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
                    result = self.query(myquery, commit)
                    if commit:
                        await self.channel.send("Done")
                    else:
                        for row in result:
                            await self.channel.send(str(row))
                except mysql.connector.Error as e:
                    await self.channel.send("An error occured")
            else:
                await self.channel.send("You are not authorized to do this.")
            return



        # regex check so that it doesn't crash later
        if re.match('^[a-zA-Z0-9\t\n\s,.~/<>?;:\"\'`!@#$%^&*()\[\]\{\}_+=|\\-]+$', msg.content):
            pass
        else:
            return


        # Now retrieve commands
        myquery = 'SELECT response, access FROM bot.commands WHERE command_name = %s'
        try:
            result = self.query(myquery, False, (command,))
            if len(result)>0:
                response = result[0][0]
                access = result[0][1]
                if access=='M' and user not in MODS:
                    return "This action is restricted to mods only."
                
                # EVAL special case
                index = 0
                index2 = 0
                while 1:
                    index = response.find(EVAL, index2)
                    if index!=-1:
                        index2 = response.find(EVAL, index+1)
                        eval1 = eval(response[index+len(EVAL):index2])
                        if eval1 is None:   # We have nothing to say
                            return
                        response = response[0:index]+eval1+response[index2+len(EVAL):]
                        index2+=1
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
                        result = self.query(myquery, commit, query_args)
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
            await self.channelx.send("An error occured")
        return


if __name__ == "__main__":    
    print("Do you wish to enable POS tagging function? [y/n]")
    answer = input()
    if answer.lower() is not "y":
        is_POSTAG = False
    else:
        is_POSTAG = True
    bot = Bot()
    bot.run()
