import sys
import botconfig

#Function that prints then flushes standard output because sometimes things get stuck apparently
def ptf(str):
    print(str)
    sys.stdout.flush()

# ptfDebug prints only when debugLog is true
if botconfig.debugLog:
    def ptfDebug(str):
        ptf(str)
else:
    def ptfDebug(str):
        pass
