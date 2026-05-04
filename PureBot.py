import pymongo
import time

from Utilities.TwitchWebsocket.TwitchWebsocket import TwitchWebsocket
from Utilities.TwitchAuth import TwitchAuth

import botconfig

from Utilities.FlushPrint import ptf, ptfDebug
import Utilities.TwitchUtils as util

from Commands import *

class PureBot:
    def __init__(self):
        self.chan = botconfig.twitchChannel
        self.prefixes = botconfig.prefixes
        self.client = None
        if botconfig.DbConnectionString and botconfig.DbConnectionString != "":
            self.client = pymongo.MongoClient(f"{botconfig.DbConnectionString}", socketTimeoutMS=5000)
        else:
            ptf("Mongo connection string not found in botconfig")

        # Get OAuth token using TwitchAuth with retry
        self.auth = TwitchAuth(botconfig.clientId, botconfig.clientSecret, botconfig.authCode)
        oauth_token = None
        retry_delays = [5, 15, 30, 60, 120]
        for attempt in range(len(retry_delays) + 1):
            oauth_token = self.auth.GetAccessToken()
            if oauth_token:
                break
            if attempt < len(retry_delays):
                delay = retry_delays[attempt]
                ptf(f"Failed to obtain OAuth token (attempt {attempt + 1}/{len(retry_delays) + 1}). Retrying in {delay}s...", time=True)
                time.sleep(delay)
        
        if not oauth_token:
            raise Exception("Failed to obtain OAuth token after all retry attempts")

        # Send along all required information, and the bot will start
        # sending messages to your callback function. (self.message_handler in this case)
        self.ws = TwitchWebsocket(host="irc.chat.twitch.tv",
                                  port=6667,
                                  chan="#" + self.chan,
                                  nick=botconfig.twitchUser,
                                  auth=f"oauth:{oauth_token}",
                                  callback=self.message_handler,
                                  capability=["membership", "tags", "commands"],
                                  live=True,
                                  auth_provider=self.auth)

        util.InitializeUtils(self.ws, self.chan, self.client)

        # List of command names and args required for their constructor
        args = (self.chan, self.client)
        commandNames = {
            "WhoCommands" : args,
            "ScoreCommands" : args,
            "QuoteCommands" : args,
            "CustomCommands" : args,
            "PollCommands" : (),
            "DiceCommands" : (),
            "TimeCommands" : (),
            "VoteBanCommands" : (),
            "ShoutoutCommands" : (),
            "FindGameCommands" : (),
            "FindSongCommands" : (),
            "FindFoodCommands" : (),
        }

        for name in botconfig.exclude:
            del commandNames[name]

        self.commands = {}

        # Dynamically load commands with appropriate args
        for name, arg in commandNames.items():
            self.commands[name] = getattr(globals()[name], name)(*arg)

        # Maps all active command strings caught by imported command modules to their respective Execute function
        self.execute = {}

        # Maps all active channel points custom reward ids caught by imported command modules to their respective RedeemReward function
        self.redeem = {}

        for cmd in self.commands.values():
            if hasattr(cmd, "activeCommands"):
                self.execute = {**self.execute, **cmd.activeCommands}

            if hasattr(cmd, "activeRewards"):
                self.redeem = {**self.redeem, **cmd.activeRewards}

        self.ws.start_bot()
        # Any code after this will be executed after a KeyboardInterrupt

    def message_handler(self, m):
        # Check for proper message type
        if (m.type != "PRIVMSG" and
            m.type != "WHISPER"):
            return

        # Check for valid message with prefix and valid rewards
        validReward = "custom-reward-id" in m.tags
        validCommand = m.message != None and len(m.message) > 1 and m.message[0] in self.prefixes

        if (not validReward and
            not validCommand):
            return

        try:
            if validReward:
                util.LogReceived(m.type, m.user, m.message, m.tags)
                util.SendMessage(self.redeem[m.tags["custom-reward-id"]](m), m.type, m.user)

            if validCommand:
                # Retrieve first word without prefix
                m.message = m.message[1:]
                token = m.message.lower().split()[0]

                if (token in self.execute):
                    util.LogReceived(m.type, m.user, m.message, m.tags, True)
                    util.SendMessage(self.execute[token](m), m.type, m.user)
                    return

                # Simple response commands
                # Note that we don't get this far unless the message does not match other commands
                response = self.commands["CustomCommands"].Execute(m)
                if response != None:
                    util.SendMessage(response, m.type, m.user)
                    return

        except Exception as e:
            ptf(f"Error: {e}", time=True)

if __name__ == "__main__":
    PureBot()
