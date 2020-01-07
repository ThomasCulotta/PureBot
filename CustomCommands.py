import re
import datetime
import json

from TwitchWebsocket import TwitchWebsocket

from FlushPrint import ptf

class CustomCommands:
    def __init__(self, prefix, ws):
        self.prefix = prefix
        self.ws = ws

        with open('CustomCommands.json', 'r') as file:
            self.self.customCommandList = json.load(file)

    def Execute(self, msg):
        ptf("Beginning Custom Command")

        ##############################################

        message = msg.message[1:]
        if message.startswith("addcommand"):
            if msg.tags['mod'] != '1' and msg.user != "doomzero":
                return f"[{msg.user}]: Regular users can't add commands! Please ask a mod to add it for you."

            regmatch = re.match("^addcommand (.+? \[ARG\]|.+?) (.+?)$", message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is: addcommand TEXT TEXT"
            newCommand = self.prefix + regmatch.group(1)
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
            return

        ##############################################

        if message.startswith("delcommand"):
            if msg.tags['mod'] != '1' and msg.user != "doomzero":
                return f"[{msg.user}]: Regular users can't delete commands! Please ask a mod to delete it for you."

            regmatch = re.match("^delcommand (.+?)$", message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is delcommand TEXT"
            command = self.prefix + regmatch.group(1)

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
            return

        ##############################################

        #Generic Commands

        tokens = message.lower().split(" ")

        if tokens[0] in self.customCommandList:
            return self.customCommandList[tokens[0]]
        else:
            if len(tokens) > 1 and (tokens[0] + " [ARG]") in self.customCommandList:
                ptf("arg command")
                response = self.customCommandList[(tokens[0] + " [ARG]")].replace("[ARG]", tokens[1])
                return response

        return
