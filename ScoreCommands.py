import random
import pymongo
import datetime
import re

from FlushPrint import ptf, ptfDebug
from TwitchUtils import CheckPriv
import botconfig
import RegGroups as groups

class ScoreCommands:
    def __init__(self, chan, mongoClient):
        self.chan = chan

        leaderboard_col_name = self.chan[1:] + "LB"
        self.leaderboard_col = mongoClient.QuoteBotDB[leaderboard_col_name]
        self.leaderboard_col.create_index([("user", pymongo.ASCENDING)])

        #Set expiration timer on collection documents
        self.leaderboard_col.create_index([("createdAt", pymongo.ASCENDING)], expireAfterSeconds=botconfig.scoreLifespan)
        ptfDebug(f"leaderboard_col_name: {leaderboard_col_name}")

        self.activeCommands = {
            "purecount",
            "pureboard",
            "curseboard",
            "cursedboard",
            "clearboard",
            "clearscore",
            "stealscore",
            "swapscore",
        }

    def Execute(self,msg):
        ptfDebug("Beginning purecount Command")

        # snippet start
        # purecount
        if msg.message.startswith("purecount"):
            tempscore = random.randint(-1,101)
            ptfDebug("tempscore: " + str(tempscore))
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
                ptfDebug(result)
                score = result['score']

            resMessage = f"[{msg.user}] Your pure count is: {str(score)}/100"

            if score == 69:
                resMessage += " 😎"
            elif score >= 75:
                resMessage += " 😇"
            elif score <= 25:
                resMessage += " 😈"

            return resMessage

        ##############################################

        # snippet start
        # pureboard
        sort_order = 1

        if msg.message.startswith("pureboard"):
            sort_order = -1

        # snippet start
        # curseboard
        if msg.message.startswith("pureboard") or msg.message.startswith("curseboard") or msg.message.startswith("cursedboard"):
            result = self.leaderboard_col.find().sort([("score", sort_order)]).limit(5)

            resMessage = ""
            for x in result:
                resMessage += x['user'] + ": " + str(x['score']) + ", "

            if resMessage == "":
                return f"[{msg.user}]: Nobody has a pure count yet!"

            resMessage = resMessage[:-2]
            return resMessage

        ##############################################

        # snippet start
        # clearboard
        if msg.message.startswith("clearboard"):
            if CheckPriv(msg.tags) or msg.user == "doomzero":
                self.leaderboard_col.remove({})
                return f"[{msg.user}]: Leaderboard cleared!"

            return f"[{msg.user}]: That command is mods-only!"

        ##############################################

        ## snippet start
        # clearscore USER
        # clearscore BabotzInc
        # remarks
        # This command requires you to spend sushi rolls.
        if msg.message.startswith("clearscore"):

            regmatch = re.match(rf"^clearscore {groups.user}$", msg.message)
            #for the Reset Another's Score reward command
            if msg.tags['custom-reward-id'] == "490b67dd-a8d3-494f-b605-3626358acd5c":
                #if reward and no syntax
                if regmatch == None:
                    return f"[{msg.user}]: The syntax for that command is clearscore NAME"
                #if reward and syntax
                if msg.user != "doomzero":
                    return f"[{msg.user}]: That command is in testing, sorry. Only DoomZero can use it right now."

                targUser = regmatch[1].lower()

                self.leaderboard_col.remove({"user": targUser})
                return f"[{msg.user}]: You have cleared {targUser}'s score! 😈"
            if regmatch:
                #if no reward and syntax
                return f"[{msg.user}]: That command requires spending Sushi Rolls on the \"doomtest2\" custom reward!"

            #for the Score Reset reward command
            if msg.tags['custom-reward-id'] == "769e238b-fe80-49ba-ab89-1e7e8ad75c88":
                self.leaderboard_col.remove({"user": msg.user})
                return f"[{msg.user}]: Your score has been cleared!"

            return f"[{msg.user}]: That command requires spending Sushi Rolls on the \"Score Reset\" custom reward!"

        ##############################################

        # snippet start
        # stealscore USER
        # stealscore BabotzInc
        # remarks
        # This command requires you to spend sushi rolls.
        if msg.message.startswith("stealscore"):
            regmatch = re.match(rf"^stealscore {groups.user}$", msg.message)
            if regmatch == None:
                ptfDebug(f"message: [{msg.message}]")
                return f"[{msg.user}]: The syntax for that command is stealscore NAME"

            if msg.tags['custom-reward-id'] != "14986982-3669-4e26-a3c4-bf34025e005d":
               return f"[{msg.user}]: That command requires spending Sushi Rolls on the \"doomtest1\" custom reward!"

            # if msg.user != "doomzero":
            #     return f"[{msg.user}]: That command is in testing, sorry. Only DoomZero can use it right now."

            targUser = regmatch[1].lower()
            msgUser = msg.user.lower()

            targResult = self.leaderboard_col.find_one({"user": targUser})
            if targResult == None:
                return f"[{msg.user}]: That user does not have a score!"

            ptfDebug(f"targResult: {targResult}")
            targScore = targResult['score']

            userResult = self.leaderboard_col.find_one({"user": msgUser})
            ptfDebug(f"UserResult: {userResult}")

            #reset the target's score
            newScore = random.randint(0,100)
            self.leaderboard_col.update_one({"user": targUser}, { "$set": {"score": newScore, "createdAt": datetime.datetime.utcnow()}})

            #set the user's score to the target's old score
            userScore = userResult['score']
            if userScore == None:
                self.leaderboard_col.insert_one({"user": msgUser, "score": targScore, "createdAt": datetime.datetime.utcnow()})
            else:
                self.leaderboard_col.update_one({"user": msgUser}, { "$set": {"score": targScore, "createdAt": datetime.datetime.utcnow()}})

            return f"[{msg.user}]: You have stolen {targUser}'s score, and theirs has been reset! Your pure count is {str(targScore)}/100, and theirs is {str(newScore)}/100"

        ##############################################

        # snippet start
        # swapscore USER
        # swapscore BabotzInc
        # remarks
        # This command requires you to spend sushi rolls.
        if msg.message.startswith("swapscore"):
            regmatch = re.match(rf"^swapscore {groups.user}$", msg.message)
            if regmatch == None:
                ptfDebug(f"message: [{msg.message}]")
                return f"[{msg.user}]: The syntax for that command is swapscore NAME"

            if msg.tags['custom-reward-id'] != "14986982-3669-4e26-a3c4-bf34025e005d":
                return f"[{msg.user}]: That command requires spending Sushi Rolls on the \"doomtest3\" custom reward!"

            # if msg.user != "doomzero":
            #     return f"[{msg.user}]: That command is in testing, sorry. Only DoomZero can use it right now."

            targUser = regmatch[1].lower()
            msgUser = msg.user.lower()

            targResult = self.leaderboard_col.find_one({"user": targUser})
            if targResult == None:
                return f"[{msg.user}]: That user does not have a score!"

            ptfDebug(f"targResult: {targResult}")
            targScore = targResult['score']

            userResult = self.leaderboard_col.find_one({"user": msgUser})
            ptfDebug(f"UserResult: {userResult}")
            userScore = userResult['score']

            if userScore == None:
                newScore = random.randint(0,100)
                self.leaderboard_col.insert_one({"user": msgUser, "score": targScore, "createdAt": datetime.datetime.utcnow()})
                self.leaderboard_col.update_one({"user": targUser}, { "$set": {"score": newScore, "createdAt": datetime.datetime.utcnow()}})

                return f"[{msg.user}]: You have taken {targUser}'s score, and theirs has been reset! Your pure count is {str(targScore)}/100, and theirs is {str(newScore)}/100"

            else:
                self.leaderboard_col.update_one({"user": msgUser}, { "$set": {"score": targScore, "createdAt": datetime.datetime.utcnow()}})
                self.leaderboard_col.update_one({"user": targUser}, { "$set": {"score": userScore, "createdAt": datetime.datetime.utcnow()}})

                return f"[{msg.user}]: You have swapped {targUser}'s score with your own! Your pure count is {str(targScore)}/100, and theirs is {str(userScore)}/100"

