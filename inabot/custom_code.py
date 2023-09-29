import helper
import data
import boto3
import time


async def cmd_manager(channel_read, channel_write, author, args):
    if len(args) < 3:
        return await channel_write.send(
            f"@{author.display_name} [ERROR] Too few arguments."
        )
    match args[1].lower():
        case "add":
            return await helper.cmd_add(channel_write, author, args)
        case "edit":
            return await helper.cmd_edit(channel_write, author, args)
        case "del":
            return await helper.cmd_del(channel_write, author, args)
        case "show":
            return await helper.cmd_show(channel_write, author, args)
        case "options":
            return await helper.cmd_options(channel_write, author, args)
        case _:
            return await channel_write.send(
                f'@{author.display_name} [ERROR] "{args[1]}" is not a valid option.'
            )


async def edit_counter(channel_read, channel_write, author, args):
    if len(args) < 3:
        return await channel_write.send(
            f"@{author.display_name} [ERROR] Too few arguments."
        )
    if not helper.check_int(args[2]):
        return await channel_write.send(
            f'@{author.display_name} [ERROR] "{args[2]}" is not an integer.'
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
        f'@{author.display_name} Counter "{args[1]}" set to {args[2]}.'
    )

async def fierce(channel_read, channel_write, author, args):
    return await helper.quotes(channel_write, author, args)


async def asdf(channel_read, channel_write, author, args):
    return await channel_write.send("message")