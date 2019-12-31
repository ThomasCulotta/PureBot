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

    def Execute(self,msg):

        ##############################################
        
        if msg.message.startswith("!quoteadd "):
            regmatch = re.match("^!quoteadd (.+?)$", msg.message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is !quoteadd TEXT"

            counterName = self.chan[1:] + "Counter"
            result = None
            result = self.counter_col.find_one_and_update(
                {"name": counterName},
                {'$inc': {'value':1}},
                upsert=True
            )
            if result == None:
                return f"[{msg.user}]: Mistakes have been made. quoteID: [{quoteID}]"

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
            return f"[{msg.user}]: Your quote has been added with id {quoteID}!"

        ##############################################

        if msg.message.startswith("!quoteget "):
            regmatch = re.match("^!quoteget (\d+)$", msg.message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is !quoteget NUMBER"
            quoteID = int(regmatch.group(1))
            result = None
            result = self.quote_col.find_one({"id":quoteID})
            if result == None:
                return f"[{msg.user}]: No quote with an ID of [{quoteID}]!"
            else:
                formattedDate = result['date'].strftime("%x")
                return f"[{quoteID}]: \"{result['text']}\" - {result['game']} on {formattedDate}"

        ##############################################

        if msg.message.startswith("!quotechange "):
            regmatch = re.match("^!quotechange (\d+) (.+?)$", msg.message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is !quotechange NUMBER TEXT"

            quoteID = int(regmatch.group(1))
            newQuote = regmatch.group(2)
            ptf(newQuote)

            result = None
            result = self.quote_col.find_one({"id":quoteID})

            if result == None:
                return f"[{msg.user}]: No quote with an ID of [{quoteID}]!"
            if msg.tags['mod'] != '1':
                if result['user'] != msg.user:
                    return f"[{msg.user}]: Regular users can't edit a quote someone else added!"
                if result['date'].strftime("%x") != datetime.datetime.now().strftime("%x"):
                    return f"[{msg.user}]: Regular users can't edit a quote except on the day it was added!"

            self.quote_col.update_one(
                {"id": quoteID},
                {'$set': {'text': newQuote}}
            )

            return f"[{msg.user}]: Updated quote #{quoteID}!"

        ##############################################

        if msg.message.startswith("!quotedelete "):
            regmatch = re.match("^!quotedelete (\d+|last)$", msg.message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is !quotedelete NUMBER"

            deleteFlag = False
            counterName = self.chan[1:] + "counter"

            result = None
            result = self.counter_col.find_one({"name": counterName})
            if result == None:
                return f"[{msg.user}]: QuoteID could not be found: [{quoteID}]"
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
                return f"[{msg.user}]: No quote with an ID of [{quoteID}]!"
            if msg.tags['mod'] != '1':
                if result['user'] != msg.user:
                    return f"[{msg.user}]: Regular users can't delete a quote someone else added!"
                if result['date'].strftime("%x") != datetime.datetime.now().strftime("%x"):
                    return f"[{msg.user}]: Regular users can't delete a quote except on the day it was added!"

            if deleteFlag:
                self.quote_col.delete_one({"id":quoteID})
                self.counter_col.update_one({"name": counterName}, {'$inc': {'value':-1}})
            else:
                self.quote_col.update_one(
                    {"id": quoteID},
                    {'$set': {'text': ""}}
                )

            return f"[{msg.user}]: Deleted quote #{quoteID}!"
