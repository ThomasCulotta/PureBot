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
            elif score >= 75:
                message += " 😇"
            elif score <= 25:
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

            regmatch = re.match(r"^!clearscore (\S+?) ?$", msg.message)
            #for the Reset Another's Score reward command
            if msg.tags['custom-reward-id'] == "490b67dd-a8d3-494f-b605-3626358acd5c":
                #if reward and no syntax
                if regmatch == None:
                    return f"[{msg.user}]: The syntax for that command is !clearscore NAME"
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
        # stealscore
        if msg.message.startswith("!stealscore"):
            regmatch = re.match(r"^!stealscore (\S+?) ?$", msg.message)
            if regmatch == None:
                ptf(f"message: [{msg.message}]")
                return f"[{msg.user}]: The syntax for that command is !stealscore NAME"

            if msg.tags['custom-reward-id'] != "14986982-3669-4e26-a3c4-bf34025e005d":
                return f"[{msg.user}]: That command requires spending Sushi Rolls on the \"doomtest1\" custom reward!"

            if msg.user != "doomzero":
                return f"[{msg.user}]: That command is in testing, sorry. Only DoomZero can use it right now."

            targUser = regmatch[1].lower()
            msgUser = msg.user.lower()

            targResult = self.leaderboard_col.find_one({"user": targUser})
            if targResult == None:
                return f"[{msg.user}]: That user does not have a score!"

            ptf(f"targResult: {targResult}")
            targScore = targResult['score']

            if targScore == None:
                return

            userResult = self.leaderboard_col.find_one({"user": msgUser})
            ptf(f"UserResult: {userResult}")
            userScore = userResult['score']

            if userScore == None:
                self.leaderboard_col.remove({"user": targUser})
                self.leaderboard_col.remove({"user": msgUser})
                self.leaderboard_col.insert_one({"user": msgUser, "score": targScore, "createdAt": datetime.datetime.utcnow()})

                return f"[{msg.user}]: You have stolen {targUser}'s score, and theirs has been reset! Your pure count is: {str(targScore)}/100"
            
            else:
                self.leaderboard_col.remove({"user": targUser})
                self.leaderboard_col.remove({"user": msgUser})

                self.leaderboard_col.insert_one({"user": msgUser, "score": targScore, "createdAt": datetime.datetime.utcnow()})
                self.leaderboard_col.insert_one({"user": targUser, "score": userScore, "createdAt": datetime.datetime.utcnow()})

                return f"[{msg.user}]: You have stolen {targUser}'s score, and given them yours! Your pure count is: {str(targScore)}/100"