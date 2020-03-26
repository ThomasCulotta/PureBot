import re
import json
import random
import pymongo

from FlushPrint import ptf, ptfDebug
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

    # snippet start
    # who (@USER) (ID)
    # who
    # who 14
    # who @BabotzInc
    # who @BabotzInc 14
    # remarks
    # When no username is given, this command defaults to your own quotes.
    def ExecuteWho(self, msg):
        try:
            subCommand = msg.message.lower().split()[1]
        except IndexError:
            subCommand = None

        if subCommand in self.whoSubCommands:
            return self.whoSubCommands[subCommand](msg)

        regMatch = re.match(f"^who @{groups.user} {groups.num}$", msg.message)

        # TODO: clean this up
        if regMatch == None:
            regMatch = re.match(f"^who @{groups.user}$", msg.message)
            quoteId = None

            if regMatch == None:
                regMatch = re.match(f"^who {groups.num}$", msg.message)
                userName = msg.user

                if regMatch == None:
                    regMatch = re.match(f"^who$", msg.message)

                    if regMatch == None:
                        return f"[{msg.user}]: The syntax for that command is: who (@USER) (ID)"
                else:
                    quoteId = regMatch.group(1)
            else:
                userName = regMatch.group(1).lower()
        else:
            userName = regMatch.group(1).lower()
            quoteId = regMatch.group(2)


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
    # who add @USER TEXT
    # who add @BabotzInc Hello I'm a Babotz quote
    # remarks
    # @ing the user is required. Type @ and use Twitch's username picker/autocomplete to ensure the correct username is given.
    def ExecuteWhoAdd(self, msg):
        regMatch = re.match(f"^who add @{groups.user} {groups.text}$", msg.message)

        if not util.CheckPriv(msg.tags):
            return f"[{msg.user}]: Regular users can't add a who quote!"

        if regMatch == None:
            return f"[{msg.user}]: The syntax for that command is: who add @USER TEXT"

        userName = regMatch.group(1).lower()
        quote = regMatch.group(2)

        result = self.colWho.find_one(
            {"user": userName}
        )

        newCol = False
        quoteBank = {}
        if result == None:
            newCol = True
            quoteId = 1
        else:
            quoteId = result['counter']
            quoteBank = json.loads(result['quotes'])

        quoteBank[quoteId] = quote
        ptfDebug(f"{userName} : {quote}")

        if newCol:
            userObj = {
                "user": userName,
                "quotes": json.dumps(quoteBank),
                "counter": int(quoteId)+1,
            }
            self.colWho.insert_one(userObj)
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
    # who del @USER ID
    # who del @BabotzInc 12
    # remarks
    # @ing the user is required. Type @ and use Twitch's username picker/autocomplete to ensure the correct username is given.
    def ExecuteWhoDel(self, msg):
        regMatch = re.match(f"^who del @{groups.user} {groups.idOrLast}$", msg.message)

        if not util.CheckPriv(msg.tags):
            return f"[{msg.user}]: Regular users can't delete a who quote!"

        if regMatch == None:
            return f"[{msg.user}]: The syntax for that command is: who del @USER NUMBER"

        userName = regMatch.group(1).lower()
        quoteId = regMatch.group(2)

        result = self.colWho.find_one({"user":userName})

        if result == None:
            return f"[{msg.user}]: No quotes from {userName}"

        quoteBank = json.loads(result['quotes'])
        deletedQuote = None

        if quoteId == "last":
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
