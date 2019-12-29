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

    def Execute(msg):
        if m.message.startswith("!score"):
            tempscore = random.randint(0,100)
            ptf("tempscore: " + str(tempscore))
            result = None;
            result = self.leaderboard_col.find_one({"user": m.user})

            if result == None:
                score = tempscore
                userObj = {
                    "user": m.user,
                    "score": tempscore
                }
                self.leaderboard_col.insert_one(userObj)
            else:
                ptf(result)
                score = result['score']

            message = f"[{m.user}] Your pure count is: {str(score)}/100"

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

        if m.message.startswith("!pureboard"):
            result = self.leaderboard_col.find().sort("score", 1)

            message = result[0]['user'] + ": " + str(result[0]['score'])
            result = result[1:5]
            for x in result:
                message += ", " + x['user'] + ": " + str(x['score'])

            self.ws.send_message(message)
            return

        ##############################################

        if m.message.startswith("!cursedboard"):
            result = self.leaderboard_col.find().sort("score", -1)

            message = result[0]['user'] + ": " + str(result[0]['score'])
            result = result[1:5]
            for x in result:
                message += ", " + x['user'] + ": " + str(x['score'])

            self.ws.send_message(message)
            return

        ##############################################

        if m.message.startswith("!clearboard"):
            if m.tags['mod'] == '1' or m.user == "doomzero":
                self.leaderboard_col.remove({})
                self.ws.send_message(f"[{m.user}]: Leaderboard cleared!")
                return
            self.ws.send_message(f"[{m.user}]: That command is mods-only!")

        ##############################################

        if m.message.startswith("!clearscore"):
            if m.tags['custom-reward-id'] == "769e238b-fe80-49ba-ab89-1e7e8ad75c88":
                self.leaderboard_col.remove({"user": m.user})
                self.ws.send_message(f"[{m.user}]: Your score has been cleared!")
                return
            self.ws.send_message(f"[{m.user}]: That command requires spending Sushi Rolls on the custom reward!")
