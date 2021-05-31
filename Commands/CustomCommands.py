import re
import json
import random
import pymongo

from Utilities.FlushPrint import ptf
import Utilities.TwitchUtils as util
import Utilities.RegGroups as groups

class CustomCommands:
    def __init__(self, chan, mongoClient):
        self.colCustomCommands = mongoClient.purebotdb[chan + "CustomCommands"]
        self.colCustomCommands.create_index([("command", pymongo.ASCENDING)])

        self.customCommandList = {}

        for result in self.colCustomCommands.find():
            self.customCommandList[result["command"]] = result["response"]

        self.activeCommands = {
            # snippet start
            # addcom COMMAND TEXT
            # addcom newcom I'm a new command
            # remarks
            # Mod Only.
            "addcom" : self.ExecuteAddCom,

            # snippet start
            # delcom COMMAND
            # delcom newcom
            # remarks
            # Mod Only.
            "delcom" : self.ExecuteDelCom,
        }

        self.addComRegex = re.compile(f"^addcom (.+? \[ARG\]|.+?) {groups.text}$")
        self.delComRegex = re.compile(f"^delcom {groups.text}$")

    def ExecuteAddCom(self, msg):
        if not util.CheckPrivMod(msg.tags):
            return f"[{msg.user}]: Only mods can add commands"

        if (regmatch := self.addComRegex.match(msg.message)) is None:
            return util.GetSyntax(msg.user, "addcom TEXT TEXT")

        command = regmatch.group(1).lower()
        commandText = regmatch.group("text")

        commandExists = False
        if command in self.customCommandList:
            commandExists = True
            self.colCustomCommands.update_one({ "command" : command }, { "$set" : { "response" : commandText } })
        else:
            self.colCustomCommands.insert_one({ "command" : command, "response" : commandText })

        self.customCommandList[command] = commandText

        if command in self.customCommandList:
            if commandExists:
                return f"[{msg.user}]: Command [{command}] was updated"
            else:
                return f"[{msg.user}]: Command [{command}] was added"
        else:
            return f"[{msg.user}]: Could not add/update command"

    def ExecuteDelCom(self, msg):
        if not util.CheckPrivMod(msg.tags):
            return f"[{msg.user}]: Only mods can delete commands"

        if (regmatch := self.delComRegex.match(msg.message)) is None:
            return util.GetSyntax(msg.user, "delcom TEXT")

        command = regmatch.group("text").lower()

        if command not in self.customCommandList:
            return f"[{msg.user}]: {command} is not a command"

        self.colCustomCommands.delete_one({ "command" : command })
        self.customCommandList.pop(command)

        if command not in self.customCommandList:
            return f"[{msg.user}]: Command [{command}] was deleted"
        else:
            return f"[{msg.user}]: Command [{command}] could not be deleted"

    # Generic Commands
    def Execute(self, msg):
        tokens = msg.message.lower().split()

        if tokens[0] in self.customCommandList:
            util.LogReceived(msg.type, msg.user, msg.message, msg.tags, True)

            response = self.customCommandList[tokens[0]]

            if isinstance(response, dict):
                if msg.user in response:
                    response = response[msg.user]
                else:
                    response = response["other"]

            if isinstance(response, list):
                return random.choice(response)

            return response

        elif len(tokens) > 1 and (tokens[0] + " [ARG]") in self.customCommandList:
            util.LogReceived(msg.type, msg.user, msg.message, msg.tags, True)
            response = self.customCommandList[(tokens[0] + " [ARG]")].replace("[ARG]", tokens[1])
            return response

        return None
