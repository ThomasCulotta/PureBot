import re
import json
import random
import pymongo

from FlushPrint import ptf, ptfDebug
from BotRequests import GetUserId
import TwitchUtils as util
import RegGroups as groups

class WhoCommands():
    def __init__(self, chan, mongoClient):
        self.chan = chan

        colNameWho = self.chan[1:] + "Who"
        self.colWho = mongoClient.QuoteBotDB[colNameWho]
        self.colWho.create_index([("user", pymongo.ASCENDING)])
        ptfDebug(f"colNameWho: {colNameWho}")

        self.activeCommands = {
            "who" : self.ExecuteWho,
        }

        self.whoSubCommands = {
            "add" : self.ExecuteWhoAdd,
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

    # snippet start
    # who (USER) (ID)
    # who
    # who 14
    # who @BabotzInc
    # who BabotzInc 14
    # remarks
    # When no username is given, this command defaults to your own quotes.
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
            quoteId = regMatch.group("num0")
        except (IndexError, AttributeError):
            quoteId = None

        try:
            userName = regMatch.group("user")
        except (IndexError, AttributeError):
            userName = msg.user

        result = self.colWho.find_one({"user":userName})

        if result == None:
            return f"[{msg.user}]: No quotes from {userName}"

        quoteBank = json.loads(result['quotes'])

        if quoteId == None:
            quoteId, quote = random.choice(list(quoteBank.items()))
        elif quoteId in quoteBank:
            quote = quoteBank[quoteId]
        else:
            return f"[{msg.user}]: No quote from {userName} with id {quoteId}"

        return f"[{userName} {quoteId}]: {quote}"

    # snippet start
    # who add USER TEXT
    # who add @BabotzInc Hello I'm a Babotz quote
    # remarks
    # @ing the user is recommended. Type @ and use Twitch's username picker/autocomplete to help ensure the correct username is given.
    def ExecuteWhoAdd(self, msg):
        if not util.CheckPriv(msg.tags):
            return f"[{msg.user}]: Regular users can't add a who quote!"

        regMatch = self.whoAddRegex.match(msg.message)

        if regMatch == None:
            return f"[{msg.user}]: The syntax for that command is: who add USER TEXT"

        userName = regMatch.group("user").lower()
        quote = regMatch.group("text")

        if GetUserId(userName) == None:
            return f"[{msg.user}]: {user} is not an existing username."

        result = self.colWho.find_one(
            {"user": userName}
        )

        if result == None:
            newCol = True
            quoteId = 1
            quoteBank = {}
        else:
            newCol = False
            quoteId = result['counter']
            quoteBank = json.loads(result['quotes'])

        quoteBank[quoteId] = quote
        ptfDebug(f"{userName} : {quote}")

        if newCol:
            self.colWho.insert_one( {
                    "user": userName,
                    "quotes": json.dumps(quoteBank),
                    "counter": int(quoteId)+1,
                }
            )
        else:
            self.colWho.update_one(
                {"user": userName},
                {"$set": {
                        "quotes": json.dumps(quoteBank),
                        "counter": int(quoteId)+1
                    }
                }
            )

        return f"[{msg.user}]: Your quote for user {userName} has been added with id {quoteId}!"

    # snippet start
    # who del USER ID
    # who del @BabotzInc 12
    # remarks
    # @ing the user is recommended. Type @ and use Twitch's username picker/autocomplete to help ensure the correct username is given.
    def ExecuteWhoDel(self, msg):
        if not util.CheckPriv(msg.tags):
            return f"[{msg.user}]: Regular users can't delete a who quote!"

        regMatch = self.whoDelRegex.match(msg.message)

        if regMatch == None:
            return f"[{msg.user}]: The syntax for that command is: who del USER NUMBER"

        userName = regMatch.group("user").lower()
        quoteId = regMatch.group("idOrLast")

        if GetUserId(userName) == None:
            return f"[{msg.user}]: {userName} is not an existing username."

        result = self.colWho.find_one({"user":userName})

        if result == None:
            return f"[{msg.user}]: No quotes from {userName}"

        quoteBank = json.loads(result['quotes'])
        deletedQuote = None

        if quoteId.lower() == "last":
            deletedId, deletedQuote = quoteBank.sort_by_key().pop_back()##################
        else:
            deletedQuote = quoteBank.pop(quoteId, None)

        if deletedQuote == None:
            return f"[{msg.user}]: No {userName} quote #{quoteId}"

        if len(quoteBank) == 0:
            self.colWho.delete_one({"user":userName})
            return f"[{msg.user}]: Deleted {userName} quote #{quoteId}. No more quotes for {userName}"

        self.colWho.update_one(
                {"user": userName},
                {"$set": {"quotes": json.dumps(quoteBank)}}
            )

        return f"[{msg.user}]: Deleted {userName} quote #{quoteId}"
