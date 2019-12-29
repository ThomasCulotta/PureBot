import re
import random
import sys
import datetime
import importlib

from TwitchWebsocket import TwitchWebsocket
import pymongo

import botconfig
import botstrings

#Function that prints then flushes standard output because sometimes things get stuck apparently
def ptf(str):
    print(str)
    sys.stdout.flush()

client = pymongo.MongoClient(f"mongodb://{botconfig.DBusername}:{botconfig.DBpassword}@{botconfig.DBhostIP}/QuoteBotDB")

class QuoteBot:
    def __init__(self):
        self.host = "irc.chat.twitch.tv"
        self.port = 6667
        self.chan = botconfig.twitchChannel
        self.nick = botconfig.twitchUser
        self.auth = botconfig.oauth

        LBcolName = self.chan[1:] + "LB"
        self.leaderboard_col = client.QuoteBotDB[LBcolName]
        self.leaderboard_col.create_index([("user", pymongo.ASCENDING)])
        ptf(LBcolName)

        QuotesColName = self.chan[1:] + "Quotes"
        self.quote_col = client.QuoteBotDB[QuotesColName]
        self.quote_col.create_index([("id", pymongo.ASCENDING)])
        ptf(QuotesColName)

        self.counter_col = client.QuoteBotDB['counters']

        # Send along all required information, and the bot will start 
        # sending messages to your callback function. (self.message_handler in this case)
        self.ws = TwitchWebsocket(host=self.host, port=self.port, chan=self.chan, nick=self.nick, auth=self.auth,
                                  callback=self.message_handler, capability=["membership", "tags", "commands"],
                                  live=True)
        self.ws.start_bot()
        # Any code after this will be executed after a KeyboardInterrupt

    def message_handler(self, m):
        # Create your bot functionality here.
        ptf(m)
        if m.message is None or m.type != "PRIVMSG":
            return

        ##############################################

        if m.message.startswith("!score"):
            tempscore = random.randint(0,100)
            ptf("tempscore: " + str(tempscore))
            result = None;
            result = self.leaderboard_col.find_one({"user": m.user})

            if result == None:
                score = tempscore
                userObj = {
                    "user": m.user,
                    "score": tempscore 
                }
                self.leaderboard_col.insert_one(userObj)
            else:
                ptf(result)
                score = result['score']

            message = f"[{m.user}] Your pure count is: {str(score)}/100"
            
            if score == 69: 
                #message += " nice :sunglasses:"
                message += " 😎"
            elif score <= 25:
                #message += " :innocent:"
                message += " 😇"
            elif score >= 75:
                #message += " :smiling_imp:"
                message += " 😈"

            self.ws.send_message(message)
            return

        ##############################################

        if m.message.startswith("!pureboard"):
            result = self.leaderboard_col.find().sort("score", 1)

            message = result[0]['user'] + ": " + str(result[0]['score'])
            result = result[1:5]
            for x in result:
                message += ", " + x['user'] + ": " + str(x['score'])

            self.ws.send_message(message)
            return

        ##############################################

        if m.message.startswith("!cursedboard"):
            result = self.leaderboard_col.find().sort("score", -1)

            message = result[0]['user'] + ": " + str(result[0]['score'])
            result = result[1:5]
            for x in result:
                message += ", " + x['user'] + ": " + str(x['score'])

            self.ws.send_message(message)
            return

        ##############################################

        if m.message.startswith("!clearboard"): 
            if m.tags['mod'] == '1' or m.user == "doomzero":
                self.leaderboard_col.remove({})
                self.ws.send_message(f"[{m.user}]: Leaderboard cleared!")
                return
            self.ws.send_message(f"[{m.user}]: That command is mods-only!")

        ##############################################

        if m.message.startswith("!clearscore"):
            if m.tags['custom-reward-id'] == "769e238b-fe80-49ba-ab89-1e7e8ad75c88":
                self.leaderboard_col.remove({"user": m.user})
                self.ws.send_message(f"[{m.user}]: Your score has been cleared!")
                return
            self.ws.send_message(f"[{m.user}]: That command requires spending Sushi Rolls on the custom reward!")

        ##############################################

        if m.message.startswith("!quoteadd "):
            regmatch = re.match("^!quoteadd (.+?)$", m.message)
            if regmatch == None:
                self.ws.send_message(f"[{m.user}]: The syntax for that command is !quoteadd \"TEXT\"")
                return
            
            counterName = self.chan[1:] + "counter"
            result = None
            result = self.counter_col.find_one_and_update(
                {"name": counterName},
                {'$inc': {'value':1}},
                upsert=True
            )
            if result == None:
                self.ws.send_message(f"[{m.user}]: Mistakes have been made. quoteID: [{quoteID}]")
                return

            quoteID = result['value']

            quoteText = regmatch.group(1)
            ptf(quoteText)
            quoteObj = {
                "id": quoteID,
                "user": m.user,
                "text": quoteText,
                "game": "[game PH]",
                "date": datetime.datetime.now()
            }
            self.quote_col.insert_one(quoteObj)
            self.ws.send_message(f"[{m.user}]: Your quote has been added with id {quoteID}!")
            return

        ##############################################

        if m.message.startswith("!quoteget "):
            regmatch = re.match("^!quoteget (\d+)$", m.message)
            if regmatch == None:
                self.ws.send_message(f"[{m.user}]: The syntax for that command is !quoteget NUMBER") 
                return
            quoteID = int(regmatch.group(1))
            result = None
            result = self.quote_col.find_one({"id":quoteID})
            if result == None:
                self.ws.send_message(f"[{m.user}]: No quote with an ID of [{quoteID}]!") 
            else:
                formattedDate = result['date'].strftime("%x")
                self.ws.send_message(f"[{quoteID}]: \"{result['text']}\" - {result['game']} on {formattedDate}")
            return

        ##############################################

        if m.message.startswith("!quotechange "):
            regmatch = re.match("^!quotechange (\d+) (.+?)$", m.message)
            if regmatch == None:
                self.ws.send_message(f"[{m.user}]: The syntax for that command is !quotechange NUMBER \"TEXT\"") 
                return
            
            quoteID = int(regmatch.group(1))
            newQuote = regmatch.group(2)
            ptf(newQuote)
            
            result = None
            result = self.quote_col.find_one({"id":quoteID})
            
            if result == None:
                self.ws.send_message(f"[{m.user}]: No quote with an ID of [{quoteID}]!") 
                return
            if m.tags['mod'] != '1':
                if result['user'] != m.user:
                    self.ws.send_message(f"[{m.user}]: Regular users can't edit a quote someone else added!") 
                    return
                if result['date'].strftime("%x") != datetime.datetime.now().strftime("%x"):
                    self.ws.send_message(f"[{m.user}]: Regular users can't edit a quote except on the day it was added!") 
                    return

            self.quote_col.update_one(
                {"id": quoteID},
                {'$set': {'text': newQuote}}
            )
            
            self.ws.send_message(f"[{m.user}]: Updated quote #{quoteID}!")
            return

        ##############################################

        if m.message.startswith("!quotedelete "):
            regmatch = re.match("^!quotedelete (\d+|last)$", m.message)
            if regmatch == None:
                self.ws.send_message(f"[{m.user}]: The syntax for that command is !quotedelete NUMBER") 
                return
            
            deleteFlag = False
            counterName = self.chan[1:] + "counter"

            result = None
            result = self.counter_col.find_one({"name": counterName})
            if result == None:
                self.ws.send_message(f"[{m.user}]: QuoteID could not be found: [{quoteID}]")
                return
            lastquoteID = int(result['value']) - 1
            
            if regmatch.group(1) == "last":
                deleteFlag = True
                quoteID = lastquoteID
            else:
                quoteID = int(regmatch.group(1))

                if quoteID == lastquoteID:
                    deleteFlag = True
            
            ptf(f"quoteID: {quoteID}")

            result = None
            result = self.quote_col.find_one({"id":quoteID})
            if result == None:
                self.ws.send_message(f"[{m.user}]: No quote with an ID of [{quoteID}]!") 
                return
            if m.tags['mod'] != '1':
                if result['user'] != m.user:
                    self.ws.send_message(f"[{m.user}]: Regular users can't delete a quote someone else added!") 
                    return
                if result['date'].strftime("%x") != datetime.datetime.now().strftime("%x"):
                    self.ws.send_message(f"[{m.user}]: Regular users can't delete a quote except on the day it was added!") 
                    return

            if deleteFlag: 
                self.quote_col.delete_one({"id":quoteID})
                self.counter_col.update_one({"name": counterName}, {'$inc': {'value':-1}})
            else: 
                self.quote_col.update_one(
                    {"id": quoteID},
                    {'$set': {'text': ""}}
                )

            self.ws.send_message(f"[{m.user}]: Deleted quote #{quoteID}!")
            return

        ##############################################

        #for the silly commands

        tokens = m.message.lower().split(" ")

        importlib.reload(botstrings)
        if tokens[0] in botstrings.commands:
            self.ws.send_message(botstrings.commands[tokens[0]])


if __name__ == "__main__":
    QuoteBot()