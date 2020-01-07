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

        self.scoreCommands = ScoreCommands(chan=self.chan,
                                           ws=self.ws,
                                           mongoClient=client)

        self.quoteCommands = QuoteCommands(chan=self.chan,
                                           ws=self.ws,
                                           mongoClient=client)

        self.customCommands = CustomCommands(prefix=self.prefix, 
                                             ws=self.ws)

        self.ws.start_bot()
        # Any code after this will be executed after a KeyboardInterrupt


    def message_handler(self, m):
        # Create your bot functionality here.
        ptf(m)
        if m.message is None or (m.type != "PRIVMSG" and m.type != "WHISPER"):
            return

        ##############################################
        try: 
            if (m.message.startswith("!lewdcount") or 
                m.message.startswith("~lewdcount")):

                response = f"[{m.user}]: That command is fake! Please use !score instead!"

                self.ws.send_message(response)
                return

            ##############################################

            #ignore messages that don't start with the bot's prefix
            if (not m.message.startswith(self.prefix)):
                return

            ##############################################

            if (m.message.startswith(self.prefix + "score") or
                m.message.startswith(self.prefix + "pureboard") or
                m.message.startswith(self.prefix + "cursedboard") or
                m.message.startswith(self.prefix + "clearboard") or
                m.message.startswith(self.prefix + "clearscore")):

                response = self.scoreCommands.Execute(m)

                self.send(m.type, m.user, response)
                return

            ##############################################

            if m.message.startswith(self.prefix + "quote"):
                
                response = self.quoteCommands.Execute(m)

                self.send(m.type, m.user, response)
                return

            ##############################################

            if (m.message.startswith(self.prefix + "addcommand ") or
                m.message.startswith(self.prefix + "delcommand ")):

                response = self.customCommands.Execute(m)                

                self.send(m.type, m.user, response)
                return

            ##############################################

            # Simple response commands 
            # Note that we don't get this far unless the message does not match other commands

            if m.message.startswith(self.prefix):
                tokens = m.message.lower().split(" ")

                response = self.customCommands.Execute(m)
                
                self.send(m.type, m.user, response)
                return

            ##############################################

            #Code written after this point will execute upon every message sent to the channel, including non-command messages 
            
            #this one might be excessive, so keep it commented out when the channel's active
            #ptf("No command recognized!")


        except Exception as e:
            ptf(f"Error: {e}")

    ##############################################

    def send(self, mType, user, response):
        ptf("in send")
        if (mType == "PRIVMSG"):
            self.ws.send_message(response)
            ptf("after message")
            return
        if (mType == "WHISPER"):
            #self.ws.send_message(f"/w {m.user} {response}")
            self.ws.send_whisper(m.user, response)
            ptf("after whisper")
            return
        ptf("Failed to send!")

    ##############################################

if __name__ == "__main__":
    PureBot()
