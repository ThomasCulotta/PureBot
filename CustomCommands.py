import re
import datetime
import json
import random

from TwitchWebsocket import TwitchWebsocket

from FlushPrint import ptf, ptfDebug
import RegGroups as groups

class CustomCommands:
    def __init__(self):
        with open('CustomCommands.json', 'r') as file:
            self.customCommandList = json.load(file)

    def Execute(self, msg):
        ptfDebug("Beginning Custom Command")

        # snippet start
        # addcommand COMMAND TEXT
        # addcommand newcom I'm a new command
        if msg.message.startswith("addcommand"):

            if msg.tags['mod'] != '1' and msg.user != "doomzero":
                return f"[{msg.user}]: Regular users can't add commands! Please ask a mod to add it for you."

            regmatch = re.match(f"^addcommand (.+? \[ARG\]|.+?) {groups.regTextGroup}$", msg.message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is: addcommand TEXT TEXT"
            newCommand = regmatch.group(1).lower()
            newCommandText = regmatch.group(2)

            with open('CustomCommands.json', 'r') as file:
                self.customCommandList = json.load(file)

            if newCommand in self.customCommandList:
                return f"[{msg.user}]: That command ({newCommand}) already exists!"

            self.customCommandList[newCommand] = newCommandText

            with open('CustomCommands.json', 'w') as outfile:
                json.dump(self.customCommandList, outfile, indent = 2)

            with open('CustomCommands.json', 'r') as file:
                self.customCommandList = json.load(file)

            if newCommand in self.customCommandList:
                return f"[{msg.user}]: Command added as [{newCommand}]!"
            else:
                return f"[{msg.user}]: Command not added, for some reason."

            #This return is a failure state
            return None

        ##############################################

        # snippet start
        # delcommand COMMAND
        # delcommand newcom
        if msg.message.startswith("delcommand"):

            if msg.tags['mod'] != '1' and msg.user != "doomzero":
                return f"[{msg.user}]: Regular users can't delete commands! Please ask a mod to delete it for you."

            regmatch = re.match(f"^delcommand {groups.regTextGroup}$", msg.message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is delcommand TEXT"
            command = regmatch.group(1).lower()

            with open('CustomCommands.json', 'r') as file:
                self.customCommandList = json.load(file)

            if command not in self.customCommandList:
                return f"[{msg.user}]: That command ({command}) is not a command!"

            self.customCommandList.pop(command)

            #write changes to file
            with open('CustomCommands.json', 'w') as outfile:
                json.dump(self.customCommandList, outfile, indent = 2)

            #reload file's contents
            with open('CustomCommands.json', 'r') as file:
                self.customCommandList = json.load(file)

            #test if the command has been removed
            if command not in self.customCommandList:
                return f"[{msg.user}]: That command ({command}) has been removed!"
            else:
                return f"[{msg.user}]: Command not removed, for some reason."

            #This return is a failure state
            return None

        ##############################################

        #Generic Commands

        tokens = msg.message.lower().split(" ")
        recvLog = f"{datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S')} | Received [{msg.type}] from [{msg.user}]: {msg.message}"
        tagLog = f"With tags: {msg.tags}"

        if tokens[0] in self.customCommandList:
            ptf(recvLog)
            ptf(tagLog)

            response = self.customCommandList[tokens[0]]

            if isinstance(response, list):
                return random.choice(response)

            return response

        elif len(tokens) > 1 and (tokens[0] + " [ARG]") in self.customCommandList:
            ptf(recvLog)
            ptf(tagLog)

            ptfDebug("arg command")
            response = self.customCommandList[(tokens[0] + " [ARG]")].replace("[ARG]", tokens[1])
            return response

        #This return is a failure state
        return None
