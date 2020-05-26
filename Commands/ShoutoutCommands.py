import re
import random

from Utilities.BotRequests import GetUserId, GetGame
from Utilities.FlushPrint import ptf
import Utilities.TwitchUtils as util
import Utilities.RegGroups as groups

class ShoutoutCommands():
    def __init__(self):
        self.activeCommands = {
            # snippet start
            # shoutout USER
            # shoutout PureSushi
            # shoutout @PureSushi
            # remarks
            # Mod Only. Promotes the given user's channel.
            "shoutout" : self.ExecuteShoutout,
        }

        self.shoutoutRegex = re.compile(f"^shoutout {groups.user}")

    def ExecuteShoutout(self, msg):
        if not util.CheckPrivMod(msg.tags):
            return f"[{msg.user}]: Only mods can shoutout"

        if (regMatch := self.shoutoutRegex.match(msg.message)) is None:
            return util.GetSyntax(msg.user, "shoutout USER")

        user = regMatch.group("user")

        if GetUserId(user) == None:
            return f"[{msg.User}]: {user} is not an existing username."

        emote = random.choice(["OhMyDog", "PogChamp", ":D", ])
        response = f"Follow @{user} over at twitch.tv/{user} ! "

        if (game := GetGame(user)) is None:
            response += f"{emote}"
        else:
            response += f"<3 Was last seen playing \"{game}\" {emote}"

        return response
