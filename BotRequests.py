import json
import requests

import botconfig
from FlushPrint import ptf, ptfDebug

helixEndpoint  = "https://api.twitch.tv/helix"
krakenEndpoint = "https://api.twitch.tv/kraken"

clientId = botconfig.clientId
appToken = "invalid"

helixHeader = { "Authorization": f"Bearer {appToken}",
                "Client-ID": clientId }
v5Header = { "Authorization" : f"OAuth {appToken}",
             "Accept" : "application/vnd.twitchtv.v5+json" }

hostName = botconfig.twitchChannel[1:]

def CheckGetAccessToken():
    response = requests.get(f"https://id.twitch.tv/oauth2/validate", headers=v5Header)
    print(response.text)
    if not response.ok:
        response = requests.post(f"https://id.twitch.tv/oauth2/token?client_id={clientId}&client_secret={botconfig.clientSecret}&grant_type=client_credentials")
        data = response.json()

        global appToken
        appToken= data["access_token"]
        helixHeader["Authorization"] = f"Bearer {appToken}"
        v5Header["Authorization"] = f"OAuth {appToken}"

def GetUserId(user=None):
    CheckGetAccessToken()

    if user == None:
        user = hostName

    loginParam = { "login" : user }

    response = requests.get(f"{helixEndpoint}/users", params=loginParam, headers=helixHeader)
    data = response.json()["data"]

    if len(data) == 0:
        return None

    return data[0]["id"]

# TODO: Currently partially using v5 API. Upgrade to Helix API ASAP
def GetGame(user=None):
    CheckGetAccessToken()

    if user == None:
        user = hostName

    loginParam = { "user_login" : user }

    response = requests.get(f"{helixEndpoint}/streams", params=loginParam, headers=helixHeader)
    streamData = response.json()["data"]

    if len(streamData) > 0:
        streamData = streamData[0]

    if "game_id" not in streamData:
        response = requests.get(f"{krakenEndpoint}/channels/{GetUserId(user)}", headers=v5Header)
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

def GetStartTime():
    loginParam = { "user_login" : hostName }

    response = requests.get(f"{helixEndpoint}/streams", params=loginParam, headers=helixHeader)
    streamData = response.json()["data"]

    if len(streamData) > 0:
        streamData = streamData[0]

        if "started_at" in streamData:
            return streamData["started_at"][:-1]

    return None
