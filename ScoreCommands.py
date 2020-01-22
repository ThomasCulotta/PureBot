import random
import pymongo
import datetime

from TwitchWebsocket import TwitchWebsocket

from FlushPrint import ptf
import botconfig

class ScoreCommands:
    def __init__(self, chan, mongoClient):
        self.chan = chan

        leaderboard_col_name = self.chan[1:] + "LB"
        self.leaderboard_col = mongoClient.QuoteBotDB[leaderboard_col_name]
        self.leaderboard_col.create_index([("user", pymongo.ASCENDING)])

        #Set expiration timer on collection documents
        self.leaderboard_col.drop_index([("createdAt", pymongo.ASCENDING)])
        self.leaderboard_col.create_index([("createdAt", pymongo.ASCENDING)], expireAfterSeconds=botconfig.scoreLifespan)
        ptf(leaderboard_col_name)

    def Execute(self,msg):
        ptf("Beginning purecount Command")
        message = msg.message[1:]

        # snippet start
        # purecount
        if message.startswith("purecount"):
            tempscore = random.randint(0,100)
            ptf("tempscore: " + str(tempscore))
            result = None;
            result = self.leaderboard_col.find_one({"user": msg.user})

            if result == None:
                score = tempscore
                userObj = {
                    "user": msg.user,
                    "score": tempscore,
                    "createdAt": datetime.datetime.utcnow()
                }
                self.leaderboard_col.insert_one(userObj)
            else:
                ptf(result)
                score = result['score']
                message = f"[{msg.user}] Your pure count is: {str(score)}/100"

            if score == 69:
                message += " 😎"
            elif score <= 25:
                message += " 😇"
            elif score >= 75:
                message += " 😈"

            return message

        ##############################################

        # snippet start
        # pureboard
        if message.startswith("pureboard"):
            result = self.leaderboard_col.find().sort("score", 1)

            message = result[0]['user'] + ": " + str(result[0]['score'])
            result = result[1:5]
            for x in result:
                message += ", " + x['user'] + ": " + str(x['score'])

            return message

        ##############################################

        # snippet start
        # cursedboard
        if message.startswith("cursedboard"):
            result = self.leaderboard_col.find().sort("score", -1)
            message = result[0]['user'] + ": " + str(result[0]['score'])
            result = result[1:5]

            for x in result:
                message += ", " + x['user'] + ": " + str(x['score'])

            return message

        ##############################################

        # snippet start
        # clearboard
        if message.startswith("clearboard"):
            if msg.tags['mod'] == '1' or msg.user == "doomzero":
                self.leaderboard_col.remove({})
                return f"[{msg.user}]: Leaderboard cleared!"

            return f"[{msg.user}]: That command is mods-only!"

        ##############################################

        # snippet start
        # clearscore
        if message.startswith("clearscore"):
            if msg.tags['custom-reward-id'] == "769e238b-fe80-49ba-ab89-1e7e8ad75c88":
                self.leaderboard_col.remove({"user": msg.user})
                return f"[{msg.user}]: Your score has been cleared!"

            return f"[{msg.user}]: That command requires spending Sushi Rolls on the custom reward!"
