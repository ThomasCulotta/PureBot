import random
import pymongo
import datetime
import re

import botconfig

from Utilities.FlushPrint import ptf, ptfDebug
import Utilities.TwitchUtils as util
import Utilities.RegGroups as groups

class ScoreCommands:
    def __init__(self, chan, mongoClient):
        leaderboard_col_name = chan + "LB"
        self.leaderboard_col = mongoClient.QuoteBotDB[leaderboard_col_name]
        self.leaderboard_col.create_index([("user", pymongo.ASCENDING)])

        # Set expiration timer on collection documents
        self.leaderboard_col.create_index([("createdAt", pymongo.ASCENDING)], expireAfterSeconds=botconfig.scoreLifespan)
        ptfDebug(f"leaderboard_col_name: {leaderboard_col_name}")

        self.activeCommands = {
            "purecount" : self.ExecutePureCount,
            "pureboard" : self.ExecutePureBoard,
            "curseboard" : self.ExecuteCurseBoard,
            "cursedboard" : self.ExecuteCurseBoard,
            "clearboard" : self.ExecuteClearBoard,
            "stealscore" : self.ExecuteStealScore,
            "swapscore" : self.ExecuteSwapScore,
        }

        self.activeRewards = {
            botconfig.clearScoreId : self.RedeemClearScore,
            botconfig.stealScoreId : self.RedeemStealScore,
            botconfig.swapScoreId : self.RedeemSwapScore,
        }

        self.rewardStealId = "stealScore"
        self.rewardSwapId = "swapScore"

        self.redeemStealSwapScoreRegex = re.compile(f"^{groups.user}")
        self.stealScoreRegex = re.compile(f"^stealscore {groups.user}")
        self.swapScoreRegex = re.compile(f"^swapscore {groups.user}")

    def RedeemClearScore(self, msg):
        self.leaderboard_col.remove({"user": msg.user})
        return f"[{msg.user}]: Your score has been cleared!"

    def RedeemStealScore(self, msg):
        util.RedeemReward(msg.user, self.rewardStealId)
        regMatch = self.redeemStealSwapScoreRegex.match(msg.message)

        if regMatch == None:
            return f"[{msg.user}]: You've redeemed stealscore. At any time, use the command stealscore USER"

        return self.StealScoreHelper(msg.user, regMatch.group("user"))

    def RedeemSwapScore(self, msg):
        util.RedeemReward(msg.user, self.rewardSwapId)
        regMatch = self.redeemStealSwapScoreRegex.match(msg.message)

        if regMatch == None:
            return f"[{msg.user}]: You've redeemed swapscore. At any time, use the command swapscore USER"

        return self.SwapScoreHelper(msg.user, regMatch.group("user"))

    def StealScoreHelper(self, user, targUser):
        targUser = targUser.lower()
        targResult = self.leaderboard_col.find_one({"user": targUser})

        if targResult == None:
            return f"[{user}]: That user does not have a score!"

        if not util.CheckRemoveReward(user, self.rewardStealId):
            return f"[{user}]: This command requires spending sushi rolls"

        ptfDebug(f"targResult: {targResult}")
        targScore = targResult['score']

        # Give the target a new score
        newScore = random.randint(-1,101)
        self.leaderboard_col.update_one({"user": targUser}, { "$set": {"score": newScore, "createdAt": datetime.datetime.utcnow()}})

        userResult = self.leaderboard_col.find_one({"user": user})
        ptfDebug(f"UserResult: {userResult}")

        # Set the user's score to the target's old score
        if userResult == None:
            self.leaderboard_col.insert_one({"user": user, "score": targScore, "createdAt": datetime.datetime.utcnow()})
        else:
            self.leaderboard_col.update_one({"user": user}, { "$set": {"score": targScore, "createdAt": datetime.datetime.utcnow()}})

        return f"[{user}]: You have stolen {targUser}'s score and given them a new one! Your pure count is {targScore}/100, and theirs is {newScore}/100"

    def SwapScoreHelper(self, user, targUser):
        targetUser = targetUser.lower()
        targResult = self.leaderboard_col.find_one({"user": targUser})

        if targResult == None:
            return f"[{user}]: That user does not have a score!"

        if not util.CheckRemoveReward(user, self.rewardSwapId):
            return f"[{user}]: This command requires spending sushi rolls"

        ptfDebug(f"targResult: {targResult}")
        targScore = targResult['score']

        userResult = self.leaderboard_col.find_one({"user": user})
        ptfDebug(f"UserResult: {userResult}")

        if userResult == None:
            newScore = random.randint(-1,101)
            self.leaderboard_col.insert_one({"user": user, "score": targScore, "createdAt": datetime.datetime.utcnow()})
            self.leaderboard_col.update_one({"user": targUser}, { "$set": {"score": newScore, "createdAt": datetime.datetime.utcnow()}})

            return f"[{user}]: You have taken {targUser}'s score and given them a new one! Your pure count is {targScore}/100, and theirs is {newScore}/100"

        else:
            userScore = userResult['score']
            self.leaderboard_col.update_one({"user": user}, { "$set": {"score": targScore, "createdAt": datetime.datetime.utcnow()}})
            self.leaderboard_col.update_one({"user": targUser}, { "$set": {"score": userScore, "createdAt": datetime.datetime.utcnow()}})

            return f"[{user}]: You have swapped {targUser}'s score with your own! Your pure count is {targScore}/100, and theirs is {userScore}/100"

    # snippet start
    # purecount
    def ExecutePureCount(self, msg):
        tempscore = random.randint(-1,101)
        ptfDebug("tempscore: " + str(tempscore))

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

    # Handles pureboard and curseboard based on the sort order
    def BoardHelper(self, user, sort_order):
        result = self.leaderboard_col.find().sort([("score", sort_order)]).limit(5)

        resMessage = ""
        for x in result:
            resMessage += x['user'] + ": " + str(x['score']) + ", "

        if resMessage == "":
            return f"[{user}]: Nobody has a pure count yet!"

        resMessage = resMessage[:-2]
        return resMessage

    # snippet start
    # pureboard
    def ExecutePureBoard(self, msg):
        return self.BoardHelper(msg.user, -1)

    # snippet start
    # curseboard
    def ExecuteCurseBoard(self, msg):
        return self.BoardHelper(msg.user, 1)

    # snippet start
    # clearboard
    # remarks
    # Mod Only. Clears leaderboard.
    def ExecuteClearBoard(self, msg):
        if util.CheckPrivMod(msg.tags):
            self.leaderboard_col.remove({})
            return f"[{msg.user}]: Leaderboard cleared!"

        return f"[{msg.user}]: Only mods can clear leaderboards"

    ## snippet start
    # stealscore USER
    # stealscore BabotzInc
    # remarks
    # This command requires you to spend sushi rolls.
    def ExecuteStealScore(self, msg):
        regmatch = self.stealScoreRegex.match(msg.message)

        if regmatch == None:
            return f"[{msg.user}]: The syntax for that command is stealscore USER"

        return self.StealScoreHelper(msg.user, regmatch.group(1).lower())

    ## snippet start
    # swapscore USER
    # swapscore BabotzInc
    # remarks
    # This command requires you to spend sushi rolls.
    def ExecuteSwapScore(self, msg):
        regmatch = self.swapScoreRegex.match(msg.message)

        if regmatch == None:
            return f"[{msg.user}]: The syntax for that command is swapscore USER"

        return self.SwapScoreHelper(msg.user, regmatch.group(1).lower())
