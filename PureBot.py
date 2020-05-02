import pymongo

from TwitchWebsocket import TwitchWebsocket

import botconfig

from Utilities.FlushPrint import ptf, ptfDebug
import Utilities.TwitchUtils as util

from Commands import *

client = pymongo.MongoClient(f"mongodb://{botconfig.DBusername}:{botconfig.DBpassword}@{botconfig.DBhostIP}/QuoteBotDB")

class PureBot:
    def __init__(self):
        self.chan = botconfig.twitchChannel
        self.prefix = botconfig.prefix

        # Send along all required information, and the bot will start
        # sending messages to your callback function. (self.message_handler in this case)
        self.ws = TwitchWebsocket(host="irc.chat.twitch.tv",
                                  port=6667,
                                  chan="#" + self.chan,
                                  nick=botconfig.twitchUser,
                                  auth=botconfig.oauth,
                                  callback=self.message_handler,
                                  capability=["membership", "tags", "commands"],
                                  live=True)

        util.InitializeUtils(self.ws, self.chan, client)

        # List of command names and args required for their constructor
        args = (self.chan, client)
        commandNames = {
            "WhoCommands" : args,
            "ScoreCommands" : args,
            "QuoteCommands" : args,
            "PollCommands" : (),
            "DiceCommands" : (),
            "TimeCommands" : (),
            "CustomCommands" : (),
            "VoteBanCommands" : (),
            "ShoutoutCommands" : (),
            "FindGameCommands" : (),
            "FindSongCommands" : (),
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
        validCommand = m.message != None and len(m.message) > 1 and m.message[0] == self.prefix

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
