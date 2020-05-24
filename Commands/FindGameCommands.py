import re
import json
import random
import requests
import datetime

import botconfig

from Utilities.FlushPrint import ptf
import Utilities.TwitchUtils as util
import Utilities.RegGroups as groups

class FindGameCommands():
    def __init__(self):
        if not hasattr(botconfig, "igdbAuthKey"):
            ptf("igdbAuthKey not found in botconfig")
        if not hasattr(botconfig, "steamAuthKey"):
            ptf("steamAuthKey not found in botconfig")

        self.igdbHeader = { "user-key" : botconfig.igdbAuthKey,
                            "Accept" : "application/json" }

        params = { "key" : botconfig.steamAuthKey }

        response = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/", params=params)
        data = response.json()

        self.steamApps = {}
        if response.ok:
            self.steamApps = { app["name"] : app["appid"] for app in data["applist"]["apps"] }

        self.activeCommands = {
            "findgame" : self.ExecuteFindGame,
        }

        self.findGameRegex = re.compile(f"^findgame {groups.text}$")

    # snippet start
    # findgame TEXT
    # findgame Halo
    # findgame Silent Hill
    def ExecuteFindGame(self, msg):
        if (regMatch := self.findGameRegex.match(msg.message)) is None:
            return util.GetSyntax(msg.user, "findgame TEXT")

        bodyBase = f"search \"{regMatch.group('text')}\"; limit 3; fields name, url, involved_companies.developer, involved_companies.company.name, first_release_date; where version_parent = null & category = 0"

        # Successive searches for valid dev and date, then just valid date, then anything
        requestBodies = [
            f"{bodyBase} & first_release_date != null & involved_companies.developer = true;",
            f"{bodyBase} & first_release_date != null;",
            f"{bodyBase};",
        ]

        data = []

        for requestBody in requestBodies:
            response = requests.post(f"https://api-v3.igdb.com/games", data=requestBody, headers=self.igdbHeader)
            data = response.json()

            if len(data) != 0:
                break

        if not response.ok or len(data) == 0:
            return f"[{msg.user}]: Game not found"

        data = random.choice(data)

        foundName = data["name"]
        releaseDate = datetime.datetime.utcfromtimestamp(data["first_release_date"]).strftime("%B %d, %Y") if "first_release_date" in data else "[Unknown Date]"
        companyName = next((comp["company"]["name"] for comp in data["involved_companies"] if comp["developer"]), "[Unknown Developer]") if "involved_companies" in data else "[Unknown Developer]"
        gameUrl = data["url"]

        if foundName in self.steamApps:
            gameUrl = f"https://store.steampowered.com/app/{self.steamApps[foundName]}"

        return f"[{msg.user}]: {foundName} by {companyName} first released on {releaseDate} {gameUrl}"
