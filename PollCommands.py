import re
import time

from TwitchWebsocket import TwitchWebsocket

from FlushPrint import ptf, ptfDebug
import RegGroups as groups

class PollCommands():
    def __init__(self, chan, socket):
        self.chan = chan
        self.ws = socket

        self.voteCollection = {}
        self.voters = []
        self.pollRunning = False
        self.pollTimeout = 0

    def EndPoll():
        if not self.pollRunning:
            return

        self.pollRunning = False
        winner = max(self.voteCollection, key=self.voteCollection.get)
        percent = round(self.voteCollection[winner] / len(self.voters) * 100)
        response = f"Poll ended with {len(self.voters)} votes. "

        if self.voteCollection.keys() == {"y", "n"}:
            response += "VoteYea " if winner == "y" else "VoteNay "
        else:
            response += f"Option {winner.upper()} "

        response += f"wins with {percent}% of the vote."

        self.voteCollection = {}
        self.voters = []
        self.pollTimeout = 0
        return response

    def Execute(self, msg):

        # snippet start
        # poll end
        if msg.message.startswith("poll end"):
            if msg.tags['mod'] != '1':
                return f"[{msg.user}]: Regular users can't end a poll"

            if not self.pollRunning:
                return "No poll active."

            return EndPoll()

        if msg.message.startswith("poll"):
            if msg.tags['mod'] != '1':
                return f"[{msg.user}]: Regular users can't start a poll"

            if not self.pollRunning:
                return "Poll already active."

            regMatch = re.match(f"^poll {groups.regNumGroup} {groups.regNumGroup}$", msg.message)

            if regMatch == None:
                regMatch = re.match(f"^poll {groups.regNumGroup}$", msg.message)

                if regMatch == None:
                    return f"[{msg.user}]: The syntax for that command is: poll NUM_MINUTES (NUM_CHOICES)"

                self.voteCollection["y"] = 0
                self.voteCollection["n"] = 0
            else:
                numChoices = regMatch.group(2)

                if numChoices > 10:
                    self.ws.send_message("10 options to vote on is already unreasonable. Let's keep the vote at that.")
                for i in range(numChoices):
                    self.voteCollection[ord("a") + i] = 0

            self.pollTimeout = regMatch.group(1) * 60

            if self.pollTimeout <= 0:
                self.pollTimeout == 60

            while self.pollTimeout >= 30:
                time.sleep(30)

                if not self.pollRunning:
                    return

                self.pollTimeout -= 30

                if self.pollTimeout % 60 == 0:
                    minutes = self.pollTimeout / 60

                    minMsg = "minute" if minutes == 1 else "minutes"
                    self.ws.send_message(f"Don't forget to vote! Only {minutes} {minMsg} remaining.")

                elif self.pollTimeout == 30
                    self.ws.send_message(f"Last chance to vote! Only 30 seconds left!")

            return EndPoll()

        if msg.message.startswith("vote"):
            regMatch = re.match(f"^vote {groups.regTextGroup}$", msg.message)

            if not self.pollRunning:
                return f"[{msg.user}]: Nothing to vote for."

            if regMatch == None:
                return f"[{msg.user}]: The syntax for that command is: vote LETTER"

            if msg.user in self.voters:
                return f"[{msg.user}]: You already voted in this poll."

            vote = regMatch.group(1)[0].lower()

            if vote not in self.voteCollection:
                return f"[{msg.user}]: {vote} is not a valid option for this poll."

            voters.append(msg.user)
            self.voteCollection[vote] += 1

            return f"[{msg.user}]: Your vote for {vote} has been recorded."

