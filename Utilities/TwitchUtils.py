import json
import time
import pymongo
import threading

from TwitchWebsocket import TwitchWebsocket
from .FlushPrint import ptf

ws = None
statsDict = {}
statsLock = None
statsThread = None
colRewards = None

# True if user is a mod or the broadcaster
def CheckPrivMod(tags):
    return (tags["mod"] == "1" or
            tags["user-id"] == tags["room-id"])

# True if user is a sub, mod, or the broadcaster
def CheckPrivSub(tags):
    return (CheckPrivMod(tags) or
            tags["subscriber"] == "1")

# True if user is a dev
def CheckDev(user):
    return (user == "babotzinc" or
            user == "doomzero")

# Record that the given user has redeemed the given reward
def RedeemReward(user, rewardId):
    result = colRewards.find_one({"user": user})

    rewards = {}
    if result == None:
        rewards[rewardId] = 1
        userObj = {
            "user" : user,
            "rewards" : json.dumps(rewards)
        }
        colRewards.insert_one(userObj)
    else:
        rewards = json.loads(result['rewards'])

        if rewardId in rewards:
            rewards[rewardId] += 1
        else:
            rewards[rewardId] = 1

        colRewards.update_one(
            {"user": user},
            {"$set": {"rewards": json.dumps(rewards)}}
        )

# Return true if the given user has redeemed the given reward and decrement
def CheckRemoveReward(user, rewardId):
    result = colRewards.find_one({"user": user})

    if result == None:
        return False

    rewards = json.loads(result['rewards'])

    if rewardId in rewards:
        if rewards[rewardId] == 1:
            del rewards[rewardId]
        else:
            rewards[rewardId] -= 1

        if len(rewards) == 0:
            colRewards.delete_one({"user":user})
        else:
            colRewards.update_one(
                {"user": user},
                {"$set": {"rewards": json.dumps(rewards)}}
            )

        return True

    return False


# Log info for an incoming message
def LogReceived(type, user, message, tags, recordUsage=False):
    ptf(f"Received [{type}] from [{user}]: {message}", time=True)
    ptf(f"With tags: {tags}")

    if (recordUsage)
        token = message.lower().split(" ")[0]
        RecordUsage(token, user)

# Send a message to twitch chat and log
def SendMessage(response, type="PRIVMSG", user=None):
    global ws
    userStr = "" if user == None else f" to [{user}]"

    if response == None:
        ptf(f"No [{type}] message sent{userStr}\n", time=True)
        return

    if type == "WHISPER":
        ws.send_whisper(user, response)
    else:
        ws.send_message(response)

    ptf(f"Sent [{type}]{userStr}: {response}\n", time=True)

# Increment command usage of non-dev users
def RecordUsage(command, user):
    global statsDict
    global statsLock

    if CheckDev(user):
        return

    with statsLock:
        if command in statsDict:
            statsDict[command] += 1
        else:
            statsDict[command] = 1

# Dump current usage stats to file
def StoreUsageAsync():
    global statsDict
    global statsLock

    while True:
        # Every 10 minutes
        time.sleep(60 * 10)

        # No stats to dump
        if not statsDict:
            continue

        with open('UsageStats.json', 'r') as file:
            statsJson = json.load(file)

        with open('UsageStats.json', 'w') as file:
            with statsLock:
                for key in statsDict:
                    if key in statsJson:
                        statsJson[key] += statsDict[key]
                    else:
                        statsJson[key] = statsDict[key]

                statsDict = {}

            json.dump(statsJson, file, indent=4, sort_keys=True)

# Initialize util fields
def InitializeUtils(socket, chan, mongoClient):
    global ws
    global statsLock
    global statsThread
    global colRewards

    ws = socket
    colRewards = mongoClient.QuoteBotDB[chan + "Rewards"]
    colRewards.create_index([("user", pymongo.ASCENDING)])

    with open('UsageStats.json', 'a+') as file:
        try:
            file.seek(0)
            json.load(file)
        except:
            file.truncate(0)
            file.write("{}\n")

    statsLock = threading.Lock()
    statsThread = threading.Thread(target=StoreUsageAsync)
    statsThread.start()
