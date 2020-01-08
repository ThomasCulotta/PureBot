import re
import json
import random
import pymongo
import datetime

from TwitchWebsocket import TwitchWebsocket

from FlushPrint import ptf

# TODO: Move these to a separate file to make regex readable and centralized
# no need to duplicate these patterns each time and increase chances of typos
regNumGroup = "(\d+?)"
regUserGroup = "(\w+?)"
regTextGroup = "(.+?)"
regIdOrLastGroup = "(\d+?|last)"

class WhoCommands():
    def __init__(self, chan, mongoClient):
        self.chan = chan

        colNameWho = self.chan[1:] + "Who"
        self.colWho = mongoClient.QuoteBotDB[colNameWho]
        self.colWho.create_index([("user", pymongo.ASCENDING)])
        ptf(colNameWho)

    def Execute(self,msg):
        message = msg.message[1:]

        # snippet start
        # who add USER TEXT
        # who add Babotz Hello I'm a Babotz quote
        if message.startswith("who add"):
            regMatch = re.match(f"^who add {regUserGroup} {regTextGroup}$", message)

            if regMatch == None:
                return f"[{msg.user}]: The syntax for that command is: who add USER TEXT"

            userName = regMatch.group(1)
            quoteText = regMatch.group(2)
            ptf(f"{userName} : {quoteText}")

            result = self.colWho.find_one(
                {"user": userName}
            )

            if result == None:
                return f"[{msg.user}]: Unable to add quote for user:. quoteId: [{quoteId}]"

            quoteId = result["counter"]
            quoteBank = json.loads(result["quotes"])

            quoteBank[quoteId] = quoteText

            userObj = {
                "user": msg.user,
                "quotes": json.dumps(quoteBank),
                "counter": quoteId+1,
            }

            self.colWho.insert_one(quoteObj)
            return f"[{msg.user}]: Your quote has been added with id {quoteId}!"

        ##############################################

        # snippet start
        # who delete USER ID
        # who delete Babotz 12
        if message.startswith("who delete"):
            regMatch = re.match(f"^who delete {regUserGroup} {regIdOrLastGroup}$", message)

            if regMatch == None:
                return f"[{msg.user}]: The syntax for that command is: who delete USER NUMBER"

            userName = regMatch.group(1)
            quoteId = regMatch.group(2)

            result = self.colWho.find_one({"user":userName})

            if result == None:
                return f"[{msg.user}]: No quotes from {userName}"

            quoteBank = json.loads(result["quotes"])
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

            ##### TODO: How do we want to handle mods vs reg users??? #####

            # TODO: I currently have all the quotes in one doc per user since mongodb is
            # suited to larger docs anyway and a collection per user will add
            # unnecessary overhead pretty quickly and bloat the db regardless
            # Gonna need to look into collection performance to see how impactful
            # it would actually be. May end up being a nonissue after all (doubtful)

            if result == None:
                return f"[{msg.user}]: No quote with an ID of [{quoteId}]!"
            if msg.tags['mod'] != '1':
                if result['user'] != msg.user:
                    return f"[{msg.user}]: Regular users can't delete a quote someone else added!"
                if result['date'].strftime("%x") != datetime.datetime.now().strftime("%x"):
                    return f"[{msg.user}]: Regular users can't delete a quote except on the day it was added!"

            return f"[{msg.user}]: Deleted quote #{quoteId}!"

        ##############################################

        # snippet start
        # who USER (ID)
        # who Babotz
        # who Babotz 14
        if message.startswith("who"):
            regMatch = re.match(f"^who {regUserGroup} {regNumGroup}?$", message)

            if regMatch == None:
                return f"[{msg.user}]: The syntax for that command is: who USER (ID)"

            userName = regMatch.group(1)
            quoteId = regMatch.group(2)

            result = self.colWho.find_one({"user":userName})

            if result == None:
                return f"[{msg.user}]: No quotes from {userName}"

            quoteBank = json.loads(result["quotes"])

            if quoteId == None:
                quoteId, quote = random.choice(list(quoteBank.items()))
            elif quoteId in quoteBank:
                quote = quoteBank[quoteId]
            else:
                return f"[{msg.user}]: No quote from {userName} with id {quoteId}"

            return f"[{userName} {quoteId}]: \"{result[quote]}\""
