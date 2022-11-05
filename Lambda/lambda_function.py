import socket
import hmac
import hashlib
import os
import json

HOST = 'irc.chat.twitch.tv'
NICK = 'a_poorly_written_bot'
PORT = 6667
CHAN = '#mike_hu_0_0'


def say(message):
    password = os.getenv('TWITCH_OAUTH_TOKEN')
    # print(password)
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
        s.sendall(f"JOIN {CHAN}\r\n".encode('utf-8'))
        s.sendall(f"PRIVMSG {CHAN} : {message}\r\n".encode('utf-8'))
        s.sendall(f"PART {CHAN}\r\n".encode('utf-8'))
    except:
        raise Exception("Socket Error")
    finally:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
    


def lambda_handler(event, context):
    # print(event)
    body = json.loads(event['body'])
    # print(body)
    if event['headers']['twitch-eventsub-message-type']=='webhook_callback_verification':
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
        say("signature mismatch: "+signature+" / "+my_signature)
        return  {
            'statusCode': 403,
            'body': ''
        }

    event_type = body.get('subscription', {}).get('type')
    # print("Event type: ", event_type)
    if event_type == "channel.follow":
        target = body.get('event', {}).get('user_name')
        if target is not None:
            message = target + ", thank you so much for the follow! Welcome to the stream!"
            say(message)

    elif event_type == "channel.prediction.begin":
        title = body.get('event', {}).get('title')
        outcomes = body.get('event', {}).get('outcomes')
        if title is not None and outcomes is not None:
            message = "Kappa What a dilemma: \"" + title + "\" Make your prediction between *" + outcomes[0].get("title") + "* and *" + outcomes[1].get("title") + "*, chat!"
            #print(message)
            say(message)

    elif event_type == 'channel.subscribe':
        user_name = body.get('event', {}).get('user_name')
        tier = body.get('event', {}).get('tier')
        if user_name is not None and tier is not None:
            try:
                tier = int(tier) // 1000
                message = "Whoa, "+user_name+" just subscribed at tier "+str(tier)+"! Thank you so much!"
            except:
                message = "Whoa, "+user_name+" just subscribed! Thank you so much!"
            say(message)

    elif event_type == 'channel.subscription.message':
        user_name = body.get('event', {}).get('user_name')
        tier = body.get('event', {}).get('tier')
        cumulative_months = body.get('event', {}).get('cumulative_months')
        if user_name is not None and tier is not None:
            try:
                tier = int(tier) // 1000
                if cumulative_months>1:
                    cumulative_months = str(cumulative_months)
                    message = "Whoa, "+user_name+" just resubscribed at tier "+str(tier)+" for "+cumulative_months+" months! Thank you so much!"
            except:
                message = "Whoa, "+user_name+" just resubscribed! Thank you so much!"
            say(message)

    elif event_type == 'channel.cheer':
        is_anonymous = body.get('event', {}).get('is_anonymous')
        if not is_anonymous:
            user_name = body.get('event', {}).get('user_name')
            bits = body.get('event', {}).get('bits')
            if user_name is not None and bits is not None:
                try:
                    bits = str(bits)
                    message = "PogChamp "+user_name+" just cheered for "+bits+" bits! I really appreaciate it :D"
                    say(message)
                except:
                    pass

    elif event_type == 'channel.raid':
        from_broadcaster_user_name = body.get('event', {}).get('from_broadcaster_user_name')
        if from_broadcaster_user_name is not None:
            message = "Welcome, raiders from "+from_broadcaster_user_name+"\'s channel!"
            say(message)

    elif event_type == 'channel.poll.begin':
        title = body.get('event', {}).get('title')
        choices = body.get('event', {}).get('choices')
        if title is not None and choices is not None:
            message = "PopCorn We have a new poll about...*checks notes*...\""+title+"\". The options are:"
            try:
                for i in range(len(choices)):
                    option = choices[i].get("title")
                    message = message + " " + str(i+1) + ") " + option
            except:
                raise Exception("Error assembling message")
            say(message)

    else:
        say("This is an error message")

    return  {
        'statusCode': 200,
        'body': ''
    }


# if __name__ == '__main__':
#     dotenv.load_dotenv()
#     # say("This is another test")
#     home()
