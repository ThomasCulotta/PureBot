import re
import datetime
import json

from TwitchWebsocket import TwitchWebsocket

from FlushPrint import ptf

class CustomCommands:
    def __init__(self, prefix, ws):
        self.prefix = prefix
        self.ws = ws

    def Execute(self, msg):
        ptf("Beginning Custom Command")
        
        ##############################################

        if msg.message.startswith("!addcommand "):
            if msg.tags['mod'] != '1' and msg.user != "doomzero":
                return f"[{msg.user}]: Regular users can't add quotes! Please ask a mod to add it for you."

            regmatch = re.match("^!addcommand (.+? \[ARG\]|.+?) (.+?)$", msg.message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is !addcommand TEXT TEXT"
            newCommand = self.prefix + regmatch.group(1)
            newCommandText = regmatch.group(2)


            with open('CustomCommands.json', 'r') as file:
                customCommandList = json.load(file)

            if newCommand in customCommandList:
                return f"[{msg.user}]: That command ({newCommand}) already exists!"
            
            customCommandList[newCommand] = newCommandText

            with open('CustomCommands.json', 'w') as outfile:
                json.dump(customCommandList, outfile, indent = 2)

            with open('CustomCommands.json', 'r') as file:
                customCommandList = json.load(file)

            if newCommand in customCommandList:
                return f"[{msg.user}]: Command added as [{newCommand}]!"
            else:
                return f"[{msg.user}]: Command not added, for some reason."
            return

        ##############################################

        if msg.message.startswith("!delcommand "):
            if msg.tags['mod'] != '1' and msg.user != "doomzero":
                return f"[{msg.user}]: Regular users can't delete quotes! Please ask a mod to delete it for you."

            regmatch = re.match("^!delcommand (.+?)$", msg.message)
            if regmatch == None:
                return f"[{msg.user}]: The syntax for that command is !delcommand TEXT"
            command = self.prefix + regmatch.group(1)

            with open('CustomCommands.json', 'r') as file:
                customCommandList = json.load(file)

            if command not in customCommandList:
                return f"[{msg.user}]: That command ({command}) is not a command!"
            
            customCommandList.pop(command)

            #write changes to file
            with open('CustomCommands.json', 'w') as outfile:
                json.dump(customCommandList, outfile, indent = 2)

            #reload file's contents
            with open('CustomCommands.json', 'r') as file:
                customCommandList = json.load(file)

            #test if the command has been removed
            if command not in customCommandList:
                return f"[{msg.user}]: That command ({command}) has been removed!"
            else:
                return f"[{msg.user}]: Command not removed, for some reason."
            return

        ##############################################

        #Generic Commands

        if msg.message.startswith("!"):
            tokens = msg.message.lower().split(" ")

            with open('CustomCommands.json', 'r') as file:
                customCommandList = json.load(file)

            if tokens[0] in customCommandList:
                return customCommandList[tokens[0]]
            else:
                if len(tokens) > 1 and (tokens[0] + " [ARG]") in customCommandList:
                    ptf("arg command")
                    response = customCommandList[(tokens[0] + " [ARG]")].replace("[ARG]", tokens[1])   
                    return response
                else:
                    return f"[{msg.user}]: That command does not exist yet!"
