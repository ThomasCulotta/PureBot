import re
import pymongo
import datetime

from TwitchWebsocket import TwitchWebsocket

from FlushPrint import ptf

class QuoteCommands():
    def __init__(self, chan, ws, mongoClient):
        self.ws = ws
        self.chan = chan

        QuotesColName = self.chan[1:] + "Quotes"
        self.quote_col = mongoClient.QuoteBotDB[QuotesColName]
        self.quote_col.create_index([("id", pymongo.ASCENDING)])
        ptf(QuotesColName)

        self.counter_col = mongoClient.QuoteBotDB['counters']

    def Execute(msg):
        if msg.message.startswith("!quoteadd "):
            regmatch = re.match("^!quoteadd (.+?)$", msg.message)
            if regmatch == None:
                self.ws.send_message(f"[{msg.user}]: The syntax for that command is !quoteadd \"TEXT\"")
                return

            counterName = self.chan[1:] + "counter"
            result = None
            result = self.counter_col.find_one_and_update(
                {"name": counterName},
                {'$inc': {'value':1}},
                upsert=True
            )
            if result == None:
                self.ws.send_message(f"[{msg.user}]: Mistakes have been made. quoteID: [{quoteID}]")
                return

            quoteID = result['value']

            quoteText = regmatch.group(1)
            ptf(quoteText)
            quoteObj = {
                "id": quoteID,
                "user": msg.user,
                "text": quoteText,
                "game": "[game PH]",
                "date": datetime.datetime.now()
            }
            self.quote_col.insert_one(quoteObj)
            self.ws.send_message(f"[{msg.user}]: Your quote has been added with id {quoteID}!")
            return

        ##############################################

        if msg.message.startswith("!quoteget "):
            regmatch = re.match("^!quoteget (\d+)$", msg.message)
            if regmatch == None:
                self.ws.send_message(f"[{msg.user}]: The syntax for that command is !quoteget NUMBER")
                return
            quoteID = int(regmatch.group(1))
            result = None
            result = self.quote_col.find_one({"id":quoteID})
            if result == None:
                self.ws.send_message(f"[{msg.user}]: No quote with an ID of [{quoteID}]!")
            else:
                formattedDate = result['date'].strftime("%x")
                self.ws.send_message(f"[{quoteID}]: \"{result['text']}\" - {result['game']} on {formattedDate}")
            return

        ##############################################

        if msg.message.startswith("!quotechange "):
            regmatch = re.match("^!quotechange (\d+) (.+?)$", msg.message)
            if regmatch == None:
                self.ws.send_message(f"[{msg.user}]: The syntax for that command is !quotechange NUMBER \"TEXT\"")
                return

            quoteID = int(regmatch.group(1))
            newQuote = regmatch.group(2)
            ptf(newQuote)

            result = None
            result = self.quote_col.find_one({"id":quoteID})

            if result == None:
                self.ws.send_message(f"[{msg.user}]: No quote with an ID of [{quoteID}]!")
                return
            if msg.tags['mod'] != '1':
                if result['user'] != msg.user:
                    self.ws.send_message(f"[{msg.user}]: Regular users can't edit a quote someone else added!")
                    return
                if result['date'].strftime("%x") != datetime.datetime.now().strftime("%x"):
                    self.ws.send_message(f"[{msg.user}]: Regular users can't edit a quote except on the day it was added!")
                    return

            self.quote_col.update_one(
                {"id": quoteID},
                {'$set': {'text': newQuote}}
            )

            self.ws.send_message(f"[{msg.user}]: Updated quote #{quoteID}!")
            return

        ##############################################

        if msg.message.startswith("!quotedelete "):
            regmatch = re.match("^!quotedelete (\d+|last)$", msg.message)
            if regmatch == None:
                self.ws.send_message(f"[{msg.user}]: The syntax for that command is !quotedelete NUMBER")
                return

            deleteFlag = False
            counterName = self.chan[1:] + "counter"

            result = None
            result = self.counter_col.find_one({"name": counterName})
            if result == None:
                self.ws.send_message(f"[{msg.user}]: QuoteID could not be found: [{quoteID}]")
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
                self.ws.send_message(f"[{msg.user}]: No quote with an ID of [{quoteID}]!")
                return
            if msg.tags['mod'] != '1':
                if result['user'] != msg.user:
                    self.ws.send_message(f"[{msg.user}]: Regular users can't delete a quote someone else added!")
                    return
                if result['date'].strftime("%x") != datetime.datetime.now().strftime("%x"):
                    self.ws.send_message(f"[{msg.user}]: Regular users can't delete a quote except on the day it was added!")
                    return

            if deleteFlag:
                self.quote_col.delete_one({"id":quoteID})
                self.counter_col.update_one({"name": counterName}, {'$inc': {'value':-1}})
            else:
                self.quote_col.update_one(
                    {"id": quoteID},
                    {'$set': {'text': ""}}
                )

            self.ws.send_message(f"[{msg.user}]: Deleted quote #{quoteID}!")
            return
