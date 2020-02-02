import pymongo
import datetime
import importlib
import json
import re

from TwitchWebsocket import TwitchWebsocket

# Local misc imports
import botconfig
from FlushPrint import ptf, ptfDebug

# Command imports
from WhoCommands    import WhoCommands
from PollCommands   import PollCommands
from ScoreCommands  import ScoreCommands
from QuoteCommands  import QuoteCommands
from CustomCommands import CustomCommands
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

        # TODO: remove ws param from constructors
        self.commands = {
            "who"   : WhoCommands(chan=self.chan, mongoClient=client),
            "poll"  : PollCommands(chan=self.chan, socket=self.ws),
            "score" : ScoreCommands(chan=self.chan, mongoClient=client),
            "quote" : QuoteCommands(chan=self.chan, mongoClient=client),
            "custom" : CustomCommands(),
            "shoutout" : ShoutoutCommands(),
        }

        # Defines all command strings caught by imported command modules
        # TODO: is there a cleaner way to define duplicate values (e.g. "score")
        self.execute = {
            "who" : self.commands["who"].Execute,
            "poll" : self.commands["poll"].Execute,
            "vote" : self.commands["poll"].Execute,
            "quote" : self.commands["quote"].Execute,
            "purecount"  : self.commands["score"].Execute,
            "pureboard"  : self.commands["score"].Execute,
            "curseboard" : self.commands["score"].Execute,
            "clearboard" : self.commands["score"].Execute,
            "clearscore" : self.commands["score"].Execute,
            "swapscore"  : self.commands["score"].Execute,
            "stealscore" : self.commands["score"].Execute,
            "addcommand" : self.commands["custom"].Execute,
            "delcommand" : self.commands["custom"].Execute,
            "shoutout"   : self.commands["shoutout"].Execute,
        }

        ptf("Bot Started!")

        self.ws.start_bot()
        # Any code after this will be executed after a KeyboardInterrupt

    def SendMessage(self, type, user, response):
        timestamp = datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S')

        if response == None:
            ptf(f"{timestamp} | Response \"None\" of type [{type}] was NOT sent to [{user}]: {response}\n")
            return

        if (type == "PRIVMSG"):
            self.ws.send_message(response)
        elif (type == "WHISPER"):
            self.ws.send_whisper(user, response)

        ptf(f"{timestamp} | Sent [{type}] to [{user}]: {response}\n")
        return

    def message_handler(self, m):
        # Check for valid message with prefix
        # TODO: add ability for multiple prefixes
        if (m.message is None or
           (m.type != "PRIVMSG" and m.type != "WHISPER") or
           (not m.message.startswith(self.prefix))):
            return

        try:
            # Retrieve first word without prefix
            m.message = m.message[1:]
            token = m.message.lower().split(" ")[0]

            if (token in self.execute):
                # TODO: make this repeated log cleaner
                ptf(f"{datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S')} | Received [{m.type}] from [{m.user}]: {m.message}")
                ptf(f"With tags: {m.tags}")
                self.SendMessage(m.type, m.user, self.execute[token](m))
                return

            ##############################################

            # Simple response commands
            # Note that we don't get this far unless the message does not match other commands

            response = self.commands["custom"].Execute(m)
            if response != None:
                self.SendMessage(m.type, m.user, response)
            return

        except Exception as e:
            ptf(f"Error: {e}")

if __name__ == "__main__":
    PureBot()
