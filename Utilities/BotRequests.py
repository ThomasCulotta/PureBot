import json
import time
import requests

import botconfig

from Utilities.FlushPrint import ptf, ptfDebug

helixEndpoint  = "https://api.twitch.tv/helix"

clientId = botconfig.clientId
appToken = "invalid"

helixHeader = { "Authorization": f"Bearer {appToken}",
                "Client-ID": clientId }
v5Header = { "Authorization" : f"OAuth {appToken}",
             "Accept" : "application/vnd.twitchtv.v5+json" }

hostName = botconfig.twitchChannel

_lastValidated = 0
_VALIDATE_CACHE_SECONDS = 60

def CheckGetAccessToken():
    try:
        global appToken, _lastValidated

        # Skip validation if we validated recently
        if time.time() - _lastValidated < _VALIDATE_CACHE_SECONDS:
            return

        validateHeader = { "Authorization": f"Bearer {appToken}" }
        response = requests.get("https://id.twitch.tv/oauth2/validate", headers=validateHeader, timeout=10)

        if response.ok:
            _lastValidated = time.time()
            return

        response = requests.post(
            "https://id.twitch.tv/oauth2/token",
            data={
                "client_id": clientId,
                "client_secret": botconfig.clientSecret,
                "grant_type": "client_credentials"
            },
            timeout=10
        )

        if not response.ok:
            ptf("ERROR: Failed to obtain access token from Twitch")
            return

        data = response.json()

        if "access_token" not in data:
            ptf("ERROR: Twitch token response missing access_token")
            return

        appToken = data["access_token"]
        helixHeader["Authorization"] = f"Bearer {appToken}"
        v5Header["Authorization"] = f"OAuth {appToken}"
        _lastValidated = time.time()

    except requests.exceptions.RequestException as e:
        ptf(f"ERROR: CheckGetAccessToken request failed: {e}")

def GetUserId(user=None):
    CheckGetAccessToken()

    if user == None:
        user = hostName

    loginParam = { "login" : user }

    try:
        response = requests.get(f"{helixEndpoint}/users", params=loginParam, headers=helixHeader, timeout=10)
        data = response.json()["data"]
    except (requests.exceptions.RequestException, KeyError, json.JSONDecodeError) as e:
        ptf(f"ERROR: GetUserId failed: {e}")
        return None

    if len(data) == 0:
        return None

    return data[0]["id"]

# TODO: Currently partially using v5 API. Upgrade to Helix API ASAP
def GetGame(user=None):
    CheckGetAccessToken()

    if user == None:
        user = hostName

    loginParam = { "user_login" : user }

    try:
        response = requests.get(f"{helixEndpoint}/streams", params=loginParam, headers=helixHeader, timeout=10)
        streamData = response.json()["data"]
    except (requests.exceptions.RequestException, KeyError, json.JSONDecodeError) as e:
        ptf(f"ERROR: GetGame failed to fetch stream: {e}")
        return None

    if len(streamData) > 0:
        streamData = streamData[0]
    else:
        streamData = None

    if streamData is None or "game_id" not in streamData:
        return None

    gameIdParam = { "id" : streamData["game_id"] }

    try:
        response = requests.get(f"{helixEndpoint}/games", params=gameIdParam, headers=helixHeader, timeout=10)
        gameData = response.json()["data"]
    except (requests.exceptions.RequestException, KeyError, json.JSONDecodeError) as e:
        ptf(f"ERROR: GetGame failed to fetch game: {e}")
        return None

    if len(gameData) == 0:
        return None

    gameData = gameData[0]

    if "name" in gameData:
        return gameData["name"]

    return None

def GetStartTime():
    CheckGetAccessToken()

    loginParam = { "user_login" : hostName }

    try:
        response = requests.get(f"{helixEndpoint}/streams", params=loginParam, headers=helixHeader, timeout=10)
        streamData = response.json()["data"]
    except (requests.exceptions.RequestException, KeyError, json.JSONDecodeError) as e:
        ptf(f"ERROR: GetStartTime failed: {e}")
        return None

    if len(streamData) > 0:
        streamData = streamData[0]

        if "started_at" in streamData:
            return streamData["started_at"][:-1]

    return None
