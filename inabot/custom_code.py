import helper
import data
import boto3
import access
import API
import json
from datetime import datetime
from dateutil import relativedelta
from dateutil import parser
import pytz
import requests


async def cmd_manager(channel_read, channel_write, context, args):
    if len(args) < 3:
        return await context.reply(f"[ERROR] Too few arguments.")
    match args[1].lower():
        case "add":
            return await helper.cmd_add(channel_write, context, args)
        case "edit":
            return await helper.cmd_edit(channel_write, context, args)
        case "del":
            return await helper.cmd_del(channel_write, context, args)
        case "show":
            return await helper.cmd_show(channel_write, context, args)
        case "options":
            return await helper.cmd_options(channel_write, context, args)
        case _:
            return await context.reply(f'[ERROR] "{args[1]}" is not a valid option.')


async def web_cmd_manager(display_name, args):
    if args[0] == "!cmd" and len(args) < 3:
        return f"@{display_name} [ERROR] Too few arguments."
    if display_name == "inabox44":
        web_author = data.WebAuthor(
            display_name=display_name, name=display_name.lower(), is_broadcaster=True
        )
        web_context = data.WebContext(author=web_author)
    else:
        web_author = data.WebAuthor(
            display_name=display_name, name=display_name.lower()
        )
        web_context = data.WebContext(author=web_author)

    if args[0] == "!editcounter":
        return await edit_counter(None, None, web_context, args, web=True)
    elif args[0] == "!deletecounter":
        return await delete_counter(None, None, web_context, args, web=True)
    match args[1].lower():
        case "add":
            return await helper.cmd_add(None, web_context, args, web=True)
        case "edit":
            return await helper.cmd_edit(None, web_context, args, web=True)
        case "del":
            return await helper.cmd_del(None, web_context, args, web=True)
        case "show":
            return await helper.cmd_show(None, web_context, args, web=True)
        case "options":
            return await helper.cmd_options(None, web_context, args, web=True)
        case _:
            return f"@{display_name} [ERROR] Invalid Operation"


async def edit_counter(channel_read, channel_write, context, args, web=False):
    if len(args) < 3:
        if web:
            return f"@{context.author.display_name} [ERROR] Too few arguments."
        else:
            return await context.reply(f"[ERROR] Too few arguments.")
    counter = args[1]
    if not helper.check_int(args[2]):
        if web:
            return (
                f'@{context.author.display_name} [ERROR] "{args[2]}" is not an integer.'
            )
        else:
            return await context.reply(f'[ERROR] "{args[2]}" is not an integer.')
    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.update_item(
        Key={
            "var_name": {
                "S": counter,
            },
            "var_type": {"S": "COUNTER"},
        },
        TableName=data.VARIABLES_TABLE,
        UpdateExpression="SET var_val=:v",
        ExpressionAttributeValues={
            ":v": {
                "N": args[2],
            }
        },
        ReturnValues="ALL_NEW",
    )

    # Update counters list
    if counter not in data.COUNTERS_LIST:
        data.COUNTERS_LIST.append(counter)
        response2 = client.update_item(
            Key={
                "var_name": {
                    "S": "_counters_json",
                },
                "var_type": {"S": "CUSTOM"},
            },
            TableName=data.VARIABLES_TABLE,
            UpdateExpression="SET var_val=:v",
            ExpressionAttributeValues={
                ":v": {
                    "S": json.dumps(data.COUNTERS_LIST, separators=(",", ":")),
                }
            },
        )

    if web:
        return f'@{context.author.display_name} Counter "{counter}" set to {args[2]}.'
    else:
        return await context.reply(f'Counter "{counter}" set to {args[2]}.')


async def delete_counter(channel_read, channel_write, context, args, web=False):
    if len(args) < 2:
        if web:
            return f"@{context.author.display_name} [ERROR] Too few arguments."
        else:
            return await context.reply(f"[ERROR] Too few arguments.")
    if args[1] not in data.COUNTERS_LIST:
        if web:
            return f'@{context.author.display_name} [ERROR] Counter "{args[1]}" does not exist.'
        else:
            return await context.reply(f'[ERROR] Counter "{args[1]}" does not exist.')
    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.delete_item(
        Key={
            "var_name": {
                "S": args[1],
            },
            "var_type": {"S": "COUNTER"},
        },
        TableName=data.VARIABLES_TABLE,
    )

    data.COUNTERS_LIST.remove(args[1])
    response = client.update_item(
        Key={
            "var_name": {
                "S": "_counters_json",
            },
            "var_type": {"S": "CUSTOM"},
        },
        TableName=data.VARIABLES_TABLE,
        UpdateExpression="SET var_val = :r",
        ExpressionAttributeValues={
            ":r": {
                "S": json.dumps(data.COUNTERS_LIST, separators=(",", ":")),
            }
        },
    )
    if web:
        return (
            f'@{context.author.display_name} Counter "{args[1]}" deleted successfully.'
        )
    else:
        return await context.reply(f'Counter "{args[1]}" deleted successfully.')


async def fierce(channel_read, channel_write, context, args):
    return await helper.quotes(channel_write, context, args)


async def kimexplains(channel_read, channel_write, context, args):
    return await helper.quotes(channel_write, context, args)


async def permit(channel_read, channel_write, context, args):
    if len(args) < 2:
        return await channel_write.send(
            f"@{context.author.display_name} [ERROR] Too few arguments."
        )
    user = args[1]
    if user[0] == "@":
        user = user[1:]
    await channel_write.send(f"@{user} You can post one link in the next 60 seconds.")
    # Dummy value for cooldown control
    data.COMMANDS["_permit_timeout"] = {
        "command_cooldown_global": {"N": 1},
        "command_cooldown_user": {"N": 60},
    }
    # Reset cooldown in case we are in the middle of suppressed state
    if data.COOLDOWN.get("_permit_timeout"):
        if data.COOLDOWN["_permit_timeout"].get(user.lower()):
            del data.COOLDOWN["_permit_timeout"][user.lower()]
    # Suppress timeout
    access.cooldown_approved("_permit_timeout", user.lower())
    data.PERMIT.append(user.lower())
    return


async def so(channel_read, channel_write, context, args):
    if len(args) < 2:
        return await channel_write.send(
            f"@{context.author.display_name} [ERROR] Too few arguments."
        )

    user = args[1]
    if user[0] == "@":
        user = user[1:]

    user = API.broadcaster_ID(user)
    if not user:
        return await channel_write.send(
            f"@{context.author.display_name} [ERROR] User {user} not found."
        )
    id = user["id"]
    display_name = user["display_name"]

    game_name = API.get_game(id)

    response = f"inaboxHype Check out {display_name}! When they aren't in The Box™, they're streaming {game_name} over at https://twitch.tv/{display_name.lower()}"

    API.shoutout(id)
    return API.announcement(response)


async def title(channel_read, channel_write, context, args):
    if len(args) < 2:
        return await context.reply("[ERROR] Too few arguments.")
    status = API.update_channel_info(title=" ".join(args[1:]))
    if status == 204:
        return await context.reply("Title updated successfully.")
    else:
        return await context.reply(f"[ERROR] Status code: {str(status)}")


async def game(channel_read, channel_write, context, args):
    if len(args) < 2:
        return await context.reply("[ERROR] Too few arguments.")
    game_name = " ".join(args[1:])
    game_id = API.get_game_id(game_name)
    if not game_id:
        return await context.reply(f'[ERROR] Game "{game_name}" not found.')
    status = API.update_channel_info(game_id=game_id)
    if status == 204:
        return await context.reply("Category updated successfully.")
    else:
        return await context.reply(f"[ERROR] Status code: {str(status)}")


async def followers(channel_read, channel_write, context, args):
    return await channel_write.send(
        f"Kim has {str(API.follower_count())} followers inaboxHype"
    )


async def follow_age(channel_read, channel_write, context, args):
    target = context.author.display_name
    if len(args) > 1 and access.authorization("M", context.author):
        target = args[1]
        if target[0] == "@":
            target = target[1:]
        user = API.broadcaster_ID(target)
        if not user:
            return await context.reply(f"[ERROR] User {target} not found.")
        date = API.follow_date(user["id"])
        target = user["display_name"]
    else:
        date = API.follow_date(context.author.id)
    if not date:
        return await context.reply(f"{target} is not following Kim.")
    date = parser.isoparse(date)
    delta = relativedelta.relativedelta(
        datetime.utcnow().replace(tzinfo=pytz.utc), date
    )
    response = f"{target} followed Kim on {date.strftime('%b %d %Y at %H:%M:%S UTC')}, for a total of "
    if delta.years:
        response += f"{delta.years} year{'s' if delta.years>1 else ''} "
    if delta.months:
        response += f"{delta.months} month{'s' if delta.months>1 else ''} "
    response += f"{delta.days} day{'s' if delta.days>1 else ''} "
    response += f"and {delta.hours} hour{'s' if delta.hours>1 else ''} "

    return await context.reply(response)


async def inabot_queue(channel_read, channel_write, context, args):
    if len(args) > 1:
        match args[1].lower():
            case "join":
                queue = helper.get_queue()
                if context.author.display_name in queue:
                    return await channel_write.send(
                        f"@{context.author.display_name} is already in the queue."
                    )
                queue.append(context.author.display_name)
                helper.save_queue(queue)
                return await channel_write.send(
                    f"@{context.author.display_name} has joined the queue."
                )
            case "leave":
                queue = helper.get_queue()
                if not queue:
                    return await channel_write.send("Current queue: EMPTY")
                if context.author.display_name not in queue:
                    return await channel_write.send(
                        f"@{context.author.display_name} is not currently in the queue."
                    )
                queue.remove(context.author.display_name)
                helper.save_queue(queue)
                return await channel_write.send(
                    f"@{context.author.display_name} has left the queue."
                )
            case "clear":
                if not access.authorization("M", context.author):
                    return await context.reply(
                        f"[ERROR] You do not have permission for this action."
                    )
                helper.save_queue([])
                return await channel_write.send(
                    f"@{context.author.display_name} has cleared the queue."
                )
            case "remove":
                if not access.authorization("M", context.author):
                    return await context.reply(
                        f"[ERROR] You do not have permission for this action."
                    )
                queue = helper.get_queue()
                if not queue:
                    return await channel_write.send("Current queue: EMPTY")
                if len(args) > 2:
                    if args[2] not in queue:
                        return await channel_write.send(
                            f"@{context.author.display_name} User {args[2]} is not currently in the queue."
                        )
                    queue.remove(args[2])
                    helper.save_queue(queue)
                    return await channel_write.send(
                        f"@{context.author.display_name} User {args[2]} has been removed from the queue."
                    )
                else:
                    removed = queue.pop(0)
                    helper.save_queue(queue)
                    return await channel_write.send(
                        f"@{context.author.display_name} User {removed} has been removed from the queue."
                    )
            case "add":
                if not access.authorization("M", context.author):
                    return await context.reply(
                        f"[ERROR] You do not have permission for this action."
                    )
                queue = helper.get_queue()
                if len(args) > 2:
                    if args[2] in queue:
                        return await channel_write.send(
                            f"@{context.author.display_name} User {args[2]} is already in the queue."
                        )
                    queue.append(args[2])
                    helper.save_queue(queue)
                    return await channel_write.send(
                        f"@{context.author.display_name} User {args[2]} has been added to the queue."
                    )
                else:
                    return await context.reply(f"[ERROR] Too few arguments.")
            case _:
                pass
    queue = helper.get_queue()
    output = "Current queue: "
    if not queue:
        return await channel_write.send("Current queue: EMPTY")
    else:
        for person in queue:
            output += f"{person}, "
        output = output[:-2]
        return await channel_write.send(f"{output}")


async def joinqueue(channel_read, channel_write, context, args):
    return await inabot_queue(channel_read, channel_write, context, ["!queue", "join"])


async def modban(channel_read, channel_write, context, args):
    mods = helper.get_mods()
    mod = None
    if args[1].lower() in list(mods.keys()):
        mod = mods[args[1].lower()]
    if mod is None:
        for alias in list(mods.values()):
            if args[1].lower() == alias.lower():
                mod = alias
                break
    if mod is None:
        return await channel_write.send(f"{args[1]} is not a mod.")
    counter = helper.count(f"{mod}Ban".replace(" ", ""))
    return await channel_write.send(
        f"The people have wanted to ban {mod} {counter} times, but have been unable to because {mod} is a mod inaboxPout"
    )


async def timezone(channel_read, channel_write, context, args):
    timezone = pytz.timezone("Canada/Mountain")
    now = datetime.now(timezone)
    return await channel_write.send(
        f"The current time for inabox44 is {now.strftime('%H:%M:%S')} (Canada/Mountain time zone, {now.strftime('%z')})"
    )


async def youtube(channel_read, channel_write, context, args):
    r = requests.get(
        url="https://decapi.me/youtube/latest_video?id=UCDiSZI6qL_kYW_NkQmyE0zQ"
    )
    return await channel_write.send(
        f"Kim has a YouTube channel! Check out her latest video here: {r.text}"
    )


async def taint(channel_read, channel_write, context, args):
    await helper.word_appearance(channel_write, "taint", context.author.display_name, "the forbidden T word")


async def last_taint(channel_read, channel_write, context, args):
    await helper.last_word_appearance(channel_write, "taint", "the forbidden T word")

async def im_jeevan(channel_read, channel_write, context, args):
    if context.author.name == "gurjeevan_":
        return await context.reply("Hi Jeevan, I'm inabot inaboxArrive")
    else:
        return await context.reply("You are not Jeevan inaboxSus")
