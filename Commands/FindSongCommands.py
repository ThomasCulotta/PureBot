import re
import json
import base64
import random
import requests
import datetime

import botconfig

from Utilities.FlushPrint import ptf
import Utilities.TwitchUtils as util
import Utilities.RegGroups as groups

class FindSongCommands():
    def __init__(self):
        if not hasattr(botconfig, "spotifyIdAndSecret"):
            ptf("spotifyIdAndSecret not found in botconfig")

        self.authHeader = { "Authorization" : f"Basic {base64.urlsafe_b64encode(botconfig.spotifyIdAndSecret.encode('utf-8')).decode('utf-8')}" }
        self.authBody = { "grant_type" : "client_credentials" }

        self.spotifyHeader = { "Authorization" : "Bearer [Invalid]",
                               "Accept" : "application/json" }

        self.activeCommands = {
            # snippet start
            # findsong TEXT
            # findsong Piano Man
            # findsong Killer Queen
            "findsong" : self.ExecuteFindSong,
        }

        self.findSongRegex = re.compile(f"^findsong {groups.text}$")

    def CheckGetAccessToken(self):
        response = requests.get(f"https://api.spotify.com/v1/tracks/11dFghVXANMlKmJXsNCbNl", headers=self.spotifyHeader)

        if not response.ok:
            response = requests.post("https://accounts.spotify.com/api/token", headers=self.authHeader, data=self.authBody)
            data = response.json()
            ptf(data)
            self.spotifyHeader["Authorization"] = f"Bearer {data['access_token']}"

    def ExecuteFindSong(self, msg):
        self.CheckGetAccessToken()

        if (regMatch := self.findSongRegex.match(msg.message)) is None:
            return util.GetSyntax(msg.user, "findsong TEXT")

        queryParams = { "q" : "track:" + regMatch.group("text"),
                        "type" : "track",
                        "limit" : 3 }

        response = requests.get(f"https://api.spotify.com/v1/search", params=queryParams, headers=self.spotifyHeader)
        data = response.json()

        if not response.ok or len(data["tracks"]["items"]) == 0:
            return f"[{msg.user}]: Song not found"

        data = random.choice(data["tracks"]["items"])

        foundName = data["name"]
        album = data["album"]["name"]
        artist = data["artists"][0]["name"]

        datePrecision = data["album"]["release_date_precision"]

        releaseDateStr = "on [Unknown Date]"

        if datePrecision == "day":
            releaseDateStr = datetime.datetime.strptime(data["album"]["release_date"], "%Y-%m-%d").strftime("on %B %d, %Y")
        elif datePrecision == "month":
            releaseDateStr = datetime.datetime.strptime(data["album"]["release_date"], "%Y-%m").strftime("in %B %Y")
        else:
            releaseDateStr = "in " + data["album"]["release_date"]

        return f"[{msg.user}]: {foundName} by {artist} on {album} first released {releaseDateStr}"
