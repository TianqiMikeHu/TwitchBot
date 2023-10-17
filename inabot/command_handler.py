import data
import helper
import random
import re
import time
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

    if cmd not in data.CMD_LIST:
        # Try ANY POSITION match
        if len(data.ANY_COMMANDS) > 0:
            match = re.findall(
                r"\b" + r"\b|\b".join(data.ANY_COMMANDS) + r"\b", " ".join(args)
            )
            if len(match) > 0:
                cmd = match[0]
            else:  # Beanie regex
                if re.search(
                    r"[bßᵇᵦǝ][eéêëèEÉÈÊËĒₑᵉᴉq3][aààâäAÀÂÅᵃₐu][ñnNÑⁿₙɐ][iîïÎÏIᵢᶦǝ][eéêëèEÉÈÊËĒᵉₑ!q3]",
                    " ".join(args),
                ):
                    return await channel_write.send(
                        f"@{context.author.display_name} I think you mean toque inaboxToque"
                    )
                return
        else:
            return
    cmd_data = data.COMMANDS.get(cmd)
    if not cmd_data:  # Not loaded in yet
        cmd_data = helper.load_command(cmd)

    # print(f"VIP: {author.is_vip}; MOD: {author.is_mod}; SUPERMODS {author.name in data.SUPERMODS}; BROADCASTER: {author.is_broadcaster}")
    if context is not None:  # Schedule is exempt from permission check
        if not access.authorization(
            cmd_data["command_permission"]["S"], context.author
        ):
            return

    if context is not None:  # Schedule is exempt from cooldown check
        if not access.cooldown_approved(cmd, context.author.display_name):
            return

    if cmd_data["command_type"]["S"] != "DYNAMIC":
        await channel_write.send(
            helper.parse_variables(cmd_data["command_response"]["S"], context, args)
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


async def dynamic_handler(cmd, channel_read, channel_write, context, args):
    execute = getattr(custom_code, cmd)
    await execute(channel_read, channel_write, context, args)
