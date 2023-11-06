from queue import Queue
from lru import LRU

INABOT_ID = "687759326"
BROADCASTER_ID = "57184879"
# INABOT_ID = "681131749"
# BROADCASTER_ID = "160025583"
CLIENT_ID = ""

COMMANDS_TABLE = "inabot-commands"
VARIABLES_TABLE = "inabot-variables"
QUOTES_TABLE = "inabot-quotes"
TOKENS_TABLE = "CF-Cookies"
SQS_URL = "https://sqs.us-west-2.amazonaws.com/414556232085/inabot-queue"
SQS_RESPONSE_URL = (
    "https://sqs.us-west-2.amazonaws.com/414556232085/inabot-API-response"
)
SUPERMODS = ["mike_hu_0_0"]

BRACKET_L = "${"
BRACKET_R = "}"

PYRAMID_WIDTH_MAX = 0
PYRAMID_WIDTH_NEXT = 1
PYRAMID_WORD = None

ACCESS_TOKENS = {}
# Key: user_id
# Val: Access Token

CMD_LIST = []  # ['!cmd1', '!cmd2', ...]
COMMANDS = LRU(50)
# Key: command_name
# Val: {
#     "command_type": {
#         "S": "SIMPLE"
#     },
#     "command_cooldown_schedule": {
#         "N": "-1"
#     },
#     "command_response": {
#         "S": "https://clips.twitch.tv/HealthyCalmVultureStrawBeary-Q6ZGYM3Pd0yW7kCo"
#     },
#     "command_name": {
#         "S": "!inabox44"
#     },
#     "command_cooldown_user": {
#         "N": "15"
#     },
#     "command_cooldown_global": {
#         "N": "15"
#     }
# }

COOLDOWN = {}

ANY_COMMANDS = []  # ['!cmd1', '!cmd2', ...]
SCHEDULABLE_COMMANDS = []  # ['!cmd1', '!cmd2', ...]
COUNTERS_LIST = []

CURRENT_SCHEDULE = {}
# {
#     "!dice": 16.960158397654475,
#     "!test": 3.235009327883418
# }

REGEX = {
    r"[bßᵇᵦǝ][eéêëèEÉÈÊËĒₑᵉᴉq3][aààâäAÀÂÅᵃₐu][ñnNÑⁿₙɐ][iîïÎÏIᵢᶦǝ][eéêëèEÉÈÊËĒᵉₑ!q3]": "!beanie",
    r"\btab(?:s|bed)?\b": "!bpaddtab",
}

SQS_QUEUE = Queue()

PERMIT = []

IS_LIVE = False


class WebContext:
    def __init__(self, author):
        self.author = author


class WebAuthor:
    def __init__(
        self, display_name, name, is_broadcaster=False, is_mod=True, is_vip=True
    ):
        self.display_name = display_name
        self.name = name
        self.is_broadcaster = is_broadcaster
        self.is_mod = is_mod
        self.is_vip = is_vip
