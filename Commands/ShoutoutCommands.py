import re
import json
import random

from Utilities.BotRequests import GetUserId, GetGame
from Utilities.FlushPrint import ptf, ptfDebug
import Utilities.TwitchUtils as util
import Utilities.RegGroups as groups

class ShoutoutCommands():
    def __init__(self):
        self.autoShoutoutFile = "Commands/AutoShoutoutUsers.json"

        with open(self.autoShoutoutFile, 'r') as file:
            self.autoShoutoutUsers = json.load(file)

        self.activeCommands = {
            "shoutout" : self.ExecuteShoutout,
        }

        self.activeOnBroadcasterJoinEvents = {
            self.ExecuteOnBroadcasterJoinShoutout
        }

        self.activeOnRaidEvents = {
            self.ExecuteOnRaidShoutout
        }

        self.shoutoutRegex = re.compile(f"^shoutout {groups.user}")

    def ShoutoutHelper(self, user, msgUser):
        if GetUserId(user) == None:
            return f"[{msgUser}]: {user} is not an existing username."

        game = GetGame(user)
        emote = random.choice(["OhMyDog", "PogChamp", ":D", ])
        response = f"Follow @{user} over at twitch.tv/{user} ! "

        if game == None:
            response += f"{emote}"
        else:
            response += f"<3 Was last seen playing \"{game}\" {emote}"

        return response

    # snippet start
    # shoutout USER
    # shoutout PureSushi
    # shoutout @PureSushi
    # remarks
    # Mod Only. Promotes the given user's channel.
    def ExecuteShoutout(self, msg):
        if not util.CheckPrivMod(msg.tags):
            return f"[{msg.user}]: Only mods can shoutout"

        regMatch = self.shoutoutRegex.match(msg.message)

        if regMatch == None:
            return f"[{msg.user}]: The syntax for that command is: shoutout USER"

        return self.ShoutoutHelper(regMatch.group("user"), msg.user)

    # Event on broadcaster join
    def ExecuteOnBroadcasterJoinShoutout(self):
        with open(self.autoShoutoutFile, 'r') as file:
            self.autoShoutoutUsers = json.load(file)

    # Event on raid
    def ExecuteOnRaidShoutout(self, user):
        try:
            self.autoShoutoutUsers.remove(user)
        except ValueError:
            return

        return self.ShoutoutHelper(user, "puresushibot")
