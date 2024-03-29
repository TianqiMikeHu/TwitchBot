import data
import helper
import random
import re
from datetime import datetime
import pytz
import custom_code
import access


def initialize_schedule(schedule_routine):
    try:
        schedule_routine.cancel()
    except:
        pass
    # Load commands again
    data.CURRENT_SCHEDULE = {}
    for cmd in data.SCHEDULABLE_COMMANDS:
        cmd_data = data.COMMANDS.get(cmd)
        if not cmd_data:  # Not loaded in yet
            cmd_data = helper.load_command(cmd)
        data.CURRENT_SCHEDULE[cmd] = random.random() * int(
            cmd_data["command_cooldown_schedule"]["N"]
        )
    schedule_routine.start(stop_on_error=False)


async def schedule_handler(channel_read, channel_write):
    occurred = False
    for cmd, time in data.CURRENT_SCHEDULE.items():
        if time <= 0 and not occurred:
            occurred = True
            await parse_command(channel_read, channel_write, None, [cmd])
            data.CURRENT_SCHEDULE[cmd] = (
                int(data.COMMANDS[cmd]["command_cooldown_schedule"]["N"])
                + random.random() * 20
                - 10
            )  # +-10 seconds randomness
        else:
            data.CURRENT_SCHEDULE[cmd] -= 10


async def parse_command(channel_read, channel_write, context, args):
    cmd = args[0].lower()
    original = " ".join(args).lower()

    if cmd not in data.CMD_LIST:
        match = False
        if len(data.ANY_COMMANDS) > 0:  # Try ANY POSITION match
            for c in data.ANY_COMMANDS:
                regex = r"(?:(?<=\s)|(?<=^))" + c + r"(?=$|\s)"
                try:
                    if re.search(regex, original):
                        cmd = c
                        match = True
                        break
                except:
                    pass
        if not match:  # Regex aliases
            for regex in data.REGEX:
                try:
                    if re.search(regex, original):
                        cmd = data.REGEX[regex]
                        match = True
                        break
                except:
                    pass

    skip = False
    if cmd in data.CMD_LIST:
        cmd_data = data.COMMANDS.get(cmd)
        if not cmd_data:  # Not loaded in yet
            cmd_data = helper.load_command(cmd)

        # print(f"VIP: {author.is_vip}; MOD: {author.is_mod}; SUPERMODS {author.name in data.SUPERMODS}; BROADCASTER: {author.is_broadcaster}")
        if context is not None:  # Schedule is exempt from permission check
            if not access.authorization(
                cmd_data["command_permission"]["S"], context.author
            ):
                skip = True

        if context is not None:  # Schedule is exempt from cooldown check
            if not access.cooldown_approved(cmd, context.author.display_name):
                skip = True

        if not skip:
            if cmd_data["command_type"]["S"] != "DYNAMIC":
                await channel_write.send(
                    helper.parse_variables(
                        cmd_data["command_response"]["S"], context, args
                    )
                )
            else:
                # DYNAMIC
                await dynamic_handler(
                    cmd_data["command_response"]["S"],
                    channel_read,
                    channel_write,
                    context,
                    args,
                )

    # Things to process after the primary command. Regex commands here should be DYNAMIC ONLY with EVERYONE permission
    for regex in data.POST_COMMAND_REGEX:
        try:
            if re.search(regex, original):
                cmd = data.POST_COMMAND_REGEX[regex]
                cmd_data = data.COMMANDS.get(cmd)
                if not cmd_data:  # Not loaded in yet
                    cmd_data = helper.load_command(cmd)
                await dynamic_handler(
                    cmd_data["command_response"]["S"],
                    channel_read,
                    channel_write,
                    context,
                    args,
                )
        except:
            pass
    if context:
        data.ACTIVE_CHATTERS[context.author.display_name] = datetime.utcnow().replace(
            tzinfo=pytz.utc
        )


async def dynamic_handler(cmd, channel_read, channel_write, context, args):
    execute = getattr(custom_code, cmd)
    await execute(channel_read, channel_write, context, args)
