import re
import json
import random

from Utilities.FlushPrint import ptf, ptfDebug
import Utilities.TwitchUtils as util
import Utilities.RegGroups as groups

class CustomCommands:
    def __init__(self):
        self.commandFile = "Commands/CustomCommands.json"

        with open(self.commandFile, 'r') as file:
            self.customCommandList = json.load(file)

        self.activeCommands = {
            "addcom" : self.ExecuteAddCom,
            "delcom" : self.ExecuteDelCom,
        }

        self.addComRegex = re.compile(f"^addcom (.+? \[ARG\]|.+?) {groups.text}$")
        self.delComRegex = re.compile(f"^delcom {groups.text}$")

    def SaveCommands(self):
        with open(self.commandFile, 'w') as outfile:
            json.dump(self.customCommandList, outfile, indent = 4)

        with open(self.commandFile, 'r') as file:
            self.customCommandList = json.load(file)

    # snippet start
    # addcom COMMAND TEXT
    # addcom newcom I'm a new command
    def ExecuteAddCom(self, msg):
        if not util.CheckPrivMod(msg.tags) and not util.CheckDev():
            return f"[{msg.user}]: Only mods can add commands"

        regmatch = self.addComRegex.match(msg.message)

        if regmatch == None:
            return f"[{msg.user}]: The syntax for that command is: addcom TEXT TEXT"

        command = regmatch.group(1).lower()
        commandText = regmatch.group("text")

        with open(self.commandFile, 'r') as file:
            self.customCommandList = json.load(file)

        commandExists = False
        if command in self.customCommandList:
            commandExists = True

        self.customCommandList[command] = commandText
        self.SaveCommands()

        if command in self.customCommandList:
            if commandExists:
                return f"[{msg.user}]: Command [{command}] was updated"
            else:
                return f"[{msg.user}]: Command [{command}] was added"
        else:
            return f"[{msg.user}]: Could not add/update command"

    # snippet start
    # delcom COMMAND
    # delcom newcom
    def ExecuteDelCom(self, msg):
        if not util.CheckPrivMod(msg.tags) and not util.CheckDev():
            return f"[{msg.user}]: Only mods can delete commands"

        regmatch = self.delComRegex.match(msg.message)

        if regmatch == None:
            return f"[{msg.user}]: The syntax for that command is: delcom TEXT"

        command = regmatch.group("text").lower()

        with open(self.commandFile, 'r') as file:
            self.customCommandList = json.load(file)

        if command not in self.customCommandList:
            return f"[{msg.user}]: {command} is not a command"

        self.customCommandList.pop(command)
        self.SaveCommands()

        if command not in self.customCommandList:
            return f"[{msg.user}]: Command [{command}] was deleted"
        else:
            return f"[{msg.user}]: Command [{command}] could not be deleted"

    # Generic Commands
    def Execute(self, msg):
        ptfDebug("Beginning Custom Command")

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

            ptfDebug("arg command")
            response = self.customCommandList[(tokens[0] + " [ARG]")].replace("[ARG]", tokens[1])
            return response

        return None
