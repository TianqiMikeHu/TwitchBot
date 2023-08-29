import hmac
import hashlib
import os
import json
import API
import socket
from twitchio.ext import commands
import boto3
import time
from websocket import create_connection


HOST = 'irc.chat.twitch.tv'
PORT = 6667
NICK = 'a_poorly_written_bot'

cold_start = True


def send_twitchio(message, chan="mike_hu_0_0"):
    global cold_start
    if not cold_start:
        send_socket(message, chan)
        return
    
    class Bot(commands.Bot):
        def __init__(self):
            channel = chan
            super().__init__(token=os.getenv('TWITCH_OAUTH_TOKEN'), prefix='!', initial_channels=[channel])
            self.channel = channel
    
        async def event_ready(self):
            chan = self.get_channel(self.channel)
            await chan.send(message)
            self.loop.stop()
            return
        
    bot = Bot()
    bot.run()
    cold_start = False
    
    try:
        client = boto3.client('lambda')
        response = client.update_function_configuration(
            FunctionName='EventSub',
            Description=f'Modified{str(time.time_ns())}'
        )
    except:
        pass


def send_socket(message, chan="mike_hu_0_0"):
    password = os.getenv('TWITCH_OAUTH_TOKEN')
    # print(password)
    channel =  chan
    try:
        s = socket.socket()
    except:
        raise Exception("Socket Creation")

    try:
        s.connect((HOST, PORT))
    except:
        s.close()
        raise Exception("Connect")

    try:
        s.sendall(f"PASS {password}\r\n".encode('utf-8'))
        s.sendall(f"NICK {NICK}\r\n".encode('utf-8'))
        s.sendall(f"JOIN #{channel}\r\n".encode('utf-8'))
        s.sendall(f"PRIVMSG #{channel} : {message}\r\n".encode('utf-8'))
        s.sendall(f"PART #{channel}\r\n".encode('utf-8'))
    except:
        raise Exception("Socket Error")
    finally:
        s.shutdown(socket.SHUT_RDWR)
        s.close()


    


def lambda_handler(event, context):
    print(event['headers'])
    if event.get('headers') is None:
        return  {
            'statusCode': 403,
            'body': ''
        }
    body = json.loads(event['body'])
    # print(body)
    if event['headers'].get('twitch-eventsub-message-type') =='webhook_callback_verification':
        challenge = body.get('challenge')
        print(f"Challenge is: {challenge}")
        if challenge is not None:
            # print(challenge)
            return  {
                'statusCode': 200,
                'body': challenge
            }
        else:
            return  {
                'statusCode': 400,
                'body': ''
            }
    
    if event['headers'].get('invoke-eventsub') == os.getenv("INVOKE_EVENTSUB"):
        return API.restricted_control(body)

    ID = event['headers']['twitch-eventsub-message-id']
    timestamp = event['headers']['twitch-eventsub-message-timestamp']
    signature = event['headers']['twitch-eventsub-message-signature']
    # print("JSON: ", data)

    concat = ID + timestamp + event['body']
    # print(concat)
    secret = os.getenv('SECRET')
    my_signature = hmac.new(secret.encode('utf-8'), msg=concat.encode('utf-8'), digestmod=hashlib.sha256).hexdigest().lower()
    my_signature = "sha256=" + my_signature

    if signature!=my_signature:
        send_twitchio(f"signature mismatch: {signature}/{my_signature}")
        return  {
            'statusCode': 403,
            'body': ''
        }

    event_type = body.get('subscription', {}).get('type')
    # print("Event type: ", event_type)
    if event_type == "channel.follow":
        target = body.get('event', {}).get('user_name')
        if target is not None:
            message = f"{target}, thank you so much for the follow! Welcome to the stream!"
            send_twitchio(message)

    elif event_type == "channel.prediction.begin":
        title = body.get('event', {}).get('title')
        outcomes = body.get('event', {}).get('outcomes')
        if title is not None and outcomes is not None:
            outcome_0 = outcomes[0].get("title")
            outcome_1 = outcomes[1].get("title")
            message = f"Prediction: \"{title}\" Waste your points between *{outcome_0}* and *{outcome_1}*, chat!"
            #print(message)
            send_twitchio(message)

    elif event_type == 'channel.subscribe':
        user_name = body.get('event', {}).get('user_name')
        tier = body.get('event', {}).get('tier')
        if user_name is not None and tier is not None:
            try:
                tier = int(tier) // 1000
                message = f"Whoa, {user_name} just subscribed at tier {str(tier)}! Thank you so much!"
            except:
                message = f"Whoa, {user_name} just subscribed! Thank you so much!"
            send_twitchio(message)

    elif event_type == 'channel.subscription.message':
        user_name = body.get('event', {}).get('user_name')
        tier = body.get('event', {}).get('tier')
        cumulative_months = body.get('event', {}).get('cumulative_months')
        if user_name is not None and tier is not None:
            try:
                tier = int(tier) // 1000
                if cumulative_months>1:
                    cumulative_months = str(cumulative_months)
                    message = f"Whoa, {user_name} just resubscribed at tier {str(tier)} for {cumulative_months} months! Thank you so much!"
            except:
                message = f"Whoa, {user_name} just resubscribed! Thank you so much!"
            send_twitchio(message)

    elif event_type == 'channel.cheer':
        is_anonymous = body.get('event', {}).get('is_anonymous')
        if not is_anonymous:
            user_name = body.get('event', {}).get('user_name')
            bits = body.get('event', {}).get('bits')
            if user_name is not None and bits is not None:
                try:
                    bits = str(bits)
                    message = f"PogChamp {user_name} just cheered for {bits} bits! I really appreaciate it :D"
                    send_twitchio(message)
                except:
                    pass

    elif event_type == 'channel.raid':
        from_broadcaster_user_name = body.get('event', {}).get('from_broadcaster_user_name')
        if from_broadcaster_user_name is not None:
            message = f"Welcome, raiders from {from_broadcaster_user_name}\'s channel!"
            send_twitchio(message)

    elif event_type == 'channel.poll.begin':
        title = body.get('event', {}).get('title')
        broadcaster_user_login = body.get('event', {}).get('broadcaster_user_login')
        choices = body.get('event', {}).get('choices')
        if title is not None and choices is not None:
            if broadcaster_user_login=='annaagtapp':
                message = "There is a new poll agtappDisco"
                send_twitchio(message, "AnnaAgtapp")
                
            elif broadcaster_user_login=='mike_hu_0_0':
                message = f"PopCorn We have a new poll about...\"{title}\". The options are:"
                try:
                    for i in range(len(choices)):
                        option = choices[i].get("title")
                        message = message + " " + str(i+1) + ") " + option
                except:
                    raise Exception("Error assembling message")
                send_twitchio(message)


            
    elif event_type == 'channel.channel_points_custom_reward_redemption.add':
        broadcaster_user_login = body.get('event', {}).get("broadcaster_user_login")
        response= API.redeem(body)
        if response!="":
            send_twitchio(response, broadcaster_user_login)
            
    elif event_type == 'stream.online':
        username = body.get('event', {}).get('broadcaster_user_name')
        if username == "AnnaAgtapp":
            API.autoscale(username.lower(), 1)
        elif username == "buritters":
            response = "!funfact"
            send_twitchio(response, username)
            API.autoscale(username.lower(), 1)
            API.pushover("ONLINE EVENT", "Britt is online", True)
        elif username == "Mike_Hu_0_0":
            API.autoscale(username.lower(), 1)
        elif username == "MikkiGemu":
            API.autoscale(username.lower(), 1)

    elif event_type == 'stream.offline':
        offline_msg = "Stream is offline. Autoscaling in..."
        username = body.get('event', {}).get('broadcaster_user_name')
        API.pushover("AUTOSCALING", f"AutoScaling-{username.lower()} capacity set to 0")
        if username == "AnnaAgtapp":
            send_twitchio(offline_msg, username)
        elif username == "buritters":
            send_twitchio(offline_msg, username)
        elif username == "Mike_Hu_0_0":
            send_twitchio(offline_msg, username)
        elif username == "MikkiGemu":
            send_twitchio(offline_msg, username)

    else:
        send_twitchio("This is an error message")

    return  {
        'statusCode': 200,
        'body': ''
    }


# if __name__ == '__main__':
#     dotenv.load_dotenv()
#     # say("This is another test")
#     home()
