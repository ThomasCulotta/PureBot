import random
import pymongo

from TwitchWebsocket import TwitchWebsocket

from FlushPrint import ptf

class ScoreCommands:
    def __init__(self, chan, ws, mongoClient):
        self.ws = ws
        self.chan = chan

        LBcolName = self.chan[1:] + "LB"
        self.leaderboard_col = mongoClient.QuoteBotDB[LBcolName]
        self.leaderboard_col.create_index([("user", pymongo.ASCENDING)])
        ptf(LBcolName)

    def Execute(self,msg):
        ptf("executing")
        if msg.message.startswith("!score"):
            tempscore = random.randint(0,100)
            ptf("tempscore: " + str(tempscore))
            result = None;
            result = self.leaderboard_col.find_one({"user": msg.user})

            if result == None:
                score = tempscore
                userObj = {
                    "user": msg.user,
                    "score": tempscore
                }
                self.leaderboard_col.insert_one(userObj)
            else:
                ptf(result)
                score = result['score']

            message = f"[{msg.user}] Your pure count is : {str(score)}/100"

            if score == 69:
                #message += " nice :sunglasses:"
                message += " 😎"
            elif score <= 25:
                #message += " :innocent:"
                message += " 😇"
            elif score >= 75:
                #message += " :smiling_imp:"
                message += " 😈"

            self.ws.send_message(message)
            return

        ##############################################

        if msg.message.startswith("!pureboard"):
            result = self.leaderboard_col.find().sort("score", 1)

            message = result[0]['user'] + ": " + str(result[0]['score'])
            result = result[1:5]
            for x in result:
                message += ", " + x['user'] + ": " + str(x['score'])

            self.ws.send_message(message)
            return

        ##############################################

        if msg.message.startswith("!cursedboard"):
            result = self.leaderboard_col.find().sort("score", -1)

            message = result[0]['user'] + ": " + str(result[0]['score'])
            result = result[1:5]
            for x in result:
                message += ", " + x['user'] + ": " + str(x['score'])

            self.ws.send_message(message)
            return

        ##############################################

        if msg.message.startswith("!clearboard"):
            if msg.tags['mod'] == '1' or msg.user == "doomzero":
                self.leaderboard_col.remove({})
                self.ws.send_message(f"[{msg.user}]: Leaderboard cleared!")
                return
            self.ws.send_message(f"[{msg.user}]: That command is mods-only!")
            return

        ##############################################

        if msg.message.startswith("!clearscore"):
            if msg.tags['custom-reward-id'] == "769e238b-fe80-49ba-ab89-1e7e8ad75c88":
                self.leaderboard_col.remove({"user": msg.user})
                self.ws.send_message(f"[{msg.user}]: Your score has been cleared!")
                return
            self.ws.send_message(f"[{msg.user}]: That command requires spending Sushi Rolls on the custom reward!")
            return