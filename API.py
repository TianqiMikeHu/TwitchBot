from tools import *
import requests
import difflib


# return values: message, status code
def broadcaster_ID(name, header):
    r = requests.get(url="https://api.twitch.tv/helix/users?login={0}".format(name), headers=header)
    if r.status_code!=200:
        print(r.status_code)
        return "Error: status code is not 200", 2
    data = r.json()
    if len(data.get('data'))==0:
        return "Error: User not found", 1
    id = data.get('data')[0].get('id')
    return id, 0


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
            return "Error: status code is not 200"
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
        return "Error: status code is not 200"
    data = r.json()
    if len(data.get('data'))==0:
        return "Error: User not found"
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
        return "Error: status code is not 200"
    data = r.json()
    if len(data.get('data'))==0:
        return "Error: User not found"
    title_name = data.get('data')[0].get('title')
    
    return title_name