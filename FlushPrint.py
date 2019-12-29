import sys

#Function that prints then flushes standard output because sometimes things get stuck apparently
def ptf(str):
    print(str)
    sys.stdout.flush()
