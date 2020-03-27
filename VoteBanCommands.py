import re
import time
import random
import threading

from FlushPrint import ptf, ptfDebug
import TwitchUtils as util
import RegGroups as groups

class VoteBanCommands():
    def __init__(self):
        self.activeCommands = {
            "voteban" : self.ExecuteVoteBan,
        }

        self.beginResponses = [
            "Preparing to ban {0}...",
            "{0} has broken all known rules of chat...",
            "The time has come for {0}..."
        ]

        self.threadRunning = False
        self.banThread = None

    def VoteBanAsync(self, user):
        util.SendMessage(random.choice(self.beginResponses).format(user))
        time.sleep(1.800)
        util.SendMessage(f"{user} will be banned in 3...")
        time.sleep(0.680)
        util.SendMessage("2...")
        time.sleep(0.880)
        util.SendMessage("1...")
        time.sleep(1.080)
        util.SendMessage(f"/me {user} is cute and important and cannot be banned from this chat GivePLZ <3")

        self.threadRunning = False
        return

    # snippet start
    # voteban USER
    # voteban BabotzInc
    # voteban @BabotzInc
    # remarks
    # This is a joke command.
    def ExecuteVoteBan(self, msg):
        regMatch = re.match(f"^voteban {groups.user}$", msg.message)

        if regMatch == None:
            return f"[{msg.user}]: The syntax for that command is: voteban USER"

        if self.threadRunning:
            return f"[{msg.user}]: Busy banning someone else."

        user = regMatch.group(1)

        self.threadRunning = True
        self.banThread = threading.Thread(target=self.VoteBanAsync, args=[user])
        self.banThread.start()

        return
