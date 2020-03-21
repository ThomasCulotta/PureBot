import re
import random

from BotRequests import GetUserId, GetGame
from FlushPrint import ptf, ptfDebug
from TwitchUtils import CheckPriv
import RegGroups as groups

class ShoutoutCommands():
    def __init__(self):
        self.activeCommands = {
            "shoutout",
        }

    def Execute(self, msg):
        # snippet start
        # shoutout (@)USER
        # shoutout PureSushi
        # shoutout @PureSushi
        # remarks
        # Mod Only. Promotes the given user's channel.
        if msg.message.startswith("shoutout"):
            if not CheckPriv(msg.tags):
                return f"[{msg.user}]: Regular users can't shoutout"

            regMatch = re.match(f"^shoutout @{groups.user}$", msg.message)

            if regMatch == None:
                regMatch = re.match(f"^shoutout {groups.user}$", msg.message)

                if regMatch == None:
                    return f"[{msg.user}]: The syntax for that command is: shoutout USER"

            user = regMatch.group(1)

            if GetUserId(user) == None:
                return f"[{msg.user}]: {user} is not an existing username."

            game = GetGame(user)
            emote = random.choice(["OhMyDog", "PogChamp", ":D", ])
            response = f"Follow @{user} over at twitch.tv/{user} ! "

            if game == None:
                response += f"{emote}"
            else:
                response += f"<3 Was last seen playing \"{game}\" {emote}"

            return response
