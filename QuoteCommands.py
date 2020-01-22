import re
import pymongo
import datetime

from TwitchWebsocket import TwitchWebsocket

from FlushPrint import ptf

class QuoteCommands:
    def __init__(self, chan, mongoClient):
        self.chan = chan

        quote_col_name = self.chan[1:] + "Quotes"
        self.quote_col = mongoClient.QuoteBotDB[quote_col_name]
        self.quote_col.create_index([("id", pymongo.ASCENDING)])
        ptf(quote_col_name)

        self.counter_col = mongoClient.QuoteBotDB['counters']

    def Execute(self,msg):
        ptf("Beginning Quote Command")
        message = msg.message[1:]

        # snippet start
        # quote add TEXT
        # quote add Hi, I'm a PureSushi quote
        if message.startswith("quote add"):
            regmatch = re.match("^quote add (.+?)$", message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is: quote add TEXT"

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

        # snippet start
        # quote change ID TEXT
        # quote change 12 Hi, I'm a better PureSushi quote
        if message.startswith("quote change"):
            regmatch = re.match("^quote change (\d+) (.+?)$", message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is: quote change NUMBER TEXT"

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

        # snippet start
        # quote del ID
        # quote del 123
        # quote del last
        if message.startswith("quote del"):
            ptf("Deleting quote")
            regmatch = re.match("^quote del (\d+?|last)$", message)

            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is: quote del NUMBER"

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

            ptf(f"Deleting quoteID: {quoteID}")

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
                self.quote_col.delete_one({"id":quoteID})

            return f"[{msg.user}]: Deleted quote #{quoteID}!"

        ##############################################

        # snippet start
        # quote (ID)
        # quote
        # quote 123
        if message.startswith("quote"):
            regmatch = re.match("^quote (\d+)$", message)

            quoteID = None
            if regmatch == None:
                results = self.quote_col.aggregate([{ "$sample": { "size": 1 }}])
                for item in results:
                    result = item
            else:
                quoteID = int(regmatch.group(1))
                result = self.quote_col.find_one({"id":quoteID})

            if result == None:
                if quoteID == None:
                    return f"[{msg.user}]: No quotes found"

                return f"[{msg.user}]: No quote with an ID of [{quoteID}]!"
            else:
                formattedDate = result['date'].strftime("%x")
                quoteID = result['id']
                return f"[{quoteID}]: \"{result['text']}\" - {result['game']} on {formattedDate}"
