import data
import time
import re


def authorization(level, author):
    match level:
        case "E":
            pass
        case "V":
            if (
                not author.is_vip
                and not author.is_mod
                and author.name not in data.SUPERMODS
                and not author.is_broadcaster
            ):
                return False
        case "M":
            if (
                not author.is_mod
                and author.name not in data.SUPERMODS
                and not author.is_broadcaster
            ):
                return False
        case "S":
            if author.name not in data.SUPERMODS and not author.is_broadcaster:
                return False
        case "B":
            if not author.is_broadcaster:
                return False
        case _:
            return
    return True


def cooldown_approved(cmd, author_name):
    global_cooldown_approved = True
    user_cooldown_approved = True
    now = int(time.time())
    cmd_data = data.COMMANDS[cmd]

    if not data.COOLDOWN.get(cmd):  # Command never invoked before, OK
        data.COOLDOWN[cmd] = {}
        data.COOLDOWN[cmd][author_name] = now
    else:
        # Check Global Cooldown
        difference = now - data.COOLDOWN[cmd][list(data.COOLDOWN[cmd])[-1]]
        if difference < int(cmd_data["command_cooldown_global"]["N"]):
            global_cooldown_approved = False
            print(
                f"{author_name} denied due to global cooldown: {difference} seconds elapsed"
            )
        # Iterate through User Cooldown and delete expired entries
        for user in list(data.COOLDOWN[cmd]):
            if now - data.COOLDOWN[cmd][user] >= int(
                cmd_data["command_cooldown_user"]["N"]
            ):
                del data.COOLDOWN[cmd][user]
            else:
                break
        # Check User Cooldown
        if data.COOLDOWN[cmd].get(author_name):
            user_cooldown_approved = False
            print(
                f"{author_name} denied due to user cooldown: {now-data.COOLDOWN[cmd][author_name]} seconds elapsed"
            )

    if not global_cooldown_approved or not user_cooldown_approved:
        return False
    else:
        data.COOLDOWN[cmd][author_name] = now
        return True


# True means block
def url_match(author, msg):
    if authorization("M", author):
        return False
    if re.match(r"([^\s]+\.(?:co|org|net))", msg):
        return True
    matches = re.findall(
        r"\b((?:https?:\/\/(?:[a-zA-Z\d\-]+\.)+[a-zA-Z]{2,6})|(?:(?:[a-zA-Z\d\-]+\.)+[a-zA-Z]{2,6}[\/|?]))",
        msg,
    )
    # matches = re.findall(r"\b((?:[a-zA-Z\d@\-]+\.)+[a-zA-Z]{2,6})\b", msg)
    if matches:
        # if not authorization("V", author):
        #     return True
        for m in matches:
            if "twitch.tv" not in m:
                return True
        return False
    else:
        return False
