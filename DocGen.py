import os
import sys
import json

botDir = os.path.dirname(os.path.realpath(__file__))
docFile = open(os.path.join(botDir, "Commands_PureSushi.md"), "w")
customCommandsFile = None

docFile.write("# PureSushi Channel Commands\n\n")

for root, dirs, files in os.walk(os.path.join(botDir, "Commands")):
    files.sort()
    for file in files:
        if file.endswith(".py"):
            title = file.rstrip(".py")

            with open(os.path.join(root, file), "r") as file:
                line = file.readline()

                while line:
                    if line.lstrip().startswith("# snippet start"):
                        if title != None:
                            docFile.write(f"---\n## {title}\n\n")
                            title = None

                        line = file.readline().strip()
                        docFile.write(f"### {line[2:]}\n")

                        examples = "```\n"

                        line = file.readline().lstrip()
                        newLine = ""
                        while len(line) > 0 and line[0] == "#" and not line.startswith("# remarks"):
                            examples += newLine + line[2:]
                            line = file.readline().lstrip()
                            newLine = "\n"

                        if len(examples) > 4:
                            docFile.write(examples + "```\n")

                        if line.startswith("# remarks"):
                            docFile.write(f"**Remarks**\n\n")
                            line = file.readline().lstrip()
                            docFile.write(line[2:] + "\n")

                    line = file.readline()

        elif file == "CustomCommands.json":
            customCommandsFile = os.path.join(root, file)

docFile.write("\n")
docFile.write(f"---\n## Other Commands\n\n")

if customCommandsFile != None:
    with open(customCommandsFile, "r") as file:
        commandJson = json.load(file)

    commands = list(commandJson)
    commands.sort()

    for command in commands:
        docFile.write("```\n" + command + "\n```\n")

docFile.write("\n")
docFile.close()
