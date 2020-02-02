import re
import random

from TwitchWebsocket import TwitchWebsocket

from BotRequests import GetUserId, GetGame
from FlushPrint import ptf, ptfDebug
import RegGroups as groups

# TODO: global SendMessage possibility?

class ShoutoutCommands():
    def __init__(self):
        pass

    def Execute(self, msg):
        if msg.message.startswith("shoutout"):
            if msg.tags['mod'] != '1':
                return f"[{msg.user}]: Regular users can't shoutout"

            regMatch = re.match(f"^shoutout @{groups.regUserGroup}$", msg.message)

            if regMatch == None:
                regMatch = re.match(f"^shoutout {groups.regUserGroup}$", msg.message)

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
