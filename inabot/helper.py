import boto3
import data
import importlib
import json
import API
import random
import access
import re


def invalidate():
    data.ACCESS_TOKENS = {}


def read_from_SQS():
    client = boto3.client("sqs", region_name="us-west-2")
    while 1:
        response = client.receive_message(
            QueueUrl=data.SQS_URL,
            WaitTimeSeconds=20,
        )
        if response.get("Messages"):
            for msg in response["Messages"]:
                data.SQS_QUEUE.put(msg["Body"])
                response = client.delete_message(
                    QueueUrl=data.SQS_URL, ReceiptHandle=msg["ReceiptHandle"]
                )


def hot_reload():
    print("reloading...")
    code = importlib.import_module("custom_code")
    importlib.reload(code)


def check_int(s):
    if s[0] == "-":
        return s[1:].isdigit()
    return s.isdigit()


def convert_to_user(arg):
    if arg[0] == "@":
        arg = arg[1:]
    user = API.broadcaster_ID(arg)
    if not user:
        return arg
    else:
        return user["display_name"]


def initialize_commands():
    client = boto3.client("dynamodb", region_name="us-west-2")

    response = client.get_item(
        Key={
            "var_name": {
                "S": "_commands_json",
            },
            "var_type": {"S": "CUSTOM"},
        },
        TableName=data.VARIABLES_TABLE,
    )
    data.CMD_LIST = json.loads(response["Item"]["var_val"]["S"])

    response = client.get_item(
        Key={
            "var_name": {
                "S": "_commands_any",
            },
            "var_type": {"S": "CUSTOM"},
        },
        TableName=data.VARIABLES_TABLE,
    )
    data.ANY_COMMANDS = json.loads(response["Item"]["var_val"]["S"])

    response = client.get_item(
        Key={
            "var_name": {
                "S": "_commands_schedule",
            },
            "var_type": {"S": "CUSTOM"},
        },
        TableName=data.VARIABLES_TABLE,
    )
    data.SCHEDULABLE_COMMANDS = json.loads(response["Item"]["var_val"]["S"])

    response = client.get_item(
        Key={
            "var_name": {
                "S": "_counters_json",
            },
            "var_type": {"S": "CUSTOM"},
        },
        TableName=data.VARIABLES_TABLE,
    )
    data.COUNTERS_LIST = json.loads(response["Item"]["var_val"]["S"])

    response = client.get_item(
        Key={
            "var_name": {
                "S": "_client_id",
            },
            "var_type": {"S": "CUSTOM"},
        },
        TableName=data.VARIABLES_TABLE,
    )
    data.CLIENT_ID = response["Item"]["var_val"]["S"]


def load_command(cmd):
    print(f"Read request: {cmd}")
    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.get_item(
        Key={
            "command_name": {
                "S": cmd,
            }
        },
        TableName=data.COMMANDS_TABLE,
    )
    data.COMMANDS[cmd] = response["Item"]
    return response["Item"]


# ${sender} -> author of the message
# ${args 1} -> args[1]
# ${args 1:3} -> args[1:3], end index not included
# ${args 1:} -> args[1:]
# ${args :5} -> args[:5]
# ${args :} -> args[:]
#
# ${user abc} -> Interpret 'abc' as user. Convert to display_name and remove @ character if needed.
# ${escape abc} -> Escapes double quotes and backslashes
#
# ${random.pick ["item one", "item two", "item three"]} -> Pick random item from list
# ${random.number 1 5} -> Pick random integer from range, inclusive. This can be negative
# ${random.chatter} -> Pick random chatter
#
# ${count abc} -> Increment counter 'abc', return new value
# ${getcount abc} -> Return value of counter 'abc'
# ${uncount abc} -> Decrement counter 'abc', return new value
#
# ${game} -> The current category of inabox44
# ${title} -> The current category of inabox44
def parse_variables(message, context, args):
    inde_left = 0
    index_right = 0
    while 1:
        # Find code that need to be evaluated, starting from the "innermost" one
        index_right = message.find(data.BRACKET_R)
        inde_left = message.rfind(data.BRACKET_L, 0, index_right - 1)

        if inde_left != -1 and index_right != -1:  # Found
            evaluate_this = message[inde_left + len(data.BRACKET_L) : index_right]
            evaluate_this_list = evaluate_this.split()

            match evaluate_this_list[0]:
                case "sender":
                    evaluate_this = context.author.display_name
                case "args":
                    slice_indices = evaluate_this_list[1].split(":")
                    if len(slice_indices) < 2:
                        evaluate_this = args[int(slice_indices[0])]
                    else:
                        if len(slice_indices[0]) and len(slice_indices[1]):
                            evaluate_this = args[
                                int(slice_indices[0]) : int(slice_indices[1])
                            ]
                        elif len(slice_indices[0]):
                            evaluate_this = args[int(slice_indices[0]) :]
                        elif len(slice_indices[1]):
                            evaluate_this = args[: int(slice_indices[1])]
                        else:
                            evaluate_this = args[:]
                    if isinstance(evaluate_this, list):
                        evaluate_this = " ".join(evaluate_this)
                case "user":
                    evaluate_this = convert_to_user(evaluate_this_list[1])
                case "escape":
                    evaluate_this = json.dumps(evaluate_this_list[1])
                    evaluate_this = evaluate_this[1:-1]
                case "random.pick":
                    picks = json.loads(" ".join(evaluate_this_list[1:]))
                    evaluate_this = random.choice(picks)
                case "random.number":
                    evaluate_this = str(
                        random.randrange(
                            int(evaluate_this_list[1]), int(evaluate_this_list[2]) + 1
                        )
                    )
                case "random.chatter":
                    evaluate_this = API.get_chatters(data.BROADCASTER_ID)
                case "count":
                    evaluate_this = count(evaluate_this_list[1])
                case "getcount":
                    evaluate_this = get_count(evaluate_this_list[1])
                case "uncount":
                    evaluate_this = uncount(evaluate_this_list[1])
                case "game":
                    evaluate_this = API.get_game(data.BROADCASTER_ID)
                case "title":
                    evaluate_this = API.get_title(data.BROADCASTER_ID)
                case _:
                    # else we don't know what this is
                    raise ValueError
            message = (
                message[0:inde_left]
                + evaluate_this
                + message[index_right + len(data.BRACKET_R) :]
            )
        else:
            break
    return message


def count(counter):
    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.update_item(
        Key={
            "var_name": {
                "S": counter,
            },
            "var_type": {"S": "COUNTER"},
        },
        TableName=data.VARIABLES_TABLE,
        UpdateExpression="ADD var_val :v",
        ExpressionAttributeValues={
            ":v": {
                "N": "1",
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

    return response["Attributes"]["var_val"]["N"]


def uncount(counter):
    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.update_item(
        Key={
            "var_name": {
                "S": counter,
            },
            "var_type": {"S": "COUNTER"},
        },
        TableName=data.VARIABLES_TABLE,
        UpdateExpression="ADD var_val :v",
        ExpressionAttributeValues={
            ":v": {
                "N": "-1",
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

    return response["Attributes"]["var_val"]["N"]


def get_count(counter):
    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.get_item(
        Key={
            "var_name": {
                "S": counter,
            },
            "var_type": {"S": "COUNTER"},
        },
        TableName=data.VARIABLES_TABLE,
    )
    return response["Item"]["var_val"]["N"]


async def cmd_add(channel_write, context, args, web=False):
    if len(args) < 4:
        if web:
            return f"@{context.author.display_name} [ERROR] Too few arguments."
        else:
            return await channel_write.send(
                f"@{context.author.display_name} [ERROR] Too few arguments."
            )
    client = boto3.client("dynamodb", region_name="us-west-2")
    command = {
        "command_name": {
            "S": args[2].lower(),
        },
        "command_response": {
            "S": " ".join(args[3:]),
        },
        "command_type": {
            "S": "SIMPLE",
        },
        "command_permission": {"S": "E"},
        "command_cooldown_user": {"N": "15"},
        "command_cooldown_global": {"N": "15"},
        "command_cooldown_schedule": {"N": "-1"},
    }
    try:
        response = client.put_item(
            Item=command,
            TableName=data.COMMANDS_TABLE,
            ConditionExpression="attribute_not_exists(command_name)",
        )
    except boto3.resource(
        "dynamodb"
    ).meta.client.exceptions.ConditionalCheckFailedException:
        if web:
            return f'@{context.author.display_name} [ERROR] Command "{args[2].lower()}" already exists.'
        else:
            return await channel_write.send(
                f'@{context.author.display_name} [ERROR] Command "{args[2].lower()}" already exists.'
            )

    data.COMMANDS[args[2].lower()] = command
    data.CMD_LIST.append(args[2].lower())

    response = client.update_item(
        Key={
            "var_name": {
                "S": "_commands_json",
            },
            "var_type": {"S": "CUSTOM"},
        },
        TableName=data.VARIABLES_TABLE,
        UpdateExpression="SET var_val = :r",
        ExpressionAttributeValues={
            ":r": {
                "S": json.dumps(data.CMD_LIST, separators=(",", ":")),
            }
        },
    )

    if web:
        return f'@{context.author.display_name} Command "{args[2].lower()}" added succcessfully.'
    else:
        return await channel_write.send(
            f'@{context.author.display_name} Command "{args[2].lower()}" added succcessfully.'
        )


async def cmd_edit(channel_write, context, args, web=False):
    if len(args) < 4:
        if web:
            return f"@{context.author.display_name} [ERROR] Too few arguments."
        else:
            return await channel_write.send(
                f"@{context.author.display_name} [ERROR] Too few arguments."
            )

    cmd = args[2].lower()

    if cmd not in data.CMD_LIST:
        if web:
            return f'@{context.author.display_name} [ERROR] Command "{cmd}" does not exist.'
        else:
            return await channel_write.send(
                f'@{context.author.display_name} [ERROR] Command "{cmd}" does not exist.'
            )
    cmd_data = data.COMMANDS.get(cmd)
    if not cmd_data:  # Not loaded in yet
        cmd_data = load_command(cmd)

    if not access.authorization(cmd_data["command_permission"]["S"], context.author):
        if web:
            return f'@{context.author.display_name} [ERROR] Command "{cmd}" is above your permission level.'
        else:
            return await channel_write.send(
                f'@{context.author.display_name} [ERROR] Command "{cmd}" is above your permission level.'
            )

    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.update_item(
        Key={
            "command_name": {
                "S": cmd,
            }
        },
        TableName=data.COMMANDS_TABLE,
        UpdateExpression="SET command_response = :r",
        ExpressionAttributeValues={
            ":r": {
                "S": " ".join(args[3:]),
            }
        },
        ReturnValues="ALL_NEW",
    )

    data.COMMANDS[cmd] = response["Attributes"]
    if web:
        return f'@{context.author.display_name} Command "{cmd}" edited succcessfully.'
    else:
        return await channel_write.send(
            f'@{context.author.display_name} Command "{cmd}" edited succcessfully.'
        )


async def cmd_del(channel_write, context, args, web=False):
    cmd = args[2].lower()

    if cmd not in data.CMD_LIST:
        if web:
            return f'@{context.author.display_name} [ERROR] Command "{cmd}" does not exist.'
        else:
            return await channel_write.send(
                f'@{context.author.display_name} [ERROR] Command "{cmd}" does not exist.'
            )
    cmd_data = data.COMMANDS.get(cmd)
    if not cmd_data:  # Not loaded in yet
        cmd_data = load_command(cmd)

    if not access.authorization(cmd_data["command_permission"]["S"], context.author):
        if web:
            return f'@{context.author.display_name} [ERROR] Command "{cmd}" is above your permission level.'
        else:
            return await channel_write.send(
                f'@{context.author.display_name} [ERROR] Command "{cmd}" is above your permission level.'
            )

    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.delete_item(
        Key={
            "command_name": {
                "S": args[2].lower(),
            }
        },
        TableName=data.COMMANDS_TABLE,
    )

    del data.COMMANDS[cmd]
    data.CMD_LIST.remove(cmd)

    response = client.update_item(
        Key={
            "var_name": {
                "S": "_commands_json",
            },
            "var_type": {"S": "CUSTOM"},
        },
        TableName=data.VARIABLES_TABLE,
        UpdateExpression="SET var_val = :r",
        ExpressionAttributeValues={
            ":r": {
                "S": json.dumps(data.CMD_LIST, separators=(",", ":")),
            }
        },
    )

    if cmd in data.ANY_COMMANDS:
        data.ANY_COMMANDS.remove(cmd)
        response = client.update_item(
            Key={
                "var_name": {
                    "S": "_commands_any",
                },
                "var_type": {"S": "CUSTOM"},
            },
            TableName=data.VARIABLES_TABLE,
            UpdateExpression="SET var_val = :r",
            ExpressionAttributeValues={
                ":r": {
                    "S": json.dumps(data.ANY_COMMANDS, separators=(",", ":")),
                }
            },
        )

    if cmd in data.SCHEDULABLE_COMMANDS:
        data.CURRENT_SCHEDULE.pop(cmd, None)
        data.SCHEDULABLE_COMMANDS.remove(cmd)
        response = client.update_item(
            Key={
                "var_name": {
                    "S": "_commands_schedule",
                },
                "var_type": {"S": "CUSTOM"},
            },
            TableName=data.VARIABLES_TABLE,
            UpdateExpression="SET var_val = :r",
            ExpressionAttributeValues={
                ":r": {
                    "S": json.dumps(data.SCHEDULABLE_COMMANDS, separators=(",", ":")),
                }
            },
        )

    if web:
        return f'@{context.author.display_name} Command "{args[2].lower()}" deleted succcessfully.'
    else:
        return await channel_write.send(
            f'@{context.author.display_name} Command "{args[2].lower()}" deleted succcessfully.'
        )


async def cmd_show(channel_write, context, args, web=False):
    cmd = args[2].lower()

    if cmd not in data.CMD_LIST:
        if web:
            return f'@{context.author.display_name} [ERROR] Command "{cmd}" does not exist.'
        else:
            return await channel_write.send(
                f'@{context.author.display_name} [ERROR] Command "{cmd}" does not exist.'
            )
    cmd_data = data.COMMANDS.get(cmd)
    if not cmd_data:  # Not loaded in yet
        cmd_data = load_command(cmd)

    if not access.authorization(cmd_data["command_permission"]["S"], context.author):
        if web:
            return f'@{context.author.display_name} [ERROR] Command "{cmd}" is above your permission level.'
        else:
            return await channel_write.send(
                f'@{context.author.display_name} [ERROR] Command "{cmd}" is above your permission level.'
            )

    if web:
        return cmd_data["command_response"]["S"]
    else:
        return await channel_write.send(cmd_data["command_response"]["S"])


async def cmd_options(channel_write, context, args, web=False):
    cmd = args[2].lower()

    if cmd not in data.CMD_LIST:
        if web:
            return f'@{context.author.display_name} [ERROR] Command "{cmd}" does not exist.'
        else:
            return await channel_write.send(
                f'@{context.author.display_name} [ERROR] Command "{cmd}" does not exist.'
            )
    cmd_data = data.COMMANDS.get(cmd)
    if not cmd_data:  # Not loaded in yet
        cmd_data = load_command(cmd)

    if not access.authorization(cmd_data["command_permission"]["S"], context.author):
        if web:
            return f'@{context.author.display_name} [ERROR] Command "{cmd}" is above your permission level.'
        else:
            return await channel_write.send(
                f'@{context.author.display_name} [ERROR] Command "{cmd}" is above your permission level.'
            )

    if len(args) == 3:  # Show options
        if web:
            return f'Permission={cmd_data["command_permission"]["S"]}, Global={cmd_data["command_cooldown_global"]["N"]}, \
            User={cmd_data["command_cooldown_user"]["N"]}, Schedule={cmd_data["command_cooldown_schedule"]["N"]}, Type={cmd_data["command_type"]["S"]}'
        else:
            return await channel_write.send(
                f'Permission={cmd_data["command_permission"]["S"]}, Global={cmd_data["command_cooldown_global"]["N"]}, \
                User={cmd_data["command_cooldown_user"]["N"]}, Schedule={cmd_data["command_cooldown_schedule"]["N"]}, Type={cmd_data["command_type"]["S"]}'
            )
    else:
        permission = False
        global_cd = False
        user_cd = False
        schedule_cd = False
        cmd_type = False

        options = (" ".join(args[3:])).split(",")
        for opt in options:
            opt_args = opt.strip().split("=")
            if len(opt_args) != 2:
                if web:
                    return (
                        f"@{context.author.display_name} [ERROR] Invalid syntax: {opt}"
                    )
                else:
                    return await channel_write.send(
                        f"@{context.author.display_name} [ERROR] Invalid syntax: {opt}"
                    )
            opt_args = [o.strip() for o in opt_args]
            match opt_args[0].lower():
                case "permission":
                    if opt_args[1] in ["E", "V", "M", "S", "B"]:
                        cmd_data["command_permission"]["S"] = opt_args[1]
                        permission = True
                    else:
                        if web:
                            return f"@{context.author.display_name} [ERROR] Invalid syntax: {opt_args[1]}"
                        else:
                            return await channel_write.send(
                                f"@{context.author.display_name} [ERROR] Invalid syntax: {opt_args[1]}"
                            )
                case "global":
                    if check_int(opt_args[1]):
                        if int(opt_args[1]) >= 0:
                            cmd_data["command_cooldown_global"]["N"] = opt_args[1]
                            global_cd = True
                        else:
                            if web:
                                return f"@{context.author.display_name} [ERROR] Global cooldown cannot be negative."
                            else:
                                return await channel_write.send(
                                    f"@{context.author.display_name} [ERROR] Global cooldown cannot be negative."
                                )
                    else:
                        if web:
                            return f"@{context.author.display_name} [ERROR] Invalid syntax: {opt_args[1]}"
                        else:
                            return await channel_write.send(
                                f"@{context.author.display_name} [ERROR] Invalid syntax: {opt_args[1]}"
                            )
                case "user":
                    if check_int(opt_args[1]):
                        if int(opt_args[1]) >= 0:
                            cmd_data["command_cooldown_user"]["N"] = opt_args[1]
                            user_cd = True
                        else:
                            if web:
                                return f"@{context.author.display_name} [ERROR] User cooldown cannot be negative."
                            else:
                                return await channel_write.send(
                                    f"@{context.uthor.display_name} [ERROR] User cooldown cannot be negative."
                                )
                    else:
                        if web:
                            return f"@{context.uthor.display_name} [ERROR] Invalid syntax: {opt_args[1]}"
                        else:
                            return await channel_write.send(
                                f"@{context.author.display_name} [ERROR] Invalid syntax: {opt_args[1]}"
                            )
                case "schedule":
                    if check_int(opt_args[1]):
                        if 0 <= int(opt_args[1]) < 15:
                            if web:
                                return f"@{context.author.display_name} [ERROR] Schedule interval cannot be less than 15 seconds."
                            else:
                                return await channel_write.send(
                                    f"@{context.author.display_name} [ERROR] Schedule interval cannot be less than 15 seconds."
                                )
                        else:
                            cmd_data["command_cooldown_schedule"]["N"] = opt_args[1]
                            schedule_cd = True
                    else:
                        if web:
                            return f"@{context.author.display_name} [ERROR] Invalid syntax: {opt_args[1]}"
                        else:
                            return await channel_write.send(
                                f"@{context.author.display_name} [ERROR] Invalid syntax: {opt_args[1]}"
                            )
                case "type":
                    if opt_args[1].upper() in ["SIMPLE", "DYNAMIC", "ANY"]:
                        cmd_data["command_type"]["S"] = opt_args[1].upper()
                        cmd_type = True
                    else:
                        if web:
                            return f"@{context.author.display_name} [ERROR] Invalid syntax: {opt_args[1]}"
                        else:
                            return await channel_write.send(
                                f"@{context.author.display_name} [ERROR] Invalid syntax: {opt_args[1]}"
                            )
                case _:
                    if web:
                        return f"@{context.author.display_name} [ERROR] Invalid syntax: {opt_args[0]}"
                    else:
                        return await channel_write.send(
                            f"@{context.author.display_name} [ERROR] Invalid syntax: {opt_args[0]}"
                        )

        data.COMMANDS[cmd] = cmd_data
        client = boto3.client("dynamodb", region_name="us-west-2")
        response = client.put_item(
            Item=cmd_data,
            TableName=data.COMMANDS_TABLE,
        )

        output = []
        if permission:
            output.append("Permission")
        if global_cd:
            output.append("Global Cooldown")
        if user_cd:
            output.append("User Cooldown")
        if schedule_cd:
            output.append("Schedule Cooldown")
            if int(data.COMMANDS[cmd]["command_cooldown_schedule"]["N"]) > 0:
                if cmd not in data.SCHEDULABLE_COMMANDS:
                    data.SCHEDULABLE_COMMANDS.append(cmd)
                    response = client.update_item(
                        Key={
                            "var_name": {
                                "S": "_commands_schedule",
                            },
                            "var_type": {"S": "CUSTOM"},
                        },
                        TableName=data.VARIABLES_TABLE,
                        UpdateExpression="SET var_val = :r",
                        ExpressionAttributeValues={
                            ":r": {
                                "S": json.dumps(
                                    data.SCHEDULABLE_COMMANDS, separators=(",", ":")
                                ),
                            }
                        },
                    )
                # Update schedule even if it is already scheduled, as cooldown might have changed
                data.CURRENT_SCHEDULE[cmd] = random.random() * int(
                    data.COMMANDS[cmd]["command_cooldown_schedule"]["N"]
                )
            else:
                data.CURRENT_SCHEDULE.pop(cmd, None)
                if cmd in data.SCHEDULABLE_COMMANDS:
                    data.SCHEDULABLE_COMMANDS.remove(cmd)
                    response = client.update_item(
                        Key={
                            "var_name": {
                                "S": "_commands_schedule",
                            },
                            "var_type": {"S": "CUSTOM"},
                        },
                        TableName=data.VARIABLES_TABLE,
                        UpdateExpression="SET var_val = :r",
                        ExpressionAttributeValues={
                            ":r": {
                                "S": json.dumps(
                                    data.SCHEDULABLE_COMMANDS, separators=(",", ":")
                                ),
                            }
                        },
                    )
        if cmd_type:
            output.append("Type")
            match cmd_data["command_type"]["S"]:
                case "SIMPLE":
                    if cmd in data.ANY_COMMANDS:
                        data.ANY_COMMANDS.remove(cmd)
                        response = client.update_item(
                            Key={
                                "var_name": {
                                    "S": "_commands_any",
                                },
                                "var_type": {"S": "CUSTOM"},
                            },
                            TableName=data.VARIABLES_TABLE,
                            UpdateExpression="SET var_val = :r",
                            ExpressionAttributeValues={
                                ":r": {
                                    "S": json.dumps(
                                        data.ANY_COMMANDS, separators=(",", ":")
                                    ),
                                }
                            },
                        )
                case "DYNAMIC":
                    hot_reload()
                    if cmd in data.ANY_COMMANDS:
                        data.ANY_COMMANDS.remove(cmd)
                        response = client.update_item(
                            Key={
                                "var_name": {
                                    "S": "_commands_any",
                                },
                                "var_type": {"S": "CUSTOM"},
                            },
                            TableName=data.VARIABLES_TABLE,
                            UpdateExpression="SET var_val = :r",
                            ExpressionAttributeValues={
                                ":r": {
                                    "S": json.dumps(
                                        data.ANY_COMMANDS, separators=(",", ":")
                                    ),
                                }
                            },
                        )
                case "ANY":
                    if cmd not in data.ANY_COMMANDS:
                        data.ANY_COMMANDS.append(cmd)
                        response = client.update_item(
                            Key={
                                "var_name": {
                                    "S": "_commands_any",
                                },
                                "var_type": {"S": "CUSTOM"},
                            },
                            TableName=data.VARIABLES_TABLE,
                            UpdateExpression="SET var_val = :r",
                            ExpressionAttributeValues={
                                ":r": {
                                    "S": json.dumps(
                                        data.ANY_COMMANDS, separators=(",", ":")
                                    ),
                                }
                            },
                        )
                case _:
                    pass

        if web:
            return f'@{context.author.display_name} Updated {", ".join(output)} for command "{cmd}".'
        else:
            return await channel_write.send(
                f'@{context.author.display_name} Updated {", ".join(output)} for command "{cmd}".'
            )


async def quotes(channel_write, context, args, web=False):
    quotes_name = args[0].lower()
    client = boto3.client("dynamodb", region_name="us-west-2")
    if len(args) >= 3:
        if args[1].upper() == "ADD":
            if not access.authorization("M", context.author):
                return await channel_write.send(
                    f"@{context.author.display_name} [ERROR] You do not have permission for this action."
                )
            response = client.update_item(
                Key={
                    "var_name": {
                        "S": f"quotes_{quotes_name}",
                    },
                    "var_type": {"S": "CUSTOM"},
                },
                TableName=data.VARIABLES_TABLE,
                UpdateExpression="ADD var_val :v",
                ExpressionAttributeValues={
                    ":v": {
                        "N": "1",
                    }
                },
                ReturnValues="ALL_NEW",
            )
            index = response["Attributes"]["var_val"]["N"]
            response = client.put_item(
                Item={
                    "quotes_name": {"S": quotes_name},
                    "quotes_index": {"N": index},
                    "quotes_val": {"S": " ".join(args[2:])},
                },
                TableName=data.QUOTES_TABLE,
            )
            if web:
                return f"@{context.author.display_name} Successfully added {quotes_name} #{index}"
            else:
                return await channel_write.send(
                    f"@{context.author.display_name} Successfully added {quotes_name} #{index}"
                )
        elif args[1].upper() == "EDIT":
            if len(args) >= 4:
                if not access.authorization("M", context.author):
                    return await channel_write.send(
                        f"@{context.author.display_name} [ERROR] You do not have permission for this action."
                    )
                response = client.get_item(
                    Key={
                        "var_name": {
                            "S": f"quotes_{quotes_name}",
                        },
                        "var_type": {"S": "CUSTOM"},
                    },
                    TableName=data.VARIABLES_TABLE,
                )
                index = args[2]
                if not index.isdigit():
                    return await channel_write.send(
                        f'@{context.author.display_name} [ERROR] "{index}" is not a positive integer.'
                    )
                if int(index) < 1:
                    return await channel_write.send(
                        f"@{context.author.display_name} [ERROR] Index cannot be less than 1."
                    )
                if int(index) > int(response["Item"]["var_val"]["N"]):
                    return await channel_write.send(
                        f"@{context.author.display_name} [ERROR] \"{index}\" is greater than the last index of {response['Item']['var_val']['N']}."
                    )
                response = client.update_item(
                    Key={
                        "quotes_name": {"S": quotes_name},
                        "quotes_index": {"N": index},
                    },
                    TableName=data.QUOTES_TABLE,
                    UpdateExpression="SET quotes_val=:v",
                    ExpressionAttributeValues={
                        ":v": {
                            "S": " ".join(args[3:]),
                        }
                    },
                    ReturnValues="ALL_NEW",
                )
                if web:
                    return f"@{context.author.display_name} Successfully edited {quotes_name} #{index}"
                else:
                    return await channel_write.send(
                        f"@{context.author.display_name} Successfully edited {quotes_name} #{index}"
                    )
    elif len(args) >= 2:
        if args[1].isdigit():
            response = client.get_item(
                Key={
                    "var_name": {
                        "S": f"quotes_{quotes_name}",
                    },
                    "var_type": {"S": "CUSTOM"},
                },
                TableName=data.VARIABLES_TABLE,
            )
            index = args[1]
            if int(index) < 1:
                return await channel_write.send(
                    f"@{context.author.display_name} [ERROR] Index cannot be less than 1."
                )
            if int(index) > int(response["Item"]["var_val"]["N"]):
                return await channel_write.send(
                    f"@{context.author.display_name} [ERROR] \"{index}\" is greater than the last index of {response['Item']['var_val']['N']}."
                )
            response = client.get_item(
                Key={
                    "quotes_name": {"S": quotes_name},
                    "quotes_index": {"N": index},
                },
                TableName=data.QUOTES_TABLE,
            )
            return await channel_write.send(response["Item"]["quotes_val"]["S"])

    # Get last index
    response = client.get_item(
        Key={
            "var_name": {
                "S": f"quotes_{quotes_name}",
            },
            "var_type": {"S": "CUSTOM"},
        },
        TableName=data.VARIABLES_TABLE,
    )
    last_index = int(response["Item"]["var_val"]["N"])
    response = client.get_item(
        Key={
            "quotes_name": {"S": quotes_name},
            "quotes_index": {"N": str(random.randrange(1, last_index + 1))},
        },
        TableName=data.QUOTES_TABLE,
    )
    return await channel_write.send(response["Item"]["quotes_val"]["S"])


async def pyramid(channel_write, author, msg):
    repetition = r"\s+\1"
    increase = None
    decrease = None

    if data.PYRAMID_WIDTH_MAX < data.PYRAMID_WIDTH_NEXT:  # Increase phase
        if data.PYRAMID_WIDTH_NEXT == 1:  # New pyramid
            increase = re.match(r"^(\w+)$", msg)
            if increase:  # Starting pyramid
                data.PYRAMID_WORD = increase.group()
                data.PYRAMID_WIDTH_MAX += 1
                data.PYRAMID_WIDTH_NEXT += 1
        else:  # Pyramid in progress
            increase = re.match(
                f"^({data.PYRAMID_WORD})"
                + repetition * (data.PYRAMID_WIDTH_NEXT - 1)
                + "$",
                msg,
            )
            if data.PYRAMID_WIDTH_MAX >= 3:  # Can decrease (When max width >=3)
                decrease = re.match(
                    f"^({data.PYRAMID_WORD})"
                    + repetition * (data.PYRAMID_WIDTH_MAX - 2)
                    + "$",
                    msg,
                )
            if increase:
                data.PYRAMID_WIDTH_MAX += 1
                data.PYRAMID_WIDTH_NEXT += 1
            elif decrease:
                data.PYRAMID_WIDTH_NEXT -= 3
            else:  # Pyramid broke
                data.PYRAMID_WIDTH_MAX = 0
                data.PYRAMID_WIDTH_NEXT = 1
                # Potential new pyramid
                increase = re.match(r"^(\w+)$", msg)
                if increase:  # Starting pyramid
                    data.PYRAMID_WORD = increase.group()
                    data.PYRAMID_WIDTH_MAX += 1
                    data.PYRAMID_WIDTH_NEXT += 1
    else:  # Decrease phase
        decrease = re.match(
            f"^({data.PYRAMID_WORD})"
            + repetition * (data.PYRAMID_WIDTH_NEXT - 1)
            + "$",
            msg,
        )
        if decrease:
            if data.PYRAMID_WIDTH_NEXT == 1:  # Success!
                match data.PYRAMID_WIDTH_MAX:
                    case 3:
                        await channel_write.send(
                            f"Nice 3-width {data.PYRAMID_WORD} myd {author.display_name} ... but is that really the best you've got? inaboxSus"
                        )
                    case 4:
                        await channel_write.send(
                            f"Nice work on the best number {data.PYRAMID_WORD} myd {author.display_name} inaboxGasm inaboxGasm inaboxGasm inaboxGasm"
                        )
                    case _:
                        await channel_write.send(
                            f"{author.display_name} just finished a {data.PYRAMID_WIDTH_MAX}-width {data.PYRAMID_WORD} myd. Now you've got my attention inaboxPog"
                        )
                data.PYRAMID_WIDTH_MAX = 0
                data.PYRAMID_WIDTH_NEXT = 1
            else:  # Should decrease further
                data.PYRAMID_WIDTH_NEXT -= 1
        else:  # Pyramid broke
            data.PYRAMID_WIDTH_MAX = 0
            data.PYRAMID_WIDTH_NEXT = 1
            # Potential new pyramid
            increase = re.match(r"^(\w+)$", msg)
            if increase:  # Starting pyramid
                data.PYRAMID_WORD = increase.group()
                data.PYRAMID_WIDTH_MAX += 1
                data.PYRAMID_WIDTH_NEXT += 1


async def sub_alert(channel_write, tags):
    months = None
    display_name = None
    if tags["msg-id"] == "sub" or tags["msg-id"] == "resub":
        months = tags["msg-param-cumulative-months"]
        display_name = tags.get("display-name")
        if not display_name:
            display_name = tags["login"]
    elif tags["msg-id"] == "subgift":
        months = tags["msg-param-months"]
        display_name = tags.get("msg-param-recipient-display-name")
        if not display_name:
            display_name = tags["msg-param-recipient-user-name"]

    if not months:
        return
    if months == "1":
        await channel_write.send(
            f"{display_name} just subscribed inaboxPog Welcome to The Box!"
        )
    else:
        await channel_write.send(
            f"Welcome back to The Box, {display_name}! inaboxPog Thanks for subscribing for {months} months in a row inaboxLove"
        )


def web_api_response(msg):
    client = boto3.client("sqs", region_name="us-west-2")
    response = client.send_message(
        QueueUrl="https://sqs.us-west-2.amazonaws.com/414556232085/inabot-API-response",
        MessageBody=msg,
    )


def get_queue():
    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.get_item(
        Key={
            "var_name": {
                "S": "queue",
            },
            "var_type": {"S": "CUSTOM"},
        },
        TableName=data.VARIABLES_TABLE,
    )
    return json.loads(response["Item"]["var_val"]["S"])


def save_queue(queue):
    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.update_item(
        Key={
            "var_name": {
                "S": "queue",
            },
            "var_type": {"S": "CUSTOM"},
        },
        TableName=data.VARIABLES_TABLE,
        UpdateExpression="SET var_val=:v",
        ExpressionAttributeValues={
            ":v": {
                "S": json.dumps(queue, separators=(",", ":")),
            }
        },
        ReturnValues="ALL_NEW",
    )


def new_commands_page():
    if data.IS_LIVE:
        client = boto3.client("lambda", region_name="us-west-2")
        response = client.invoke(
            FunctionName="CommandsPage",
            InvocationType="Event",
        )
