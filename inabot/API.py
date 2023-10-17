import data
import requests
import boto3
import random
import os


def get_header_user(user_id):
    if data.ACCESS_TOKENS.get(user_id):
        user_access_token = data.ACCESS_TOKENS.get(user_id)
    else:
        client = boto3.client("dynamodb", region_name="us-west-2")
        response = client.get_item(
            Key={
                "CookieHash": {
                    "S": user_id,
                }
            },
            TableName=data.TOKENS_TABLE,
        )
        user_access_token = response["Item"]["AccessToken"]["S"]
        data.ACCESS_TOKENS[user_id] = user_access_token

    header = {
        "Client-ID": os.getenv("CLIENTID"),
        "Authorization": f"Bearer {user_access_token}",
        "Content-Type": "application/json",
    }
    return header


def get_bot_token():
    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.get_item(
        Key={
            "CookieHash": {
                "S": data.INABOT_ID,
            }
        },
        TableName=data.TOKENS_TABLE,
    )
    user_access_token = response["Item"]["AccessToken"]["S"]
    data.ACCESS_TOKENS[data.INABOT_ID] = user_access_token
    return user_access_token


def get_chatters(broadcaster_id):
    r = requests.get(
        url=f"https://api.twitch.tv/helix/chat/chatters?broadcaster_id={broadcaster_id}&moderator_id={data.INABOT_ID}&first=1000",
        headers=get_header_user(data.INABOT_ID),
    )
    chatters = r.json()["data"]
    return random.choice(chatters)["user_name"]


def get_game(broadcaster_id):
    r = requests.get(
        url=f"https://api.twitch.tv/helix/channels?broadcaster_id={broadcaster_id}",
        headers=get_header_user(data.INABOT_ID),
    )
    if r.status_code != 200:
        return "[ERROR]"
    game_name = r.json()["data"][0]["game_name"]
    if len(game_name) < 1:
        game_name = "[Undefined]"
    return game_name


def get_title(broadcaster_id):
    r = requests.get(
        url=f"https://api.twitch.tv/helix/channels?broadcaster_id={broadcaster_id}",
        headers=get_header_user(data.INABOT_ID),
    )
    if r.status_code != 200:
        return "[ERROR]"
    title = r.json()["data"][0]["title"]
    if len(title) < 1:
        title = "[Undefined]"
    return title


def timeout_username(broadcaster_id, moderator_id, username, duration=None):
    r = requests.get(
        url=f"https://api.twitch.tv/helix/users?login={username}",
        headers=get_header_user(data.INABOT_ID),
    )
    timeout_id(broadcaster_id, moderator_id, r.json()["data"][0]["id"], duration)


def timeout_id(broadcaster_id, moderator_id, user_id, duration=None):
    payload = {"data": {"user_id": user_id}}
    if duration:
        payload["data"]["duration"] = duration
    r = requests.post(
        url=f"https://api.twitch.tv/helix/moderation/bans?broadcaster_id={broadcaster_id}&moderator_id={moderator_id}",
        headers=get_header_user(moderator_id),
        json=payload,
    )


def unban(broadcaster_id, moderator_id, user_id):
    r = requests.delete(
        url=f"https://api.twitch.tv/helix/moderation/bans?broadcaster_id={broadcaster_id}&moderator_id={moderator_id}&user_id={user_id}",
        headers=get_header_user(moderator_id),
    )

def delete_message(broadcaster_id, moderator_id, message_id):
    r = requests.delete(
        url=f"https://api.twitch.tv/helix/moderation/chat?broadcaster_id={broadcaster_id}&moderator_id={moderator_id}&message_id={message_id}",
        headers=get_header_user(moderator_id)
    )


def broadcaster_ID(name):
    r = requests.get(
        url=f"https://api.twitch.tv/helix/users?login={name}",
        headers=get_header_user(data.INABOT_ID),
    )
    if r.status_code != 200:
        print(r.json())
        return None
    output = r.json()
    if len(output["data"]) == 0:
        return None
    return output["data"][0]


def announcement(message):
    colors = ["blue", "green", "orange", "purple", "primary"]
    body = {"message": message, "color": random.choice(colors)}
    r = requests.post(
        url=f"https://api.twitch.tv/helix/chat/announcements?broadcaster_id={data.BROADCASTER_ID}&moderator_id={data.INABOT_ID}",
        headers=get_header_user(data.INABOT_ID),
        json=body,
    )
    if r.status_code != 204:
        print(r.json())
    return None


def shoutout(to_broadcaster_id):
    r = requests.post(
        url=f"https://api.twitch.tv/helix/chat/shoutouts?from_broadcaster_id={data.BROADCASTER_ID}&to_broadcaster_id={to_broadcaster_id}&moderator_id={data.INABOT_ID}",
        headers=get_header_user(data.INABOT_ID),
    )

    if r.status_code != 204 or r.status_code != 429:
        print(r.json())
    return None


def get_streams(user_login):
    r = requests.get(
        url=f"https://api.twitch.tv/helix/streams?user_login={user_login}",
        headers=get_header_user(data.INABOT_ID),
    )
    return r.json()["data"]


def get_game_id(game_name):
    r = requests.get(
        url=f"https://api.twitch.tv/helix/games?name={game_name}",
        headers=get_header_user(data.INABOT_ID),
    )
    if not r.json()["data"]:
        return None
    return r.json()["data"][0]["id"]


def update_channel_info(title=None, game_id=None):
    if not title and not game_id:
        return
    body = {}
    if title:
        body["title"] = title
    if game_id:
        body["game_id"] = game_id
    r = requests.patch(
        url=f"https://api.twitch.tv/helix/channels?broadcaster_id={data.BROADCASTER_ID}",
        headers=get_header_user(data.BROADCASTER_ID),
        json=body,
    )
    return r.status_code

def follower_count():
    r = requests.get(
        url=f"https://api.twitch.tv/helix/channels/followers?broadcaster_id={data.BROADCASTER_ID}&first=1",
        headers=get_header_user(data.INABOT_ID),
    )
    return r.json()["total"]