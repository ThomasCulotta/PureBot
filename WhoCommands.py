import re
import json
import random
import pymongo
import datetime

from TwitchWebsocket import TwitchWebsocket

from FlushPrint import ptf, ptfDebug
from TwitchUtils import CheckPriv
import RegGroups as groups

# TODO: Move these to a separate file to make regex readable and centralized
# no need to duplicate these patterns each time and increase chances of typos

class WhoCommands():
    def __init__(self, chan, mongoClient):
        self.chan = chan

        colNameWho = self.chan[1:] + "Who"
        self.colWho = mongoClient.QuoteBotDB[colNameWho]
        self.colWho.create_index([("user", pymongo.ASCENDING)])
        ptfDebug(f"colNameWho: {colNameWho}")

        self.activeCommands = {
            "who",
        }

    def Execute(self, msg):

        # snippet start
        # who add @USER TEXT
        # who add @BabotzInc Hello I'm a Babotz quote
        if msg.message.startswith("who add"):
            regMatch = re.match(f"^who add @{groups.regUserGroup} {groups.regTextGroup}$", msg.message)

            if not CheckPriv(msg.tags):
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

        ##############################################

        # snippet start
        # who del @USER ID
        # who del @BabotzInc 12
        if msg.message.startswith("who del"):
            regMatch = re.match(f"^who del @{groups.regUserGroup} {groups.regIdOrLastGroup}$", msg.message)

            if not CheckPriv(msg.tags):
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

        ##############################################

        # snippet start
        # who (@USER) (ID)
        # who
        # who 14
        # who @BabotzInc
        # who @BabotzInc 14
        if msg.message.startswith("who"):
            regMatch = re.match(f"^who @{groups.regUserGroup} {groups.regNumGroup}$", msg.message)

            # TODO: clean this up
            if regMatch == None:
                regMatch = re.match(f"^who @{groups.regUserGroup}$", msg.message)
                quoteId = None

                if regMatch == None:
                    regMatch = re.match(f"^who {groups.regNumGroup}$", msg.message)
                    userName = msg.user

                    if regMatch == None:
                        regMatch = re.match(f"^who$", msg.message)
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
