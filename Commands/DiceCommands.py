import re
import random

from Utilities.FlushPrint import ptf
import Utilities.TwitchUtils as util
import Utilities.RegGroups as groups

class DiceCommands():
    def __init__(self):
        self.activeCommands = {
            # snippet start
            # roll NUMdNUM
            # roll 1d20
            # roll 7d100
            # remarks
            # Between 1 and 10 dice may be rolled. Dice options are d2 to d100.
            "roll" : self.ExecuteRoll,
        }

        self.rollRegex = re.compile(f"^roll {groups.num}d{groups.num1}")

    def ExecuteRoll(self, msg):
        if (regMatch := self.rollRegex.match(msg.message)) is None:
            return util.GetSyntax(msg.user, "roll NUMdNUM (roll 1d20)")

        num = int(regMatch.group("num0"))
        die = int(regMatch.group("num1"))

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
