import pymongo
import datetime
import importlib

from TwitchWebsocket import TwitchWebsocket

# Local misc imports
import botconfig
import botstrings
from FlushPrint import ptf

# Command imports
from QuoteCommands import QuoteCommands
from ScoreCommands import ScoreCommands

client = pymongo.MongoClient(f"mongodb://{botconfig.DBusername}:{botconfig.DBpassword}@{botconfig.DBhostIP}/QuoteBotDB")

class PureBot:
    def __init__(self):
        self.host = "irc.chat.twitch.tv"
        self.port = 6667
        self.chan = botconfig.twitchChannel
        self.nick = botconfig.twitchUser
        self.auth = botconfig.oauth

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

        self.scoreCommands = ScoreCommands(chan=self.chan[1:],
                                           ws=self.ws,
                                           mongoClient=client)

        self.quoteCommands = QuoteCommands(chan=self.chan[1:],
                                           ws=self.ws,
                                           mongoClient=client)

        self.ws.start_bot()
        # Any code after this will be executed after a KeyboardInterrupt

    def message_handler(self, m):
        # Create your bot functionality here.
        ptf(m)
        if m.message is None or m.type != "PRIVMSG":
            return

        ##############################################

        if (m.message.startswith("!score") or
            m.message.startswith("!pureboard") or
            m.message.startswith("!cursedboard") or
            m.message.startswith("!clearboard") or
            m.message.startswith("!clearscore")):

            self.scoreCommands.Execute(m)
            return

        ##############################################

        if m.message.startswith("!quote"):
            self.quoteCommands.Execute(m)
            return

        ##############################################

        # Simple response commands

        tokens = m.message.lower().split(" ")

        importlib.reload(botstrings)
        if tokens[0] in botstrings.commands:
            self.ws.send_message(botstrings.commands[tokens[0]])


if __name__ == "__main__":
    PureBot()
