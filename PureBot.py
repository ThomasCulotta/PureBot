import pymongo
import datetime
import importlib
import json
import re

from TwitchWebsocket import TwitchWebsocket

# Local misc imports
import botconfig
from FlushPrint import ptf

# Command imports
from WhoCommands   import WhoCommands
from ScoreCommands import ScoreCommands
from QuoteCommands import QuoteCommands
from CustomCommands import CustomCommands

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

        # TODO: remove ws param from constructors
        self.commands =
        {
            "who"   : WhoCommands(chan=self.chan, mongoClient=client),
            "score" : ScoreCommands(chan=self.chan, ws=self.ws, mongoClient=client),
            "quote" : QuoteCommands(chan=self.chan, ws=self.ws, mongoClient=client),
            "custom" : CustomCommands(prefix=self.prefix, ws=self.ws),
        }

        # Defines all command strings caught by imported command modules
        # TODO: is there a cleaner way to define duplicate values (e.g. "score")
        self.execute =
        {
            "who" : self.commands["who"].Execute,
            "quote" : self.commands["quote"].Execute,
            "purecount"  : self.commands["score"].Execute,
            "pureboard"  : self.commands["score"].Execute,
            "curseboard" : self.commands["score"].Execute,
            "clearboard" : self.commands["score"].Execute,
            "clearscore" : self.commands["score"].Execute,
            "addcommand" : self.commands["custom"].Execute,
            "delcommand" : self.commands["custom"].Execute,
        }

        self.customCommands = CustomCommands(prefix=self.prefix,
                                             ws=self.ws)

        self.ws.start_bot()
        # Any code after this will be executed after a KeyboardInterrupt

    def SendMessage(self, type, user, response):
        if (type == "PRIVMSG"):
            self.ws.send_message(response)
        elif (type == "WHISPER")
            self.ws.send_whisper(m.user, response)
        else
            ptf("Failed to send message")
        return

    def message_handler(self, m):
        # Create your bot functionality here.
        ptf(m)

        if m.message is None or
           (m.type != "PRIVMSG" and m.type != "WHISPER") or
           (not m.message.startswith(self.prefix)):
            return

        try:
            # Retrieve first word without prefix
            token = m.message.lower().split(" ")[0][1:]

            if (token in self.execute)
                SendMessage(m.type, m.user, self.execute[token](m))
                return

            ##############################################

            # Simple response commands
            # Note that we don't get this far unless the message does not match other commands

            if m.message.startswith(self.prefix):
                response = self.customCommands.Execute(m)

                self.send(m.type, m.user, response)
                return

        except Exception as e:
            ptf(f"Error: {e}")

if __name__ == "__main__":
    PureBot()
