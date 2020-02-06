from TwitchWebsocket import TwitchWebsocket
from FlushPrint import ptf

ws = None

# Initialize util fields
def InitializeUtils(socket):
    global ws
    ws = socket

# True if user is a mod or the broadcaster
def CheckPriv(tags):
    return (tags["mod"] == "1" or
            tags["user-id"] == tags["room-id"])

# Log info for an incoming message
def LogReceived(type, user, message, tags):
    ptf(f"Received [{type}] from [{user}]: {message}", time=True)
    ptf(f"With tags: {tags}")

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
