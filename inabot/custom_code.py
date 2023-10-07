import helper
import data
import boto3
import access
import API

async def cmd_manager(channel_read, channel_write, context, args):
    if len(args) < 3:
        return await channel_write.send(
            f"@{context.author.display_name} [ERROR] Too few arguments."
        )
    match args[1].lower():
        case "add":
            return await helper.cmd_add(channel_write, context.author, args)
        case "edit":
            return await helper.cmd_edit(channel_write, context.author, args)
        case "del":
            return await helper.cmd_del(channel_write, context.author, args)
        case "show":
            return await helper.cmd_show(channel_write, context.author, args)
        case "options":
            return await helper.cmd_options(channel_write, context.author, args)
        case _:
            return await channel_write.send(
                f'@{context.author.display_name} [ERROR] "{args[1]}" is not a valid option.'
            )


async def edit_counter(channel_read, channel_write, context, args):
    if len(args) < 3:
        return await channel_write.send(
            f"@{context.author.display_name} [ERROR] Too few arguments."
        )
    if not helper.check_int(args[2]):
        return await channel_write.send(
            f'@{context.author.display_name} [ERROR] "{args[2]}" is not an integer.'
        )
    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.update_item(
        Key={
            "var_name": {
                "S": args[1],
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
    return await channel_write.send(
        f'@{context.author.display_name} Counter "{args[1]}" set to {args[2]}.'
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
    id = user['id']
    display_name = user['display_name']

    game_name = API.get_game(id)

    response = f"inaboxHype Check out {display_name}! When they aren't in The Box™, they're streaming {game_name} over at https://twitch.tv/{display_name.lower()}"

    API.shoutout(id)
    return API.announcement(response)
