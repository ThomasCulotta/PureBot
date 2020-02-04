import re
import datetime
import json
import random

from TwitchWebsocket import TwitchWebsocket

from FlushPrint import ptf, ptfDebug
import RegGroups as groups

class UniqueResponseCommands:
    def __init__(self):
        with open('UniqueResponseCommands.json', 'r') as file:
            self.commandList = json.load(file)

    def Execute(self, msg):
        tokens = msg.message.lower().split(" ")
        recvLog = f"{datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S')} | Received [{msg.type}] from [{msg.user}]: {msg.message}"
        tagLog = f"With tags: {msg.tags}"

        if tokens[0] in self.commandList:
            ptf(recvLog)
            ptf(tagLog)

            command = self.commandList[tokens[0]]

            if msg.user in command:
                response = command[msg.user]
            else:
                response = command["other"]

            if isinstance(response, list):
                return random.choice(response)

            return response

        #This return is a failure state
        return None
