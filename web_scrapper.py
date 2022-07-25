from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import glob
import multiprocessing
import csv
import random
import shlex
import re
import API
from constants import *


class Web_Scrapper():
    def __init__(self):
        # Setting options for a headless Chrome browser
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        # Suppress JS warnings
        chrome_options.add_argument("--log-level=3")
        # Hide the fact that we are using a headless browser
        userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36"
        chrome_options.add_argument(f'user-agent={userAgent}')
        self.chrome_options = chrome_options

        self.se_dict = {}
        self.se_defaults = []

        if os.path.isfile('SE_Cache/streamelements.txt'):
            # Load default SE commands
            with open('SE_Cache/streamelements.txt', "r", encoding='utf-8') as f:
                self.se_defaults = f.read().splitlines()
        else:
            # If default file not present, re-request everything
            self.se_clear()


    def se_clear(self, name=None):   
        # Remove local files
        if name is None:
            files = glob.glob('./SE_Cache/*')
            for f in files:
                os.remove(f)
        else:
            files = glob.glob(f'./SE_Cache/{name}.txt')
            for f in files:
                os.remove(f)
            return "Done"

        # Refetch SE default commands
        self.se_timeout_manager('streamelements')

        # Clear commands dictionary in memory
        self.se_dict = {}

        # Load default SE commands
        if os.path.isfile(f'SE_Cache/streamelements.txt'):
            # Load cached commands
            with open(f'SE_Cache/streamelements.txt', newline='', encoding='utf-8') as csvfile:
                myreader = csv.reader(csvfile, delimiter='\t', quotechar='|')
                for row in myreader:
                    self.se_defaults.append(row[0])
            return None
        else:
            return "[ERROR]: failed to clear cache"


    def se_get_command(self, streamer_name):
        driver = webdriver.Chrome(options=self.chrome_options)

        driver.get(f"https://streamelements.com/{streamer_name}/commands")

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'md-cell')))
        except:
            print("Web driver timed out")
            driver.close()
            return

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.close()
        cells = [x.getText().rstrip() for x in soup.find_all("td", {"class", "md-cell"})] 

        index = 0
        tempBuffer = []
        while index<len(cells):
            if cells[index] not in self.se_defaults:
                tempBuffer.append([cells[index], cells[index+1]])
            index+=3

        with open(f'SE_Cache/{streamer_name}.txt', 'w', newline='', encoding='utf-8') as csvfile:
            mywriter = csv.writer(csvfile, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            mywriter.writerows(tempBuffer)


    def se_timeout_manager(self, streamer_name):
        p = multiprocessing.Process(target=self.se_get_command, args=(streamer_name,))
        p.start()
        p.join(30)      # 30 second timeout
        if p.is_alive():
            print("Sub-process timed out")
            p.terminate()
            p.join()


    # Note: args start from the requested command. e.g. For '!se breakingpointes !manifest plant', args is ['!manifest', 'plant']
    def se_handler(self, streamer_name, command_name, author, args, header):
        streamer_name = streamer_name.lower()
        command_name = command_name.lower()
        if streamer_name == 'streamelements':
            return "All StreamElements default commands are excluded."

        # Check dictionary in memory 
        commands = self.se_dict.get(streamer_name)
        if commands is not None:
            val = commands.get(command_name)
            if val is not None:
                return self.se_parse(val, author, args, streamer_name, header)
            else:
                return "[ERROR]: command not found"

        # Check local disk
        if not os.path.isfile(f'SE_Cache/{streamer_name}.txt'):
            # Web request if not on disk
            self.se_timeout_manager(streamer_name)

        # If still not on disk, declare failure
        if not os.path.isfile(f'SE_Cache/{streamer_name}.txt'):
            return "[ERROR]: failed to load to memory. Likely subprocess timed out."


        # Load commands on disk
        self.se_dict[streamer_name] = {}
        with open(f'SE_Cache/{streamer_name}.txt', newline='', encoding='utf-8') as csvfile:
            myreader = csv.reader(csvfile, delimiter='\t', quotechar='|')
            for row in myreader:
                self.se_dict[streamer_name][row[0]] = row[1]
        val = self.se_dict[streamer_name].get(command_name)
        if val is not None:
            return self.se_parse(val, author, args, streamer_name, header)
        else:
            return "[ERROR]: command not found"


    def se_parse(self, text, author, args, streamer_name, header):
        index = 0
        index2 = 0
        while 1:
            index2 = text.find(BRACKET_R)
            index = text.rfind(BRACKET_L, 0, index2-1)

            if index!=-1 and index2!=-1:
                eval1 = text[index+len(BRACKET_L):index2]
                se_code = shlex.split(eval1)
                if se_code[0]=='random.pick':
                    eval1 = random.choice(se_code[1:])
                elif se_code[0]=='user' or se_code[0]=='sender':
                    if len(se_code)>1:
                        eval1 = se_code[1]
                    else:
                        eval1 = author
                elif re.match("([0-9]+:?[0-9]*)|([0-9]*:?[0-9]+)", se_code[0]):
                    try:
                        eval1 = eval(f'args[{se_code[0]}]')
                    except IndexError:  # Index out of range, say nothing
                        print("Index out of range")
                        return None
                    if isinstance(eval1, list):
                        eval1 = ' '.join(eval1)
                elif se_code[0]=='random.chatter':
                    eval1 = random.choice(API.ls_chatters(streamer_name, header))
                elif se_code[0]=='repeat':
                    num = int(se_code[1])
                    eval1 = ' '.join([se_code[2]]*num)
                else:
                    groups = re.match("random.([0-9]+)-([0-9]+)", se_code[0])
                    if groups:
                        groups = groups.groups()
                        try:
                            eval1 = random.randrange(int(groups[0]), int(groups[1])+1)
                            eval1 = str(eval1)
                        except ValueError:
                            return None
                    else:
                        eval1 = '['+eval1+']'


                text = text[0:index]+eval1+text[index2+len(BRACKET_R):]
            else:
                break
        return text


# For testing purposes
# if __name__ == '__main__':
#     # files = glob.glob('./SE_Cache/*')
#     # for f in files:
#     #     os.remove(f)
#     ws = Web_Scrapper()
#     res = ws.se_handler('breakingpointes', '!prank3', 'Mike', ['!prank3', 'prank', 'Han'])
#     print(res)