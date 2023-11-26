from tools import *
import requests
import difflib
import urllib.parse
import html2text
import nltk.data
import random
import numpy

tokenizer = nltk.data.load("nltk:tokenizers/punkt/english.pickle")


def broadcaster_ID(name):
    r = requests.get(
        url=f"https://api.twitch.tv/helix/users?login={name}",
        headers=get_header_user("160025583"),
    )
    if r.status_code != 200:
        return None, f"[ERROR]: status code is {str(r.status_code)}"
    data = r.json()
    if len(data["data"]) == 0:
        return None, "[ERROR]: User not found"
    return data["data"][0], None


def announcement(message):
    colors = ["blue", "green", "orange", "purple", "primary"]
    body = {"message": message, "color": random.choice(colors)}
    r = requests.post(
        url="https://api.twitch.tv/helix/chat/announcements?broadcaster_id=160025583&moderator_id=681131749",
        headers=get_header_user("681131749"),
        json=body,
    )
    if r.status_code != 204:
        return f"[ERROR]: status code is {str(r.status_code)}"
    return None


def shoutout(to_broadcaster_id):
    r = requests.post(
        url=f"https://api.twitch.tv/helix/chat/shoutouts?from_broadcaster_id=160025583&to_broadcaster_id={to_broadcaster_id}&moderator_id=681131749",
        headers=get_header_user("681131749"),
    )

    if r.status_code != 204 and r.status_code != 429:
        return f"[ERROR]: status code is {str(r.status_code)}"

    return None


## returns game name of broadcaster
def get_game(name):
    user, error_message = broadcaster_ID(name)
    if not user:  # It's an error message
        return error_message
    id = user["id"]
    # Get game name
    r = requests.get(
        url=f"https://api.twitch.tv/helix/channels?broadcaster_id={id}",
        headers=get_header_user("160025583"),
    )
    if r.status_code != 200:
        print(r.status_code)
        return "[no game]"
    data = r.json()
    if len(data.get("data")) == 0:
        return "[no game]"
    game_name = data.get("data")[0].get("game_name")
    if len(game_name) < 1:
        game_name = "[no game]"
    return game_name


def get_game_from_id(game_id):
    r = requests.get(
        url=f"https://api.twitch.tv/helix/games?id={game_id}",
        headers=get_header_user("160025583"),
    )
    if r.status_code != 200:
        return f"[ERROR]: status code is {str(r.status_code)}"
    else:
        data = r.json()
        data = data.get("data")
        if data is not None:
            if len(data) > 0:
                return data[0]["name"]
        return "-"


def about(attributes):
    if len(attributes["args"]) < 2:
        return "Usage: !about [user]"

    # Get user ID from name
    user, error_message = broadcaster_ID(attributes["args"][1])
    if not user:  # It's an error message
        return error_message

    return user["description"]


## Retrieves a clip given the username and key words, best effort match
def getclip(attributes):
    if len(attributes["args"]) < 3:
        return "Usage: !getclip [user] [key words]"

    # Get user ID from name
    user, error_message = broadcaster_ID(attributes["args"][1])
    if not user:  # It's an error message
        return error_message
    id = user["id"]

    key = " ".join(attributes["args"][2:])
    keyL = key.lower().split()
    limit = 20  # We're only gonna search 20*50 = 1000 clips

    # Get top clips
    r = requests.get(
        url=f"https://api.twitch.tv/helix/clips?broadcaster_id={id}&first=50",
        headers=get_header_user("160025583"),
    )
    while 1:
        if r.status_code != 200:
            print(r.status_code)
            return "[ERROR]: status code is not 200"
        data = r.json()

        # Put into a dictionary
        clips = {}
        for item in data.get("data"):
            title = item.get("title")
            link = item.get("url")
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

        if len(result) != 0:
            return "Best match: {0}".format(clips.get(result[0]))

        limit -= 1
        if limit == 0:
            return "No result (limit reached)"

        pagination = data.get("pagination").get("cursor")
        if pagination is None or pagination == "":
            return "No result (end of pages)"
        # Continue from pagination index
        r = requests.get(
            url=f"https://api.twitch.tv/helix/clips?broadcaster_id={id}&first=50&after={pagination}",
            headers=get_header_user("160025583"),
        )


def listclip(attributes):
    if len(attributes["args"]) < 2:
        return "Usage: !listclip [user]"

    limit = 10  # We're only gonna search 10*100 = 1000 clips
    games = {}

    override = False
    # 0 means no override
    if len(attributes["args"]) > 2:
        if attributes["args"][2].lower() == "true":
            override = True

    if len(attributes["args"]) > 3:
        if attributes["args"][3].isnumeric():
            limit = int(attributes["args"][3])
            if limit > 5000:
                limit = 5000
            limit //= 100

    # Get user ID from name
    user, error_message = broadcaster_ID(attributes["args"][1])
    if not user:  # It's an error message
        return error_message
    id = user["id"]
    display_name = user["display_name"]
    profile_image_url = user["profile_image_url"]
    offline_image_url = user["offline_image_url"]

    csv = numpy.array(
        [
            [f"{display_name}'s Clips", "", "", "", ""],
            ["Clip", "Game", "Views", "Created At", "Creator Name"],
        ]
    )

    if not override:
        s3 = boto3.resource("s3")
        try:
            s3.Object("a-poorly-written-bot", f"clips/clips-{display_name}.html").load()
        except botocore.exceptions.ClientError as e:
            pass
        else:
            return f"https://apoorlywrittenbot.cc/clips/clips-{display_name}.html"

    # Get top clips
    r = requests.get(
        url=f"https://api.twitch.tv/helix/clips?broadcaster_id={id}&first=100",
        headers=get_header_user("160025583"),
    )
    for i in range(limit):
        if r.status_code != 200:
            return f"[ERROR]: status code is not {str(r.status_code)}"
        data = r.json()

        for item in data.get("data"):
            title = item.get("title")
            link = item.get("url")
            creator_name = item.get("creator_name")
            view_count = item.get("view_count")
            created_at = item.get("created_at")
            game_id = item.get("game_id")

            game_name = games.get(game_id)
            if game_name is None:
                game_name = get_game_from_id(game_id)
                games[game_id] = game_name

            url = f'<a href="{link}" class="link-dark" target="_blank" rel="noopener noreferrer">{title}</a>'

            csv = numpy.append(
                csv, [[url, game_name, view_count, created_at, creator_name]], axis=0
            )

        pagination = data.get("pagination").get("cursor")
        if pagination is None or pagination == "":
            break
        # Continue from pagination index
        r = requests.get(
            url=f"https://api.twitch.tv/helix/clips?broadcaster_id={id}&first=100&after={pagination}",
            headers=get_header_user("160025583"),
        )

    fill_clips(csv, profile_image_url, offline_image_url, display_name)
    return f"https://apoorlywrittenbot.cc/clips/clips-{display_name}.html"


## Shoutout the user
def so(attributes):
    if len(attributes["args"]) < 2:
        return "Usage: !so [user]"

    # Get user ID from name
    user, error_message = broadcaster_ID(my_name(attributes))
    if not user:  # It's an error message
        return error_message
    id = user["id"]

    # Get game name
    r = requests.get(
        url=f"https://api.twitch.tv/helix/channels?broadcaster_id={id}",
        headers=get_header_user("160025583"),
    )
    if r.status_code != 200:
        print(r.status_code)
        return "[ERROR]: status code is not 200"
    data = r.json()
    if len(data.get("data")) == 0:
        return "[ERROR]: User not found"
    broadcaster_name = data.get("data")[0].get("broadcaster_name")
    game_name = data.get("data")[0].get("game_name")
    if len(game_name) < 1:
        game_name = "[no game]"

    response = f"Check out {broadcaster_name} at https://www.twitch.tv/{attributes['args'][1].lower()} ! They were playing {game_name}. "

    # Get shoutout message if there is any
    myquery = "select shoutout from bot.viewers where username=%s"
    result = query(attributes["pool"], myquery, False, (attributes["args"][1].lower(),))
    if len(result) == 0:
        result = ""
    else:
        result = result[0][0]

    response = response + result

    shoutout(id)
    return announcement(response)


## Get stream title of any channel
def title(attributes):
    if len(attributes["args"]) < 2:
        user = ME
    else:
        user = attributes["args"][1]

    # Get user ID from name
    user, error_message = broadcaster_ID(user)
    if not user:  # It's an error message
        return error_message
    id = user["id"]

    # Get title
    r = requests.get(
        url=f"https://api.twitch.tv/helix/channels?broadcaster_id={id}",
        headers=get_header_user("160025583"),
    )
    if r.status_code != 200:
        print(r.status_code)
        return "[ERROR]: status code is not 200"
    data = r.json()
    if len(data.get("data")) == 0:
        return "[ERROR]: User not found"
    title_name = data.get("data")[0].get("title")

    return title_name


## List all chatters in a channel
# def ls_chatters(broadcaster):
#     # Not using the return values, purely for checking the validity of the access token
#     id, status, display_name, img, about = broadcaster_ID(ME)

#     r = requests.get(url=f'https://tmi.twitch.tv/group/user/{broadcaster}/chatters', headers=get_header())
#     if r.status_code!=200:
#         print(r.status_code)
#         return "[ERROR]: status code is not 200"
#     data = r.json().get('chatters')
#     # Aggregate all types of chatters
#     broadcaster = data['broadcaster']
#     vips = data['vips']
#     moderators = data['moderators']
#     staff = data['staff']
#     admins = data['admins']
#     global_mods = data['global_mods']
#     viewers = data['viewers']
#     # return combined list
#     return broadcaster+vips+moderators+staff+admins+global_mods+viewers


## Search something from Wikipedia
def wiki(attributes):
    if len(attributes["args"]) < 2:
        return "Usage: !wiki [query]"
    arg = " ".join(attributes["args"][1:])  # the query
    safe_string = urllib.parse.quote_plus(arg)  # url encode
    # I don't fully understand the following query parameters, but it does a very good closest match
    r = requests.get(
        url=f"https://en.wikipedia.org/w/api.php?action=query&generator=search&format=json&gsrsearch={safe_string}&gsrlimit=1&prop=extracts|categories"
    )
    html = r.json().get("query")

    if html is None:
        return "[ERROR]: The page does not exist."
    else:
        html = html.get("pages")
        key = next(
            iter(html)
        )  # needed because we don't actually know the page id (the key to index)
        category = html.get(key).get(
            "categories"
        )  # Check category to see if it's a disambiguation page
        if (
            "disambiguation" in category[0]["title"]
        ):  # We will not resolve disambiguation if wikipedia cannot
            return "[ERROR]: Reached disambiguation page."
        else:
            page = html.get(key).get("extract")
            text = html2text.html2text(page)  # covnert html to text
            subsection = text.find("##")  # Limit result and discard subsections
            if subsection != -1:
                text = text[:subsection]
            global tokenizer
            sentences = tokenizer.tokenize(
                text
            )  # because we want to return complete sentences
            response = ""
            count = 0
            length = 0
            for i in range(len(sentences)):
                if (
                    length + len(sentences[i]) > 300
                ):  # Each message from the bot is capped at 300 chars, and 2 messages max
                    count += 1
                    length = 0
                    if count == 2:
                        break
                    response += SEPARATE
                length += len(sentences[i])
                response += sentences[i]
                response += " "
            return response


## Fetches random article from Wikipedia
# Similar logic as the above function, see comments there
def wiki_random(attributes):
    r = requests.get(
        url=f"https://en.wikipedia.org/w/api.php?format=json&action=query&generator=random&grnnamespace=0&prop=extracts"
    )

    html = r.json().get("query")
    html = html.get("pages")
    key = next(iter(html))
    page = html.get(key).get("extract")
    text = html2text.html2text(page)
    subsection = text.find("##")
    if subsection != -1:
        text = text[:subsection]

    global tokenizer
    sentences = tokenizer.tokenize(text)

    response = ""
    count = 0
    length = 0
    for i in range(len(sentences)):
        if length + len(sentences[i]) > 300:
            count += 1
            length = 0
            if count == 2:
                break
            response += SEPARATE
        length += len(sentences[i])
        response += sentences[i]
        response += " "
    return response
