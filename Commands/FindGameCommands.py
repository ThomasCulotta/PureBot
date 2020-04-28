import re
import json
import random
import requests

from Utilities.FlushPrint import ptf
import Utilities.RegGroups as groups

class FindGameCommands():
    def __init__(self, authKey):
        self.igdbHeader = { "user-key" : authKey,
                            "Accept" : "application/json" }

        self.activeCommands = {
            "findgame" : self.ExecuteFindGame,
            #"finddev" : self.ExecuteFindDev
        }

        self.findGameRegex = re.compile(f"^findgame {groups.text}$")
        self.findDevRegex = re.compile(f"^finddev {groups.text}$")
        self.dateRegex = re.compile("(?P<year>\d{4})-(?P<month>\w{3})-(?P<day>\d{2})")

    # snippet start
    # findgame TEXT
    # findgame Halo
    # findgame Silent Hill
    def ExecuteFindGame(self, msg):
        regMatch = self.findGameRegex.match(msg.message)

        if regMatch == None:
            return f"[{msg.user}]: The syntax for that command is: findgame TEXT"

        queryBody = f"fields name, involved_companies.developer, involved_companies.company.name, release_dates.human; where version_parent = null; limit 1; search \"{regMatch.group('text')}\";"

        response = requests.post(f"https://api-v3.igdb.com/games", data=queryBody, headers=self.igdbHeader)

        ptf(response.text)
        data = response.json()

        if len(data) == 0:
            return f"[{msg.user}]: Game not found"

        data = data[0]
        foundName = data["name"]
        dateMatch = self.dateRegex.match(data["release_dates"][0]["human"]) if "release_dates" in data else None
        releaseDate = f"{dateMatch.group('month')} {dateMatch.group('day')}, {dateMatch.group('year')}" if dateMatch != None else "[Unknown Date]"
        companyName = next((comp["company"]["name"] for comp in data["involved_companies"] if comp["developer"]), "[Unknown Developer]") if "involved_companies" in data else "[Unknown Developer]"

        return f"[{msg.user}]: {foundName} by {companyName} first released on {releaseDate}"
