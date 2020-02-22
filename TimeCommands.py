import datetime

from BotRequests import GetStartTime
from FlushPrint import ptf, ptfDebug

class TimeCommands():
    def __init__(self):
        self.activeCommands = {
            "uptime",
        }

    def Execute(self, msg):
        if msg.message.startswith("uptime"):
            startTimeStr = GetStartTime()

            if startTimeStr == None:
                return f"[{msg.user}]: Uptime is unavailable."

            startTime = datetime.datetime.fromisoformat(startTimeStr)
            currentTime = datetime.datetime.utcnow()
            seconds = (currentTime - startTime).total_seconds()

            hours, seconds = divmod(seconds, 3600)
            minutes, seconds = divmod(seconds, 60)

            return f"Stream uptime: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"
