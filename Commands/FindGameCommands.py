import re
import json
import random
import requests
import datetime

import botconfig

from Utilities.FlushPrint import ptf
import Utilities.RegGroups as groups

class FindGameCommands():
    def __init__(self):
        self.igdbHeader = { "user-key" : botconfig.igdbAuthKey,
                            "Accept" : "application/json" }

        self.activeCommands = {
            "findgame" : self.ExecuteFindGame,
        }

        self.findGameRegex = re.compile(f"^findgame {groups.text}$")

    # snippet start
    # findgame TEXT
    # findgame Halo
    # findgame Silent Hill
    def ExecuteFindGame(self, msg):
        regMatch = self.findGameRegex.match(msg.message)

        if regMatch == None:
            return f"[{msg.user}]: The syntax for that command is: findgame TEXT"

        bodyBase = f"search \"{regMatch.group('text')}\"; limit 5; fields name, involved_companies.developer, involved_companies.company.name, first_release_date; where version_parent = null & category = 0"

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

        return f"[{msg.user}]: {foundName} by {companyName} first released on {releaseDate}"
