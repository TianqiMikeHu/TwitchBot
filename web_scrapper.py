from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
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
import time

class Web_Scrapper():
    def __init__(self):
        # Setting options for a headless Chrome browser
        chrome_options = Options()
        prefs = {'profile.default_content_setting_values': {'cookies': 2, 'images': 2,
                            'plugins': 2, 'popups': 2, 'geolocation': 2, 
                            'notifications': 2, 'auto_select_certificate': 2, 'fullscreen': 2, 
                            'mouselock': 2, 'mixed_script': 2, 'media_stream': 2, 
                            'media_stream_mic': 2, 'media_stream_camera': 2, 'protocol_handlers': 2, 
                            'ppapi_broker': 2, 'automatic_downloads': 2, 'midi_sysex': 2, 
                            'push_messaging': 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop': 2, 
                            'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement': 2, 
                            'durable_storage': 2}}
        chrome_options.add_experimental_option('prefs', prefs)
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("start-maximized")
        chrome_options.add_argument("disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        # chrome_options.page_load_strategy = 'none'
        # Suppress JS warnings
        chrome_options.add_argument("--log-level=3")
        # Hide the fact that we are using a headless browser
        userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36"
        chrome_options.add_argument(f'user-agent={userAgent}')
        self.chrome_options = chrome_options
        self.driver = webdriver.Chrome(options=self.chrome_options)    

        self.se_dict = {}
        self.se_defaults = []

        if os.path.isfile('SE_Cache/streamelements.txt'):
            # Load default SE commands
            with open('SE_Cache/streamelements.txt', "r", encoding='utf-8') as f:
                self.se_defaults = f.read().splitlines()
        else:
            # If default file not present, re-request everything
            self.se_clear()


    ## Used to programmatically delete all SE cache, or delete a specified one
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

            self.se_dict.pop(name, None)
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


    ## Launches Selenium browser to retrieve a commands page
    # Should be ran within se_timeout_manager so that it can be killed if it takes too long
    def se_get_command(self, streamer_name):
        if self.driver is None:
            self.driver = webdriver.Chrome(options=self.chrome_options)

        self.driver.get(f"https://streamelements.com/{streamer_name}/commands")

        try:
            # Wait until the rows of the table load (class: md-cell)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'md-cell')))
        except:
            # Time out after 10 seconds
            print("Web driver timed out")
            self.driver.close()
            self.driver = None
            return

        # Use BeautifulSoup to gather the cells into list
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        # self.driver.close()
        # self.driver = None
        cells = [x.getText().rstrip() for x in soup.find_all("td", {"class", "md-cell"})] 

        index = 0
        tempBuffer = []
        while index<len(cells):
            # filter through SE default commands
            if cells[index] not in self.se_defaults:
                tempBuffer.append([cells[index], cells[index+1]])
            # We only need 2 out of every 3 rows from the result of BeautifulSoup
            index+=3

        # Write as csv
        with open(f'SE_Cache/{streamer_name}.txt', 'w', newline='', encoding='utf-8') as csvfile:
            mywriter = csv.writer(csvfile, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            mywriter.writerows(tempBuffer)


    ### WARNING: subprocess was causing too much performance hit that I decided it's not worth it
    ## Exactly what it looks like. Runs se_get_command and kills it if needed
    def se_timeout_manager(self, streamer_name):
        p = multiprocessing.Process(target=self.se_get_command, args=(streamer_name,))
        p.start()
        p.join(30)      # 30 second timeout
        if p.is_alive():
            print("Sub-process timed out")
            p.terminate()
            p.join()


    ## Main handler to retrieve a SE command
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
        starttime = time.time()
        if not os.path.isfile(f'SE_Cache/{streamer_name}.txt'):
            # Web request if not on disk
            self.se_get_command(streamer_name)
        print(time.time()-starttime)

        # If still not on disk, declare failure
        if not os.path.isfile(f'SE_Cache/{streamer_name}.txt'):
            return "[ERROR]: failed to load to memory. Likely a timed out."


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


    ## Analyze and parse SE syntax
    def se_parse(self, text, author, args, streamer_name, header):
        index = 0
        index2 = 0
        while 1:
            # Find code that need to be evaluated, starting from the "innermost" one
            index2 = text.find(BRACKET_R)
            index = text.rfind(BRACKET_L, 0, index2-1)

            if index!=-1 and index2!=-1:    # Found
                eval1 = text[index+len(BRACKET_L):index2]
                se_code = shlex.split(eval1)    # preserving quotes

                # pick from the following choices
                if se_code[0]=='random.pick':   
                    eval1 = random.choice(se_code[1:])

                # the user/target's name
                elif se_code[0]=='user' or se_code[0]=='sender':    
                    if len(se_code)>1:
                        eval1 = se_code[1]
                    else:
                        eval1 = author
                # slicing notation detected

                elif re.match("([0-9]+:?[0-9]*)|([0-9]*:?[0-9]+)", se_code[0]):     
                    try:
                        eval1 = eval(f'args[{se_code[0]}]')
                    except IndexError:  # Index out of range, say nothing
                        print("Index out of range")
                        return None
                    if isinstance(eval1, list):
                        eval1 = ' '.join(eval1)

                # Use random chatter API call
                elif se_code[0]=='random.chatter':
                    eval1 = random.choice(API.ls_chatters(streamer_name, header))

                # Kama Kama Kama Kama
                elif se_code[0]=='repeat':
                    num = int(se_code[1])
                    eval1 = ' '.join([se_code[2]]*num)
                else:
                    # random range of number
                    groups = re.match("random.([0-9]+)-([0-9]+)", se_code[0])
                    if groups:
                        groups = groups.groups()
                        try:
                            eval1 = random.randrange(int(groups[0]), int(groups[1])+1)
                            eval1 = str(eval1)
                        except ValueError:
                            return None
                    else:
                        # else do not resolve, we don't know what this is
                        eval1 = '['+eval1+']'


                text = text[0:index]+eval1+text[index2+len(BRACKET_R):]
            else:
                break
        return text


# For testing purposes
if __name__ == '__main__':
    # files = glob.glob('./SE_Cache/*')
    # for f in files:
    #     os.remove(f)
    ws = Web_Scrapper()
    res = ws.se_handler('breakingpointes', '!prank3', 'Mike', ['!prank3', 'prank', 'Han'], header=None)
    print(res)