import re
import time
import threading

from FlushPrint import ptf, ptfDebug
from TwitchUtils import CheckPriv, SendMessage
import RegGroups as groups

class PollCommands():
    def __init__(self, chan):
        self.chan = chan

        self.voteCollection = {}
        self.voters = []
        self.pollRunning = False
        self.pollTimeout = 0
        self.pollThread = None
        self.pollLock = threading.Lock()

        self.activeCommands = {
            "poll",
            "vote",
        }

    def PollAsync(self):
        while self.pollTimeout >= 30:
            time.sleep(30)

            self.pollTimeout -= 30

            if (not self.pollRunning or
                self.pollTimeout < 30):
                break

            if self.pollTimeout % 60 == 0:
                minutes = int(self.pollTimeout / 60)

                minMsg = "minute" if minutes == 1 else "minutes"
                SendMessage(f"Don't forget to vote! Only {minutes} {minMsg} remaining.")

            elif self.pollTimeout == 30:
                SendMessage(f"Last chance to vote! Only 30 seconds left!")

        self.EndPoll()
        return

    def EndPoll(self):
        with self.pollLock:
            if not self.pollRunning:
                return

            self.pollRunning = False

            if len(self.voters) == 0:
                response = "No one voted for the poll. :("
            else:
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

        SendMessage(response)
        return

    def Execute(self, msg):

        # snippet start
        # poll end
        if msg.message.startswith("poll end"):
            if not CheckPriv(msg.tags):
                return f"[{msg.user}]: Regular users can't end a poll"

            if not self.pollRunning:
                return f"[{msg.user}]: No poll active."

            self.EndPoll()
            return

        # snippet start
        # poll NUM_MINUTES (NUM_OPTIONS)
        # poll 2
        # poll 4 3
        # remarks
        # A Yes/No poll is started when NUM_OPTIONS is not provided. NUM_OPTIONS may be 2-10 and will start a poll with A, B, C, etc.
        if msg.message.startswith("poll"):
            if not CheckPriv(msg.tags):
                return f"[{msg.user}]: Regular users can't start a poll"

            if self.pollRunning:
                return f"[{msg.user}]: Poll already active."

            self.pollThread = threading.Thread(target=self.PollAsync)

            regMatch = re.match(f"^poll {groups.num} {groups.num}$", msg.message)
            optionMsg = "Vote "

            if regMatch == None:
                regMatch = re.match(f"^poll {groups.num}$", msg.message)

                if regMatch == None:
                    return f"[{msg.user}]: The syntax for that command is: poll NUM_MINUTES (NUM_CHOICES)"

                self.voteCollection["y"] = 0
                self.voteCollection["n"] = 0

                optionMsg += "Y/N"
            else:
                numChoices = int(regMatch.group(2))

                if numChoices < 2 or numChoices > 10:
                    return f"[{msg.user}]: Number of voting options must be between 2 and 10."

                for i in range(numChoices):
                    self.voteCollection[chr(ord("a") + i)] = 0

                optionMsg += f"A-{max(self.voteCollection.keys()).upper()}"

            self.pollTimeout = int(regMatch.group(1)) * 60

            if self.pollTimeout <= 0:
                self.pollTimeout == 60

            minutes = int(self.pollTimeout / 60)
            minMsg = "minute" if minutes == 1 else "minutes"

            self.pollRunning = True
            self.pollThread.start()
            return f"Poll running for {minutes} {minMsg}. {optionMsg}"

        # snippet start
        # vote LETTER
        # vote y
        if msg.message.startswith("vote"):
            regMatch = re.match(f"^vote {groups.text}$", msg.message)

            if not self.pollRunning:
                return f"[{msg.user}]: Nothing to vote for."

            if regMatch == None:
                return f"[{msg.user}]: The syntax for that command is: vote LETTER"

            if msg.user in self.voters:
                return f"[{msg.user}]: You already voted in this poll."

            vote = regMatch.group(1)[0].lower()

            if vote not in self.voteCollection:
                return f"[{msg.user}]: {vote} is not a valid option for this poll."

            self.voters.append(msg.user)
            self.voteCollection[vote] += 1

            return f"[{msg.user}]: Your vote for {vote.upper()} has been recorded."

