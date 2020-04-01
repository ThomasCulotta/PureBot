import re
import random

from FlushPrint import ptf, ptfDebug
import RegGroups as groups

class DiceCommands():
    def __init__(self):
        self.activeCommands = {
            "roll" : self.ExecuteRoll,
        }

        self.rollRegex = re.compile(f"^roll {groups.num}d{groups.num1}")

    # snippet start
    # roll NUMdNUM
    # roll 1d20
    # roll 7d100
    # remarks
    # Between 1 and 10 dice may be rolled. Dice options are d2 to d100.
    def ExecuteRoll(self, msg):
        regMatch = self.rollRegex.match(msg.message)

        if regMatch == None:
            return f"[{msg.user}]: The syntax for that command is: roll NUMdNUM (roll 1d20)"

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
