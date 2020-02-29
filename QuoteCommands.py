import re
import pymongo
import datetime

from BotRequests import GetGame
from FlushPrint import ptf, ptfDebug
from TwitchUtils import CheckPriv
import RegGroups as groups

class QuoteCommands:
    def __init__(self, chan, mongoClient):
        self.chan = chan

        quote_col_name = self.chan[1:] + "Quotes"
        self.quote_col = mongoClient.QuoteBotDB[quote_col_name]
        self.quote_col.create_index([("id", pymongo.ASCENDING)])
        ptfDebug(f"quote_col_name: {quote_col_name}")

        self.counter_col = mongoClient.QuoteBotDB['counters']
        self.counterName = self.chan[1:] + "Counter"

        self.activeCommands = {
            "quote",
        }

    def Execute(self,msg):
        ptfDebug("Beginning Quote Command")

        # snippet start
        # quote add TEXT
        # quote add Hi, I'm a PureSushi quote
        # remarks
        # Only the quote without quotation marks is required. The text will be formatted in quotation marks with the date and current game for you.
        if msg.message.startswith("quote add"):
            regmatch = re.match(f"^quote add {groups.text}$", msg.message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is: quote add TEXT"

            result = None
            result = self.counter_col.find_one_and_update(
                {"name": self.counterName},
                {'$inc': {'value':1}},
                upsert=True
            )

            if result == None:
                return f"[{msg.user}]: Unable to get new quote id from {self.counterName}"

            quoteID = result['value']

            gameName = GetGame()

            if gameName == None:
                gameName = "[Unknown Game]"

            quoteText = regmatch.group(1)
            quoteText.strip("\"")

            ptfDebug(quoteText)
            quoteObj = {
                "id": quoteID,
                "user": msg.user,
                "text": quoteText,
                "game": gameName,
                "date": datetime.datetime.now()
            }
            self.quote_col.insert_one(quoteObj)
            return f"[{msg.user}]: Your quote has been added with id {quoteID}!"

        ##############################################

        # snippet start
        # quote change ID TEXT
        # quote change 12 Hi, I'm a better PureSushi quote
        # remarks
        # Only the quote without quotation marks is required. The text will be formatted in quotation marks with the date and current game for you.
        if msg.message.startswith("quote change"):
            regmatch = re.match(f"^quote change {groups.num} {groups.text}$", msg.message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is: quote change NUMBER TEXT"

            quoteID = int(regmatch.group(1))
            newQuote = regmatch.group(2)
            newQuote.strip("\"")
            ptfDebug(newQuote)

            result = None
            result = self.quote_col.find_one({"id":quoteID})

            if result == None:
                return f"[{msg.user}]: No quote with an ID of [{quoteID}]!"
            if not CheckPriv(msg.tags):
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
        if msg.message.startswith("quote del"):
            regmatch = re.match(f"^quote del {groups.idOrLast}$", msg.message)

            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is: quote del NUMBER"

            deleteFlag = False

            result = None
            result = self.counter_col.find_one({"name": self.counterName})

            if result == None:
                ptfDebug(f"Counter not found for {self.counterName}")
                return f"[{msg.user}]: Database error. Unable to delete quote"

            lastquoteID = int(result['value']) - 1

            if regmatch.group(1) == "last":
                deleteFlag = True
                quoteID = lastquoteID
            else:
                quoteID = int(regmatch.group(1))

                if quoteID == lastquoteID:
                    deleteFlag = True

            result = None
            result = self.quote_col.find_one({"id":quoteID})

            if result == None:
                return f"[{msg.user}]: No quote with an ID of [{quoteID}]!"
            if not CheckPriv(msg.tags):
                if result['user'] != msg.user:
                    return f"[{msg.user}]: Regular users can't delete a quote someone else added!"
                if result['date'].strftime("%x") != datetime.datetime.now().strftime("%x"):
                    return f"[{msg.user}]: Regular users can't delete a quote except on the day it was added!"

            ptfDebug(f"Deleting quoteID: {quoteID}")

            if deleteFlag:
                self.quote_col.delete_one({"id":quoteID})
                self.counter_col.update_one({"name": self.counterName}, {'$inc': {'value':-1}})
            else:
                self.quote_col.delete_one({"id":quoteID})

            return f"[{msg.user}]: Deleted quote #{quoteID}!"

        ##############################################

        # snippet start
        # quote (ID)
        # quote
        # quote 123
        if msg.message.startswith("quote"):
            regmatch = re.match(f"^quote {groups.idOrLast}$", msg.message)

            quoteID = None
            if regmatch == None:
                results = self.quote_col.aggregate([{ "$sample": { "size": 1 }}])
                for item in results:
                    result = item
            else:
                if regmatch.group(1) == "last":
                    quoteID = self.counter_col.find_one({"name": self.counterName})['value'] - 1
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
