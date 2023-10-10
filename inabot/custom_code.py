import helper
import data
import boto3
import access
import API
import json


async def cmd_manager(channel_read, channel_write, context, args):
    if len(args) < 3:
        return await channel_write.send(
            f"@{context.author.display_name} [ERROR] Too few arguments."
        )
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
            return await channel_write.send(
                f'@{context.author.display_name} [ERROR] "{args[1]}" is not a valid option.'
            )


async def web_cmd_manager(display_name, args):
    if args[0] == "!cmd" and len(args) < 3:
        return f"@{display_name} [ERROR] Too few arguments."
    if display_name == "inabox44":
        web_author = data.WebAuthor(display_name=display_name, is_broadcaster=True)
        web_context = data.WebContext(author=web_author)
    else:
        web_author = data.WebAuthor(display_name=display_name)
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
            return await channel_write.send(
                f"@{context.author.display_name} [ERROR] Too few arguments."
            )
    counter = args[1]
    if not helper.check_int(args[2]):
        if web:
            return (
                f'@{context.author.display_name} [ERROR] "{args[2]}" is not an integer.'
            )
        else:
            return await channel_write.send(
                f'@{context.author.display_name} [ERROR] "{args[2]}" is not an integer.'
            )
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
        return await channel_write.send(
            f'@{context.author.display_name} Counter "{counter}" set to {args[2]}.'
        )


async def delete_counter(channel_read, channel_write, context, args, web=False):
    if len(args) < 2:
        if web:
            return f"@{context.author.display_name} [ERROR] Too few arguments."
        else:
            return await channel_write.send(
                f"@{context.author.display_name} [ERROR] Too few arguments."
            )
    if args[1] not in data.COUNTERS_LIST:
        if web:
            return f'@{context.author.display_name} [ERROR] Counter "{args[1]}" does not exist.'
        else:
            return await channel_write.send(
                f'@{context.author.display_name} [ERROR] Counter "{args[1]}" does not exist.'
            )
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
        return await channel_write.send(
            f'@{context.author.display_name} Counter "{args[1]}" deleted successfully.'
        )


async def fierce(channel_read, channel_write, context, args):
    return await helper.quotes(channel_write, context.author, args)


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
        return "Usage: !so [user]"

    user = args[1]
    if user[0] == "@":
        user = user[1:]

    user = API.broadcaster_ID(user)
    if not user:
        return
    id = user["id"]
    display_name = user["display_name"]

    game_name = API.get_game(id)

    response = f"inaboxHype Check out {display_name}! When they aren't in The Box™, they're streaming {game_name} over at https://twitch.tv/{display_name.lower()}"

    API.shoutout(id)
    return API.announcement(response)
