import json
import requests

import botconfig
from FlushPrint import ptf, ptfDebug

helixEndpoint  = "https://api.twitch.tv/helix"
krakenEndpoint = "https://api.twitch.tv/kraken"

# TODO: add Client-ID header once made. Required by April 30, 2020
helixHeader = { "Authorization": "Bearer " + botconfig.oauth.split(':')[1] }
v5Header = { "Authorization" : "OAuth " + botconfig.oauth.split(':')[1],
             "Accept" : "application/vnd.twitchtv.v5+json" }

hostName = botconfig.twitchChannel[1:]

def GetUserId(user=None):
    if user == None:
        user = hostName

    loginParam = { "login" : user }

    response = requests.get(f"{helixEndpoint}/users", params=loginParam, headers=helixHeader)
    data = response.json()["data"]

    if len(data) == 0:
        return None

    return data[0]["id"]

# Remove when Kraken no longer needed
def GetUserIdKraken(user=None):
    if user == None:
        user = hostName

    loginParam = { "login" : user }

    response = requests.get(f"{krakenEndpoint}/users", params=loginParam, headers=v5Header)
    data = response.json()["users"]

    if len(data) == 0:
        return None

    return data[0]["_id"]

# TODO: Currently partially using v5 API. Upgrade to Helix API ASAP
def GetGame(user=None):
    if user == None:
        user = hostName

    loginParam = { "user_login" : user }

    response = requests.get(f"{helixEndpoint}/streams", params=loginParam, headers=helixHeader)
    streamData = response.json()

    if "game_id" not in streamData:
        response = requests.get(f"{krakenEndpoint}/channels/{GetUserIdKraken(user)}", headers=v5Header)
        streamData = response.json()

        if "game" in streamData:
            return streamData["game"]

        return None

    gameIdParam = { "id" : streamData["game_id"] }

    response = requests.get(f"{helixEndpoint}/games", params=gameIdParam, headers=helixHeader)
    gameData = response.json()["data"][0]

    if "name" in gameData:
        return gameData["name"]

    return None
