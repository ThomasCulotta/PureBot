import re
import time
import random
import threading

from FlushPrint import ptf, ptfDebug
from TwitchUtils import SendMessage
import RegGroups as groups

class VoteBanCommands():
    def __init__(self):
        self.activeCommands = {
            "voteban",
        }

        self.beginResponses = [
            "Preparing to ban {0}...",
            "{0} has broken all known rules of chat...",
            "The time has come for {0}..."
        ]

        self.threadRunning = False
        self.banThread = None

    def VoteBanAsync(self, user):
        SendMessage(random.choice(self.beginResponses).format(user))
        time.sleep(1.800)
        SendMessage(f"{user} will be banned in 3...")
        time.sleep(0.680)
        SendMessage("2...")
        time.sleep(0.880)
        SendMessage("1...")
        time.sleep(1.080)
        SendMessage(f"/me {user} is cute and important and cannot be banned from this chat GivePLZ <3")

        self.threadRunning = False
        return

    # TODO: integrate optional @ for user RegGroup
    def Execute(self, msg):
        # snippet start
        # voteban (@)USER
        # voteban BabotzInc
        # voteban @BabotzInc
        # remarks
        # This is a joke command.
        regMatch = re.match(f"^voteban @?{groups.user}$", msg.message)

        if regMatch == None:
            return f"[{msg.user}]: The syntax for that command is: voteban USER"

        if self.threadRunning:
            return f"[{msg.user}]: Busy banning someone else."

        user = regMatch.group(1)

        self.threadRunning = True
        self.banThread = threading.Thread(target=self.VoteBanAsync, args=[user])
        self.banThread.start()

        return
