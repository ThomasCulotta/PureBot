import datetime

from Utilities.BotRequests import GetStartTime
from Utilities.FlushPrint import ptf, ptfDebug

class TimeCommands():
    def __init__(self):
        self.activeCommands = {
            "uptime" : self.ExecuteUptime,
        }

    # snippet start
    # uptime
    def ExecuteUptime(self, msg):
        startTimeStr = GetStartTime()

        if startTimeStr == None:
            return f"[{msg.user}]: Uptime is unavailable."

        startTime = datetime.datetime.fromisoformat(startTimeStr)
        currentTime = datetime.datetime.utcnow()
        seconds = (currentTime - startTime).total_seconds()

        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        return f"Stream uptime: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"
