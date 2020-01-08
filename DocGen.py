import os
import sys
import json

botDir = os.path.dirname(os.path.realpath(__file__))
docFile = open(os.path.join(botDir, "Commands_PureSushi.md"), "w")
docFile.write("**PureSushi Channel Commands**\n")
customCommandsFile = None

for root, dirs, files in os.walk(botDir):
    for file in files:
        if file.endswith(".py"):
            with open(os.path.join(root, file), "r") as file:
                line = file.readline()

                while line:
                    if line.lstrip().startswith("# snippet start"):
                        docFile.write("\n")
                        line = file.readline().lstrip()

                        while len(line) > 0 and line[0] == "#":
                            docFile.write(line[2:])
                            line = file.readline().lstrip()
                    line = file.readline()

        elif file == "CustomCommands.json":
            customCommandsFile = os.path.join(root, file)

if customCommandsFile != None:
    docFile.write("\n")
    with open(customCommandsFile, "r") as file:
        customJson = json.load(file)

    for command in customJson:
        docFile.write(command + "\n")


docFile.write("\n")
docFile.close()
