from tools import *
import requests
import difflib
import urllib.parse
import html2text
import nltk.data

tokenizer = nltk.data.load('./english.pickle')


## return values: message, status code
def broadcaster_ID(name, header):
    r = requests.get(url="https://api.twitch.tv/helix/users?login={0}".format(name), headers=header)
    if r.status_code!=200:
        print(r.status_code)
        return "[ERROR]: status code is not 200", 2
    data = r.json()
    if len(data.get('data'))==0:
        return "[ERROR]: User not found", 1
    id = data.get('data')[0].get('id')
    return id, 0


## Retrieves a clip given the username and key words, best effort match
def getclip(attributes):
    if len(attributes['args'])<3:
        return "Usage: !getclip [user] [key words]"

    # Get user ID from name
    id, status = broadcaster_ID(attributes['args'][1], attributes['header'])
    if status:      # It's an error message
        return id


    key = ' '.join(attributes['args'][2:])
    keyL = key.lower().split()
    limit = 20      # We're only gonna search 20*50 = 1000 clips

    # Get top clips
    r = requests.get(url="https://api.twitch.tv/helix/clips?broadcaster_id={0}&first=50".format(id), headers=attributes['header'])
    while 1:
        if r.status_code!=200:
            print(r.status_code)
            return "[ERROR]: status code is not 200"
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
        result = difflib.get_close_matches(key, list(clips.keys()), cutoff=0.7)

        if len(result)!=0:
            return "Best match: {0}".format(clips.get(result[0]))

        limit-=1
        if limit==0:
            return "No result (limit reached)"

        # Continue from pagination index
        r = requests.get(url="https://api.twitch.tv/helix/clips?broadcaster_id={0}&first=50&after={1}".format(id, pagination), headers=attributes['header'])


## Shoutout the user
def so(attributes):
    if len(attributes['args'])<2:
        return "Usage: !so [user]"

    # Get user ID from name
    id, status = broadcaster_ID(attributes['args'][1], attributes['header'])
    if status:      # It's an error message
        return id

    # Get game name
    r = requests.get(url="https://api.twitch.tv/helix/channels?broadcaster_id={0}".format(id), headers=attributes['header'])
    if r.status_code!=200:
        print(r.status_code)
        return "[ERROR]: status code is not 200"
    data = r.json()
    if len(data.get('data'))==0:
        return "[ERROR]: User not found"
    broadcaster_name = data.get('data')[0].get('broadcaster_name')
    game_name = data.get('data')[0].get('game_name')
    if len(game_name)<1:
        game_name = '[no game]'

    response = "Check out {0} at https://www.twitch.tv/{1} ! They were playing {2}. ".format(broadcaster_name, attributes['args'][1].lower(), game_name)
    
    # Get shoutout message if there is any
    myquery = "select shoutout from bot.viewers where username=%s"
    result = query(attributes['pool'], myquery, False, (attributes['args'][1].lower(),))
    if len(result)==0:
        result = ''
    else:
        result = result[0][0]

    response+=result

    return response


## Get stream title of any channel
def title(attributes):
    if len(attributes['args'])<2:
        user = ME
    else:
        user = attributes['args'][1]

    # Get user ID from name
    id, status = broadcaster_ID(user, attributes['header'])
    if status:      # It's an error message
        return id

    # Get title
    r = requests.get(url="https://api.twitch.tv/helix/channels?broadcaster_id={0}".format(id), headers=attributes['header'])
    if r.status_code!=200:
        print(r.status_code)
        return "[ERROR]: status code is not 200"
    data = r.json()
    if len(data.get('data'))==0:
        return "[ERROR]: User not found"
    title_name = data.get('data')[0].get('title')
    
    return title_name


## List all chatters in a channel
def ls_chatters(broadcaster, header):
    r = requests.get(url=f'https://tmi.twitch.tv/group/user/{broadcaster}/chatters', headers=header)
    if r.status_code!=200:
        print(r.status_code)
        return "[ERROR]: status code is not 200"
    data = r.json().get('chatters')
    # Aggregate all types of chatters
    broadcaster = data['broadcaster']
    vips = data['vips']
    moderators = data['moderators']
    staff = data['staff']
    admins = data['admins']
    global_mods = data['global_mods']
    viewers = data['viewers']
    # return combined list
    return broadcaster+vips+moderators+staff+admins+global_mods+viewers


## Search something from Wikipedia
def wiki(attributes):
    if len(attributes['args'])<2:
        return "Usage: !wiki [query]"
    arg = ' '.join(attributes['args'][1:])  # the query
    safe_string = urllib.parse.quote_plus(arg)  # url encode
    # I don't fully understand the following query parameters, but it does a very good closest match
    r = requests.get(url=f'https://en.wikipedia.org/w/api.php?action=query&generator=search&format=json&gsrsearch={safe_string}&gsrlimit=1&prop=extracts|categories')
    html = r.json().get('query')

    if html is None:
        return "[ERROR]: The page does not exist."
    else:
        html = html.get('pages')
        key = next(iter(html))  # needed because we don't actually know the page id (the key to index)
        category = html.get(key).get('categories')      # Check category to see if it's a disambiguation page
        if 'disambiguation' in category[0]['title']:    # We will not resolve disambiguation if wikipedia cannot
            return "[ERROR]: Reached disambiguation page."
        else:
            page = html.get(key).get('extract')
            text = html2text.html2text(page)    # covnert html to text
            subsection = text.find('##')        # Limit result and discard subsections
            if subsection!=-1:
                text = text[:subsection]
            global tokenizer
            sentences = (tokenizer.tokenize(text))      # because we want to return complete sentences
            response = ''
            count = 0
            length = 0
            for i in range(len(sentences)):               
                if length+len(sentences[i])>300:    # Each message from the bot is capped at 300 chars, and 2 messages max
                    count+=1
                    length = 0
                    if count==2:
                        break
                    response+=SEPARATE
                length+=len(sentences[i])
                response+=sentences[i]
                response+=' '
            return response


## Fetches random article from Wikipedia
# Similar logic as the above function, see comments there
def wiki_random(attributes):
    r = requests.get(url=f'https://en.wikipedia.org/w/api.php?format=json&action=query&generator=random&grnnamespace=0&prop=extracts')

    html = r.json().get('query')
    html = html.get('pages')
    key = next(iter(html))
    page = html.get(key).get('extract')
    text = html2text.html2text(page)
    subsection = text.find('##')
    if subsection!=-1:
        text = text[:subsection]
    
    global tokenizer
    sentences = (tokenizer.tokenize(text))

    response = ''
    count = 0
    length = 0
    for i in range(len(sentences)):               
        if length+len(sentences[i])>300:
            count+=1
            length = 0
            if count==2:
                break
            response+=SEPARATE
        length+=len(sentences[i])
        response+=sentences[i]
        response+=' '
    return response