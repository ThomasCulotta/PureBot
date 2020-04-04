import re
import pymongo
import datetime

from Utilities.BotRequests import GetGame
from Utilities.FlushPrint import ptf, ptfDebug
import Utilities.TwitchUtils as util
import Utilities.RegGroups as groups

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
            "quote" : self.ExecuteQuote,
        }

        self.quoteSubCommands = {
            "add" : self.ExecuteQuoteAdd,
            "del" : self.ExecuteQuoteDel,
            "change" : self.ExecuteQuoteChange,
        }

        self.quoteRegex = [
            re.compile(f"^quote {groups.idOrLast}"),
            re.compile(f"^quote {groups.text}$"),
        ]

        self.quoteAddRegex = re.compile(f"^quote add {groups.text}$")
        self.quoteDelRegex = re.compile(f"^quote del {groups.idOrLast}")
        self.quoteChangeRegex = re.compile(f"^quote change {groups.num} {groups.text}$")

    # snippet start
    # quote (ID/TEXT)
    # quote
    # quote 123
    # quote hello
    # remarks
    # When "quote TEXT" is used, a random quote with the given text in it is returned.
    def ExecuteQuote(self, msg):
        ptfDebug("Beginning Quote Command")
        try:
            subCommand = msg.message.lower().split()[1]
        except IndexError:
            subCommand = None

        if subCommand in self.quoteSubCommands:
            return self.quoteSubCommands[subCommand](msg)

        # Get the first valid match from whoRegex list
        regmatch = next((exp.match(msg.message) for exp in self.quoteRegex if exp.match(msg.message) != None), None)

        result = None
        quoteID = None
        if regmatch == None:
            results = self.quote_col.aggregate([{ "$sample": { "size": 1 }}])
            for item in results:
                result = item
        else:
            try:
                quoteArg = regmatch.group("idOrLast")
            except IndexError:
                quoteArg = None

            if quoteArg != None:
                if quoteArg.isnumeric():
                    quoteID = int(quoteArg)
                else:
                    quoteID = self.counter_col.find_one({"name": self.counterName})['value'] - 1

                if quoteID:
                    result = self.quote_col.find_one({"id":quoteID})
            else:
                quoteArg = regmatch.group("text")

                results = self.quote_col.aggregate([
                    {"$match" : {"text" : {"$regex" : quoteArg, "$options" : "i"}}},
                    {"$sample" : {"size" : 1}}])

                for item in results:
                    result = item

        if result == None:
            if quoteID == None:
                return f"[{msg.user}]: No quotes found"

            return f"[{msg.user}]: No quote with an ID of [{quoteID}]!"
        else:
            formattedDate = result['date'].strftime("%x")
            quoteID = result['id']
            return f"[{quoteID}]: \"{result['text']}\" - {result['game']} on {formattedDate}"

    # snippet start
    # quote add TEXT
    # quote add Hi, I'm a PureSushi quote
    # remarks
    # Only the quote without quotation marks is required. The text will be formatted in quotation marks with the date and current game for you.
    def ExecuteQuoteAdd(self, msg):
        regmatch = self.quoteAddRegex.match(msg.message)

        if regmatch == None:
            return f"[{msg.user}]: The syntax for that command is: quote add TEXT"

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

        quoteText = regmatch.group("text")
        quoteText.strip("\"'")

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

    # snippet start
    # quote del ID
    # quote del 123
    # quote del last
    def ExecuteQuoteDel(self, msg):
        regmatch = self.quoteDelRegex.match(msg.message)

        if regmatch == None:
            return f"[{msg.user}]: The syntax for that command is: quote del NUMBER"

        deleteFlag = False

        result = self.counter_col.find_one({"name": self.counterName})

        if result == None:
            ptfDebug(f"Counter not found for {self.counterName}")
            return f"[{msg.user}]: Database error. Unable to delete quote"

        lastquoteID = int(result['value']) - 1

        quoteIdOrLast = regmatch.group("idOrLast")
        if quoteIdOrLast.lower() == "last":
            deleteFlag = True
            quoteID = lastquoteID
        else:
            quoteID = int(quoteIdOrLast)

            if quoteID == lastquoteID:
                deleteFlag = True

        result = self.quote_col.find_one({"id":quoteID})

        if result == None:
            return f"[{msg.user}]: No quote with an ID of [{quoteID}]!"

        if not util.CheckPriv(msg.tags):
            if result['user'] != msg.user:
                return f"[{msg.user}]: Regular users can't delete a quote someone else added!"

            if result['date'].strftime("%x") != datetime.datetime.now().strftime("%x"):
                return f"[{msg.user}]: Regular users can't delete a quote except on the day it was added!"

        ptfDebug(f"Deleting quoteID: {quoteID}")

        self.quote_col.delete_one({"id":quoteID})

        if deleteFlag:
            self.counter_col.update_one({"name": self.counterName}, {'$inc': {'value':-1}})

        return f"[{msg.user}]: Deleted quote #{quoteID}!"

    # snippet start
    # quote change ID TEXT
    # quote change 12 Hi, I'm a better PureSushi quote
    # remarks
    # Only the quote without quotation marks is required. The text will be formatted in quotation marks with the date and current game for you.
    def ExecuteQuoteChange(self, msg):
        regmatch = self.quoteChangeRegex.match(msg.message)

        if regmatch == None:
            return f"[{msg.user}]: The syntax for that command is: quote change NUMBER TEXT"

        quoteID = int(regmatch.group("num0"))
        newQuote = regmatch.group("text")
        newQuote.strip("\"'")
        ptfDebug(newQuote)

        result = self.quote_col.find_one({"id":quoteID})

        if result == None:
            return f"[{msg.user}]: No quote with an ID of [{quoteID}]!"

        if not util.CheckPriv(msg.tags):
            if result['user'] != msg.user:
                return f"[{msg.user}]: Regular users can't edit a quote someone else added!"

            if result['date'].strftime("%x") != datetime.datetime.now().strftime("%x"):
                return f"[{msg.user}]: Regular users can't edit a quote except on the day it was added!"

        self.quote_col.update_one(
            {"id": quoteID},
            {'$set': {'text': newQuote}}
        )

        return f"[{msg.user}]: Updated quote #{quoteID}!"
