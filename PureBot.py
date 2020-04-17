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

        self.commands = {}

        if "who" not in botconfig.exclude:
            self.commands["who"] = WhoCommands.WhoCommands(self.chan, client)
        if "score" not in botconfig.exclude:
            self.commands["score"] = ScoreCommands.ScoreCommands(self.chan, client)
        if "quote" not in botconfig.exclude:
            self.commands["quote"] = QuoteCommands.QuoteCommands(self.chan, client)
        if "poll" not in botconfig.exclude:
            self.commands["poll"] = PollCommands.PollCommands()
        if "dice" not in botconfig.exclude:
            self.commands["dice"] = DiceCommands.DiceCommands()
        if "time" not in botconfig.exclude:
            self.commands["time"] = TimeCommands.TimeCommands()
        if "custom" not in botconfig.exclude:
            self.commands["custom"] = CustomCommands.CustomCommands()
        if "voteban" not in botconfig.exclude:
            self.commands["voteban"] = VoteBanCommands.VoteBanCommands()
        if "shoutout" not in botconfig.exclude:
            self.commands["shoutout"] = ShoutoutCommands.ShoutoutCommands()

        # Maps all active command strings caught by imported command modules to their respective Execute function
        self.execute = {}

        # Maps all active channel points custom reward ids caught by imported command modules to their respective RedeemReward function
        self.redeem = {}

        # Tracks all active events to execute on broadcaster join
        self.onBroadcasterJoin = {}

        # Tracks all active events to execute on raid
        self.onRaid = {}

        for cmd in self.commands.values():
            if hasattr(cmd, "activeCommands"):
                self.execute = {**self.execute, **cmd.activeCommands}

            if hasattr(cmd, "activeRewards"):
                self.redeem = {**self.redeem, **cmd.activeRewards}

            if hasattr(cmd, "activeOnBroadcasterJoinEvents"):
                self.onBroadcasterJoin = {*self.onBroadcasterJoin, *cmd.activeOnBroadcasterJoinEvents}

            if hasattr(cmd, "activeOnRaidEvents"):
                self.onRaid = {*self.onRaid, *cmd.activeOnRaidEvents}

        ptf("Bot Started!")

        self.ws.start_bot()
        # Any code after this will be executed after a KeyboardInterrupt

    def message_handler(self, m):
        joining = m.type == "JOIN"

        # Check for proper message type
        if (m.type != "PRIVMSG" and
            m.type != "WHISPER" and
            m.type != "USERNOTICE" and
            not joining):
            return

        # Check for valid message with prefix, valid rewards, and raids
        raiding = "msg-id" in m.tags and m.tags["msg-id"] == "raid"
        validReward = not joining and "custom-reward-id" in m.tags
        validCommand = not joining and m.message != None and m.message[0] == self.prefix

        if (not validReward and
            not validCommand and
            not joining):
            return

        try:
            if joining:
                if m.user == self.chan:
                    util.LogReceived(m.type, m.user, m.message, m.tags)
                    for broadcasterJoinEvent in self.onBroadcasterJoin:
                        broadcasterJoinEvent()

                return

            if raiding:
                util.LogReceived(m.type, m.user, m.message, m.tags)
                for raidEvent in self.onRaid:
                    util.SendMessage(raidEvent(m.user))

            if validReward:
                util.LogReceived(m.type, m.user, m.message, m.tags)
                util.SendMessage(self.redeem[m.tags["custom-reward-id"]](m), m.type, m.user)

            if validCommand:
                # Retrieve first word without prefix
                m.message = m.message[1:]
                token = m.message.lower().split()[0]

                if (token in self.execute):
                    util.LogReceived(m.type, m.user, m.message, m.tags)
                    util.SendMessage(self.execute[token](m), m.type, m.user)
                    return

                # Simple response commands
                # Note that we don't get this far unless the message does not match other commands
                response = self.commands["custom"].Execute(m)
                if response != None:
                    util.SendMessage(response, m.type, m.user)
                    return

        except Exception as e:
            ptf(f"Error: {e}", time=True)

if __name__ == "__main__":
    PureBot()
