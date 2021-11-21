from flask import Flask, request
import socket
import hmac
import hashlib

app = Flask(__name__)

HOST = 'irc.twitch.tv'
NICK = 'a_poorly_written_bot'
PORT = 6667
PASS = ''
CHAN = 'mike_hu_0_0'
SECRET = ''


def say(message):
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
        out = 'PASS ' + PASS + '\r\n'
        out += 'NICK ' + NICK + '\r\n'
        out += 'JOIN #' + CHAN + '\r\n'
        out += 'PRIVMSG #' + CHAN + ' :' + message + '\r\n'
        out += 'PART #' + CHAN + '\r\n'
        s.sendall(bytearray(out, 'utf-8'))
    except:
        s.close()
        raise Exception("Socket Error")

    s.shutdown(socket.SHUT_RDWR)
    s.close()


@app.route('/', methods=['POST'])
def home():
    data = request.json
    if request.headers.get('Twitch-Eventsub-Message-Type')=='webhook_callback_verification':
        challenge = data.get('challenge')
        if challenge is not None:
            # print(challenge)
            return challenge
        else:
            return('', 400)

    ID = request.headers.get('Twitch-Eventsub-Message-Id')
    timestamp = request.headers.get('Twitch-Eventsub-Message-Timestamp')
    signature = request.headers.get('Twitch-Eventsub-Message-Signature')
    # print("JSON: ", data)

    concat = ID + timestamp + request.get_data(True, True, False)
    my_signature = hmac.new(SECRET.encode('utf-8'), msg=concat.encode('utf-8'), digestmod=hashlib.sha256).hexdigest().lower()
    my_signature = "sha256=" + my_signature
    # logging.info("Message-ID: ",ID)
    # logging.info("Message-TIMESTAMP: ",timestamp)
    # logging.info("BODY: ",data)
    # logging.info("hmac: ", signature)
    # logging.info("my-hmac: ", my_signature)
    # print(concat)
    # print(signature)
    # print(my_signature)
    # return('', 200)
    if signature!=my_signature:
        say("signature mismatch: "+signature+" / "+my_signature)
        return('', 403)

    event_type = data.get('subscription', {}).get('type')
    # print("Event type: ", event_type)
    if event_type == "channel.follow":
        target = data.get('event', {}).get('user_name')
        if target is not None:
            if "hoss" in target.lower() or "h0ss" in target.lower():
                message = "/ban " + target
            else:
                message = target + ", thank you so much for the follow! Welcome to the stream!"
            say(message)

    elif event_type == "channel.prediction.begin":
        title = data.get('event', {}).get('title')
        outcomes = data.get('event', {}).get('outcomes')
        if title is not None and outcomes is not None:
            message = "Kappa What a dilemma: \"" + title + "\" Make your prediction between *" + outcomes[0].get("title") + "* and *" + outcomes[1].get("title") + "*, chat!"
            #print(message)
            say(message)

    elif event_type == 'channel.subscribe':
        user_name = data.get('event', {}).get('user_name')
        tier = data.get('event', {}).get('tier')
        if user_name is not None and tier is not None:
            try:
                tier = int(tier) // 1000
                message = "Whoa, "+user_name+" just subscribed at tier "+str(tier)+"! Thank you so much!"
            except:
                message = "Whoa, "+user_name+" just subscribed! Thank you so much!"
            say(message)
            
    elif event_type == 'channel.subscription.message':
        user_name = data.get('event', {}).get('user_name')
        tier = data.get('event', {}).get('tier')
        cumulative_months = data.get('event', {}).get('cumulative_months')
        if user_name is not None and tier is not None:
            try:
                tier = int(tier) // 1000
                cumulative_months = str(cumulative_months)
                message = "Whoa, "+user_name+" just resubscribed at tier "+str(tier)+" for "+cumulative_months+" months! Thank you so much!"
            except:
                message = "Whoa, "+user_name+" just resubscribed! Thank you so much!"
            say(message)

    elif event_type == 'channel.cheer':
        is_anonymous = data.get('event', {}).get('is_anonymous')
        if not is_anonymous:
            user_name = data.get('event', {}).get('user_name')
            bits = data.get('event', {}).get('bits')
            if user_name is not None and bits is not None:
                try:
                    bits = str(bits)
                    message = "PogChamp "+user_name+" just cheered for "+bits+" bits! I really appreaciate it :D"
                    say(message)
                except:
                    pass

    elif event_type == 'channel.raid':
        from_broadcaster_user_name = data.get('event', {}).get('from_broadcaster_user_name')
        if from_broadcaster_user_name is not None:
            message = "Welcome, raiders from "+from_broadcaster_user_name+"\'s channel!"
            say(message)

    elif event_type == 'channel.poll.begin':
        title = data.get('event', {}).get('title')
        choices = data.get('event', {}).get('choices')
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

    return ('', 200)


if __name__ == '__main__':
    # say("This is a test")
    app.run()