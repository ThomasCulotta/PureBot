import re
import json
import random
import requests

import botconfig

from Utilities.FlushPrint import ptf
import Utilities.RegGroups as groups

class FindFoodCommands():
    def __init__(self):
        self.header = { "Accept" : "application/json" }

        self.params = { "apiKey" : botconfig.spoonacularAuthKey }

        self.activeCommands = {
            "findfood" : self.ExecuteFindFood,
        }

        self.findFoodRegex = re.compile(f"^findfood {groups.text}$")

    # snippet start
    # findfood TEXT
    # findfood burger
    # findfood chicken alfredo
    def ExecuteFindFood(self, msg):
        regMatch = self.findFoodRegex.match(msg.message)
        ptf("hello")
        if regMatch == None:
            return f"[{msg.user}]: The syntax for that command is: findfood TEXT"

        params = { **self.params,
                   "query" : regMatch.group("text"),
                   "number" : 3 }

        response = requests.get(f"https://api.spoonacular.com/recipes/search", params=params, headers=self.header)
        data = response.json()
        if not response.ok or "results" not in data or len(data["results"]) == 0:
            return f"[{msg.user}]: Recipe not found"

        data = random.choice(data["results"])

        title = data["title"]
        recipeId = data["id"]

        response = requests.get(f"https://api.spoonacular.com/recipes/{recipeId}/information", params=self.params, headers=self.header)
        data = response.json()

        if not response.ok or "sourceUrl" not in data:
            return f"[{msg.user}]: Recipe not found"

        recipeUrl = data["sourceUrl"]

        return f"[{msg.user}]: {title} - {recipeUrl}"
