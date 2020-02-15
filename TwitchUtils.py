import json
import time
import threading

from TwitchWebsocket import TwitchWebsocket
from FlushPrint import ptf

ws = None
statsDict = {}
statsLock = None
statsThread = None

# True if user is a mod or the broadcaster
def CheckPriv(tags):
    return (tags["mod"] == "1" or
            tags["user-id"] == tags["room-id"])

# True if user is a dev
def CheckDev(user):
    return (user == "babotzinc" or
            user == "doomzero")

# Log info for an incoming message
def LogReceived(type, user, message, tags):
    ptf(f"Received [{type}] from [{user}]: {message}", time=True)
    ptf(f"With tags: {tags}")

    token = message.lower().split(" ")[0]
    RecordUsage(token, user)

# Send a message to twitch chat and log
def SendMessage(response, type="PRIVMSG", user=None):
    global ws
    userStr = "" if user == None else f" to [{user}]"

    if response == None:
        ptf(f"No [{type}] message sent{userStr}\n", time=True)
        return

    if (type == "PRIVMSG"):
        ws.send_message(response)
    elif (type == "WHISPER"):
        ws.send_whisper(user, response)

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
                for key, value in statsDict:
                    if key in statsJson:
                        statsJson[key] += statsDict[key]
                    else:
                        statsJson[key] = statsDict[key]

                statsDict = {}

            json.dump(statsJson, file)

# Initialize util fields
def InitializeUtils(socket):
    global ws
    global statsLock
    global statsThread

    ws = socket

    with open('UsageStats.json', 'a') as file:
        pass

    statsLock = threading.Lock()
    statsThread = threading.Thread(target=StoreUsageAsync)
    statsThread.start()
