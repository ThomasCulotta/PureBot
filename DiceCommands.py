import re
import random

from TwitchWebsocket import TwitchWebsocket

from BotRequests import GetUserId, GetGame
from FlushPrint import ptf, ptfDebug
import RegGroups as groups

class DiceCommands():
    def __init__(self):
        pass

    def Execute(self, msg):

        # snippet start
        # roll NUMdNUM
        # roll 1d20
        # roll 7d100
        if msg.message.startswith("roll"):
            regMatch = re.match(f"^roll {groups.regNumGroup}d{groups.regNumGroup}$", msg.message)

            if regMatch == None:
                return f"[{msg.user}]: The syntax for that command is: roll NUMdNUM (roll 1d20)"

            num = int(regMatch.group(1))
            die = int(regMatch.group(2))

            if (num < 1 or
                num > 10):
                return f"[{msg.user}]: You can only roll between 1 and 10 dice"

            if (die < 2 or
                die > 100):
                return f"[{msg.user}]: You can only use dice between d2 and d100"

            total = 0

            for i in range(num):
                total += random.randint(1, die)

            return f"{msg.user} rolled a {total}"
