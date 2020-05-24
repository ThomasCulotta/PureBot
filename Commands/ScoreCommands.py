import re
import random
import pymongo
import datetime

import botconfig

from Utilities.FlushPrint import ptf
import Utilities.TwitchUtils as util
import Utilities.RegGroups as groups

class ScoreCommands:
    def __init__(self, chan, mongoClient):
        self.colLeaderboard = mongoClient.QuoteBotDB[chan + "LB"]
        self.colLeaderboard.create_index([("user", pymongo.ASCENDING)])

        if not hasattr(botconfig, "scoreLifespan"):
            ptf("scoreLifespan not found in botconfig")
        if not hasattr(botconfig, "clearScoreId"):
            ptf("clearScoreId not found in botconfig")
        if not hasattr(botconfig, "stealScoreId"):
            ptf("stealScoreId not found in botconfig")
        if not hasattr(botconfig, "swapScoreId"):
            ptf("swapScoreId not found in botconfig")

        # Set expiration timer on collection documents
        self.colLeaderboard.create_index([("createdAt", pymongo.ASCENDING)], expireAfterSeconds=botconfig.scoreLifespan)

        self.scoreMin = -1
        self.scoreMax = 101

        self.activeCommands = {
            "purecount"   : self.ExecutePureCount,
            "pureboard"   : self.ExecutePureBoard,
            "curseboard"  : self.ExecuteCurseBoard,
            "cursedboard" : self.ExecuteCurseBoard,
            "clearboard"  : self.ExecuteClearBoard,
            "stealscore"  : self.ExecuteStealScore,
            "swapscore"   : self.ExecuteSwapScore,
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
        self.colLeaderboard.remove({ "user" : msg.user })
        return f"[{msg.user}]: Your score has been cleared"

    def RedeemStealScore(self, msg):
        util.RedeemReward(msg.user, self.rewardStealId)

        if (regMatch := self.redeemStealSwapScoreRegex.match(msg.message)) is None:
            return f"[{msg.user}]: You've redeemed stealscore. At any time, use the command: stealscore USER"

        return self.StealScoreHelper(msg.user, regMatch.group("user"))

    def RedeemSwapScore(self, msg):
        util.RedeemReward(msg.user, self.rewardSwapId)

        if (regMatch := self.redeemStealSwapScoreRegex.match(msg.message)) is None:
            return f"[{msg.user}]: You've redeemed swapscore. At any time, use the command: swapscore USER"

        return self.SwapScoreHelper(msg.user, regMatch.group("user"))

    def MakeInsert(self, user, score):
        return { "user" : user, "score" : score, "createdAt" : datetime.datetime.utcnow() }

    def MakeUpdate(self, user, score):
        return { "user" : user }, { "$set" : { "score" : score, "createdAt" : datetime.datetime.utcnow() } }

    def StealScoreHelper(self, user, targUser):
        targUser = targUser.lower()

        if (targResult := self.colLeaderboard.find_one({ "user" : targUser })) is None:
            return f"[{user}]: That user does not have a score"

        if not util.CheckRemoveReward(user, self.rewardStealId):
            return f"[{user}]: This command requires spending sushi rolls"

        targScore = targResult["score"]

        # Give the target a new score
        newScore = random.randint(self.scoreMin, self.scoreMax)
        self.colLeaderboard.update_one(self.MakeUpdate(targUser, newScore))

        # Set the user's score to the target's old score
        if (userResult := self.colLeaderboard.find_one({ "user" : user })) is None:
            self.colLeaderboard.insert_one(self.MakeInsert(user, targScore))
        else:
            self.colLeaderboard.update_one(self.MakeUpdate(user, targScore))

        return f"[{user}]: You have stolen {targUser}'s score and given them a new one! Your pure count is {targScore}/100, and theirs is {newScore}/100"

    def SwapScoreHelper(self, user, targUser):
        targUser = targUser.lower()

        if (targResult := self.colLeaderboard.find_one({ "user" : targUser })) is None:
            return f"[{user}]: That user does not have a score"

        if not util.CheckRemoveReward(user, self.rewardSwapId):
            return f"[{user}]: This command requires spending sushi rolls"

        targScore = targResult["score"]

        if (userResult := self.colLeaderboard.find_one({ "user" : user })) is None:
            newScore = random.randint(self.scoreMin, self.scoreMax)
            self.colLeaderboard.insert_one(self.MakeInsert(user, targScore))
            self.colLeaderboard.update_one(self.MakeUpdate(targUser, newScore))

            return f"[{user}]: You have stolen {targUser}'s score and given them a new one! Your pure count is {targScore}/100, and theirs is {newScore}/100"

        else:
            userScore = userResult["score"]
            self.colLeaderboard.update_one(self.MakeUpdate(user, targScore))
            self.colLeaderboard.update_one(self.MakeUpdate(targUser, userScore))

            return f"[{user}]: You have swapped {targUser}'s score with your own! Your pure count is {targScore}/100, and theirs is {userScore}/100"

    # snippet start
    # purecount
    def ExecutePureCount(self, msg):
        if (result := self.colLeaderboard.find_one({ "user" : msg.user })) is None:
            score = random.randint(self.scoreMin, self.scoreMax)
            self.colLeaderboard.insert_one(self.MakeInsert(msg.user, score))
        else:
            score = result["score"]

        resMessage = f"[{msg.user}] Your pure count is: {score}/100"

        if score == 69:
            resMessage += " 😎"
        elif score >= 75:
            resMessage += " 😇"
        elif score <= 25:
            resMessage += " 😈"

        return resMessage

    # Handles pureboard and curseboard based on the sort order
    def BoardHelper(self, user, sort):
        results = self.colLeaderboard.find().sort([("score", sort)]).limit(5)

        resMessage = ""
        for result in results:
            resMessage += f"{result['user']}: {result['score']}, "

        if resMessage == "":
            return f"[{user}]: Nobody has a pure count yet"

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
        if not util.CheckPrivMod(msg.tags):
            return f"[{msg.user}]: Only mods can clear the leaderboard"

        self.colLeaderboard.remove({})
        return f"[{msg.user}]: Leaderboard cleared"

    ## snippet start
    # stealscore USER
    # stealscore BabotzInc
    # remarks
    # This command requires you to spend sushi rolls.
    def ExecuteStealScore(self, msg):
        if (regMatch := self.stealScoreRegex.match(msg.message)) is None:
            return util.GetSyntax(msg.user, "stealscore USER")

        return self.StealScoreHelper(msg.user, regMatch.group("user").lower())

    ## snippet start
    # swapscore USER
    # swapscore BabotzInc
    # remarks
    # This command requires you to spend sushi rolls.
    def ExecuteSwapScore(self, msg):
        if (regMatch := self.swapScoreRegex.match(msg.message)) is None:
            return util.GetSyntax(msg.user, "swapscore USER")

        return self.SwapScoreHelper(msg.user, regMatch.group("user").lower())
