from queue import Queue
from lru import LRU

INABOT_ID = "681131749"
# BROADCASTER_ID = "57184879"
BROADCASTER_ID = "160025583"
COMMANDS_TABLE = "inabot-commands"
VARIABLES_TABLE = "inabot-variables"
QUOTES_TABLE = "inabot-quotes"
TOKENS_TABLE = "CF-Cookies"
SQS_URL = "https://sqs.us-west-2.amazonaws.com/414556232085/inabot-queue"
SUPERMODS = ["mike_hu_0_0"]

BRACKET_L = "${"
BRACKET_R = "}"

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

CURRENT_SCHEDULE = {}
# {
#     "!dice": 16.960158397654475,
#     "!test": 3.235009327883418
# }

SQS_QUEUE = Queue()
