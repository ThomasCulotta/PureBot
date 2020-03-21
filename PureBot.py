import pymongo

from TwitchWebsocket import TwitchWebsocket

# Local misc imports
import botconfig
from FlushPrint import ptf, ptfDebug
from TwitchUtils import *

# Command imports
from WhoCommands    import WhoCommands
from PollCommands   import PollCommands
from DiceCommands   import DiceCommands
from TimeCommands   import TimeCommands
from ScoreCommands  import ScoreCommands
from QuoteCommands  import QuoteCommands
from CustomCommands import CustomCommands
from VoteBanCommands import VoteBanCommands
from ShoutoutCommands import ShoutoutCommands

client = pymongo.MongoClient(f"mongodb://{botconfig.DBusername}:{botconfig.DBpassword}@{botconfig.DBhostIP}/QuoteBotDB")

class PureBot:
    def __init__(self):
        self.host = "irc.chat.twitch.tv"
        self.port = 6667
        self.chan = botconfig.twitchChannel
        self.nick = botconfig.twitchUser
        self.auth = botconfig.oauth

        self.prefix = botconfig.prefix

        # Send along all required information, and the bot will start
        # sending messages to your callback function. (self.message_handler in this case)
        self.ws = TwitchWebsocket(host=self.host,
                                  port=self.port,
                                  chan=self.chan,
                                  nick=self.nick,
                                  auth=self.auth,
                                  callback=self.message_handler,
                                  capability=["membership", "tags", "commands"],
                                  live=True)

        InitializeUtils(self.ws)

        self.commands = {
            "who"   : WhoCommands(chan=self.chan, mongoClient=client),
            "poll"  : PollCommands(chan=self.chan),
            "score" : ScoreCommands(chan=self.chan, mongoClient=client),
            "quote" : QuoteCommands(chan=self.chan, mongoClient=client),
            "dice"  : DiceCommands(),
            "time"  : TimeCommands(),
            "custom" : CustomCommands(),
            "voteban" : VoteBanCommands(),
            "shoutout" : ShoutoutCommands(),
        }

        # Maps all active command strings caught by imported command modules to their respective Execute function
        self.execute = {}

        for cmd in self.commands.values():
            if hasattr(cmd, "activeCommands"):
                for activeCommand in cmd.activeCommands:
                    self.execute[activeCommand] = cmd.Execute

        ptf("Bot Started!")

        self.ws.start_bot()
        # Any code after this will be executed after a KeyboardInterrupt

    def message_handler(self, m):
        # Check for valid message with prefix
        if (m.message is None or
           (m.type != "PRIVMSG" and m.type != "WHISPER") or
           (not m.message.startswith(self.prefix))):
            return

        try:
            # Retrieve first word without prefix
            m.message = m.message[1:]
            token = m.message.lower().split(" ")[0]

            if (token in self.execute):
                LogReceived(m.type, m.user, m.message, m.tags)
                SendMessage(self.execute[token](m), m.type, m.user)
                return

            ##############################################

            # Simple response commands
            # Note that we don't get this far unless the message does not match other commands

            response = self.commands["custom"].Execute(m)
            if response != None:
                SendMessage(response, m.type, m.user)
                return

        except Exception as e:
            ptf(f"Error: {e}", time=True)

if __name__ == "__main__":
    PureBot()
