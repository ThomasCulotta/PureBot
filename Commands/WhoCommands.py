import re
import json
import random
import pymongo

from Utilities.FlushPrint import ptf
from Utilities.BotRequests import GetUserId
import Utilities.TwitchUtils as util
import Utilities.RegGroups as groups

class WhoCommands():
    def __init__(self, chan, mongoClient):
        colNameWho = chan + "Who"
        self.colWho = mongoClient.QuoteBotDB[colNameWho]
        self.colWho.create_index([("user", pymongo.ASCENDING)])

        self.activeCommands = {
            # snippet start
            # who (USER) (ID)
            # who
            # who 14
            # who @BabotzInc
            # who BabotzInc 14
            # remarks
            # When no username is given, this command defaults to your own quotes.
            "who" : self.ExecuteWho,
        }

        self.whoSubCommands = {
            # snippet start
            # who add USER TEXT
            # who add @BabotzInc Hello I'm a Babotz quote
            # remarks
            # Mod Only. @ing the user is recommended. Type @ and use Twitch's username picker/autocomplete to help ensure the correct username is given.
            "add" : self.ExecuteWhoAdd,

            # snippet start
            # who del USER ID
            # who del @BabotzInc 12
            # remarks
            # Mod Only. @ing the user is recommended. Type @ and use Twitch's username picker/autocomplete to help ensure the correct username is given.
            "del" : self.ExecuteWhoDel,
        }

        # Ordered list of patterns to match against for who command
        self.whoRegex = [
            re.compile(f"^who {groups.user} {groups.num}"),
            re.compile(f"^who {groups.num}"),
            re.compile(f"^who {groups.user}"),
        ]

        self.whoAddRegex = re.compile(f"^who add {groups.user} {groups.text}$")
        self.whoDelRegex = re.compile(f"^who del {groups.user} {groups.idOrLast}")

    def ExecuteWho(self, msg):
        try:
            subCommand = msg.message.lower().split()[1]
        except IndexError:
            subCommand = None

        if subCommand in self.whoSubCommands:
            return self.whoSubCommands[subCommand](msg)

        # Get the first valid match from whoRegex list
        regMatch = next((exp.match(msg.message) for exp in self.whoRegex if exp.match(msg.message) != None), None)

        try:
            quoteId = int(regMatch.group("num0"))
        except (IndexError, AttributeError):
            quoteId = None

        try:
            userName = regMatch.group("user").lower()
        except (IndexError, AttributeError):
            userName = msg.user

        if (result := self.colWho.find_one({ "user" : userName })) is None:
            return f"[{msg.user}]: No quotes from {userName}"

        quoteBank = json.loads(result["quotes"])
        ids = list(map(int, quoteBank.keys()))
        minId = min(ids)
        maxId = max(ids)

        if quoteId == None:
            quoteId, quote = random.choice(list(quoteBank.items()))
        elif (quoteId := str(max(min(quoteId, maxId), minId))) in quoteBank:
            quote = quoteBank[quoteId]
        else:
            return f"[{msg.user}]: No {userName} quote {quoteId}"

        return f"[{userName} {quoteId}]: {quote}"

    def ExecuteWhoAdd(self, msg):
        if not util.CheckPrivSub(msg.tags):
            return f"[{msg.user}]: Only mods and subs can add a who quote"

        if (regMatch := self.whoAddRegex.match(msg.message)) is None:
            return util.GetSyntax(msg.user, "who add USER TEXT")

        userName = regMatch.group("user").lower()
        quote = regMatch.group("text")

        if GetUserId(userName) == None:
            return f"[{msg.user}]: {user} is not an existing username."

        if (result := self.colWho.find_one({ "user" : userName })) is None:
            newCol = True
            quoteId = 1
            quoteBank = {}
        else:
            newCol = False
            quoteId = result["counter"]
            quoteBank = json.loads(result["quotes"])

        quoteBank[quoteId] = quote

        try:
            if newCol:
                self.colWho.insert_one( {
                        "user" : userName,
                        "quotes" : json.dumps(quoteBank),
                        "counter" : int(quoteId) + 1,
                    }
                )
            else:
                self.colWho.update_one(
                    { "user" : userName },
                    { "$set" : {
                            "quotes" : json.dumps(quoteBank),
                            "counter" : int(quoteId) + 1
                        }
                    }
                )
        except TimeoutError:
            return f"[{msg.user}]: Server took too long"

        return f"[{msg.user}]: Added {userName} quote {quoteId}"

    def ExecuteWhoDel(self, msg):
        if not util.CheckPrivMod(msg.tags):
            return f"[{msg.user}]: Only mods can delete a who quote"

        if (regMatch := self.whoDelRegex.match(msg.message)) is None:
            return util.GetSyntax(msg.user, "who del USER NUMBER")

        userName = regMatch.group("user").lower()
        quoteId = regMatch.group("idOrLast")

        if GetUserId(userName) == None:
            return f"[{msg.user}]: {userName} is not an existing username."

        if (result := self.colWho.find_one({ "user" : userName })) is None:
            return f"[{msg.user}]: No quotes from {userName}"

        quoteBank = json.loads(result["quotes"])
        deletedQuote = None

        if quoteId.lower() == "last":
            deletedId, deletedQuote = quoteBank.sort_by_key().pop_back()
        else:
            deletedQuote = quoteBank.pop(quoteId, None)

        if deletedQuote == None:
            return f"[{msg.user}]: No {userName} quote {quoteId}"

        try:
            if len(quoteBank) == 0:
                self.colWho.delete_one({ "user" : userName })
                return f"[{msg.user}]: Deleted {userName} quote {quoteId}. No more quotes for {userName}"

            self.colWho.update_one(
                    { "user" : userName },
                    { "$set" : { "quotes" : json.dumps(quoteBank) } }
                )
        except TimeoutError:
            return f"[{msg.user}]: Server took too long"

        return f"[{msg.user}]: Deleted {userName} quote {quoteId}"
