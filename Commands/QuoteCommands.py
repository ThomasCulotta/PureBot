import re
import pymongo
import datetime

from Utilities.BotRequests import GetGame
from Utilities.FlushPrint import ptf
import Utilities.TwitchUtils as util
import Utilities.RegGroups as groups

class QuoteCommands:
    def __init__(self, chan, mongoClient):
        self.colQuotes = mongoClient.QuoteBotDB[chan + "Quotes"]
        self.colQuotes.create_index([("id", pymongo.ASCENDING)])

        self.colCounters = mongoClient.QuoteBotDB["counters"]
        self.counterName = chan + "Counter"

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

    def CheckModifyQuote(action, result):
        if not util.CheckPrivMod(msg.tags):
            if result["user"] != msg.user:
                result.append(f"[{msg.user}]: Only mods can {action} a quote someone else added")

            if result["date"].strftime("%x") != datetime.datetime.now().strftime("%x"):
                return f"[{msg.user}]: Only mods can {action} a quote on a different day than it was added"

        return None

    # snippet start
    # quote (ID/TEXT)
    # quote
    # quote 123
    # quote hello
    # remarks
    # When "quote TEXT" is used, a random quote with the given text in it is returned.
    def ExecuteQuote(self, msg):
        try:
            subCommand = msg.message.lower().split()[1]
        except IndexError:
            subCommand = None

        if subCommand in self.quoteSubCommands:
            return self.quoteSubCommands[subCommand](msg)

        # Get the first valid match from whoRegex list
        result = None
        quoteId = None

        if (regMatch := next((exp.match(msg.message) for exp in self.quoteRegex if exp.match(msg.message) != None), None)) is None:
            results = self.colQuotes.aggregate([{ "$sample" : { "size" : 1 } }])
            for item in results:
                result = item
        else:
            try:
                quoteArg = regMatch.group("idOrLast")
            except IndexError:
                quoteArg = None

            if quoteArg != None:
                latestId = self.colCounters.find_one({ "name" : self.counterName })["value"] - 1
                if quoteArg.isnumeric():
                    # Clamp id between 1 and latestId
                    quoteId = max(min(int(quoteArg), latestId), 1)
                else:
                    quoteId = latestId

                if quoteId:
                    result = self.colQuotes.find_one({ "id" : quoteId })
            else:
                quoteArg = regMatch.group("text")

                results = self.colQuotes.aggregate([
                    { "$match" : { "text" : {
                                        "$regex" : quoteArg,
                                        "$options" : "i"
                                    } } },
                    { "$sample" : { "size" : 1 } }])

                for item in results:
                    result = item

        if result == None:
            if quoteId == None:
                return f"[{msg.user}]: No quotes found"

            return f"[{msg.user}]: No quote {quoteId}"
        else:
            quoteDate = result["date"].strftime("%x")
            return f"[{result['id']}]: \"{result['text']}\" - {result['game']} on {quoteDate}"

    # snippet start
    # quote add TEXT
    # quote add Hi, I'm a PureSushi quote
    # remarks
    # Only the quote without quotation marks is required. The text will be formatted in quotation marks with the date and current game for you.
    def ExecuteQuoteAdd(self, msg):
        if not util.CheckPrivSub(msg.tags):
            return f"[{msg.user}]: Only mods and subs can add a quote"

        if (regMatch := self.quoteAddRegex.match(msg.message)) is None:
            return util.GetSyntax(msg.user, "quote add TEXT")

        result = self.colCounters.find_one_and_update(
            { "name" : self.counterName },
            { "$inc" : { "value" : 1 } },
            upsert=True
        )

        if result == None:
            ptf(f"Counter not found for {self.counterName}")
            return f"[{msg.user}]: Unable to add quote"

        quoteId = result["value"]

        if (gameName := GetGame()) is None:
            gameName = "[Unknown Game]"

        quoteText = regMatch.group("text")
        quoteText.strip("\"'")

        self.colQuotes.insert_one({
            "id" : quoteId,
            "user" : msg.user,
            "text" : quoteText,
            "game" : gameName,
            "date" : datetime.datetime.now()
        })

        return f"[{msg.user}]: Added quote {quoteId}"

    # snippet start
    # quote del ID
    # quote del 123
    # quote del last
    def ExecuteQuoteDel(self, msg):
        if (regMatch := self.quoteDelRegex.match(msg.message)) is None:
            return util.GetSyntax(msg.user, "quote del NUMBER")

        if (result := self.colCounters.find_one({ "name" : self.counterName })) is None:
            ptf(f"Counter not found for {self.counterName}")
            return f"[{msg.user}]: Unable to delete quote"

        latestId = int(result["value"]) - 1
        quoteId = latestId

        deleting = False
        quoteIdOrLast = regMatch.group("idOrLast")

        if quoteIdOrLast.lower() == "last":
            deleting = True
        else:
            quoteId = int(quoteIdOrLast)

            if quoteId == latestId:
                deleting = True

        if (result := self.colQuotes.find_one({ "id" : quoteId })) is None:
            return f"[{msg.user}]: No quote {quoteId}"

        if (checkResult := CheckModifyQuote("delete")):
            return checkResult

        self.colQuotes.delete_one({ "id" : quoteId })

        if deleting:
            self.colCounters.update_one({ "name" : self.counterName }, { "$inc" : { "value" : -1 } })

        return f"[{msg.user}]: Deleted quote {quoteId}"

    # snippet start
    # quote change ID TEXT
    # quote change 12 Hi, I'm a better PureSushi quote
    # remarks
    # Only the quote without quotation marks is required. The text will be formatted in quotation marks with the date and current game for you.
    def ExecuteQuoteChange(self, msg):
        if (regMatch := self.quoteChangeRegex.match(msg.message)) is None:
            return util.GetSyntax(msg.user, "quote change NUMBER TEXT")

        quoteId = int(regMatch.group("num0"))
        newQuote = regMatch.group("text")
        newQuote.strip("\"'")

        if (result := self.colQuotes.find_one({ "id" : quoteId })) is None:
            return f"[{msg.user}]: No quote {quoteId}"

        if (checkResult := CheckModifyQuote("edit")):
            return checkResult

        self.colQuotes.update_one(
            { "id" : quoteId },
            { "$set" : { "text" : newQuote } }
        )

        return f"[{msg.user}]: Updated quote {quoteId}"
