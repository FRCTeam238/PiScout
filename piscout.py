import ast
import csv

import os
from matplotlib import pyplot as plt
from time import sleep
import ctypes
import requests
from event import CURRENT_EVENT
import gamespecific as game
import serverinfo
import sys

# PiScout is a means of collecting match data in a scantron-like format
# This program was designed to be easily configurable, and new sheets can be made rapidly
# The configuration for the sheets is done in a separate file (gamespecific.py)
# Cory Lynch 2015

SHADED_VAL = 47500
fastMode = False


class PiScout:
    # Firstly, initializes the fields of a PiScout object
    # Then it starts the main loop of PiScout
    # Requires a function "processSheet" which contains the sheet configuration
    # Loops indefinitely and triggers a response whenever a new sheet is added
    def __init__(self):
        try:
            print("PiScout Starting")
            self.sheet = None
            self.display = None
            self.matchData = dict(game.SCOUT_FIELDS)
            self.pitData = dict(game.PIT_SCOUT_FIELDS)
            self.labels = []
            self.type = 0
            self.shift = 0

            # Uses relative path to Sheets subdirectory where scans are stored
            f = set(os.listdir("Sheets"))
            while True:
                sleep(0.25)
                files = set(os.listdir("Sheets"))  # grabs all file names as a set
                added = files - f  # check if any files were added
                for file in added:
                    if ".csv" in file:
                        retval = self.processCSV("Sheets/" + file)
                        # If loading succeeds, process and add to the list of existing files, if the loading has a critical failure, add the file to the list. If the load has a temporary failure, retval is 0 and the file will be reprocessed on the next pass
                        if retval == 1:
                            #game.processSheet(self)
                            f.add(file)
                        elif retval == -1:
                            f.add(file)
        except Exception as e:
            print("Fatal error: ", e.args)
            input("Press any key to exit")

    def processCSV(self, filepath):
        print("Loading a new file: " + filepath)
        if filepath.count("match"):
            with open(filepath, "r") as file:
                if os.path.isfile("queue.txt"):
                    os.remove("queue.txt")
                total = sum(1 for line in file)
                file.seek(0)
                reader = csv.reader(file)
                requests.post(
                     "http://127.0.0.1:8000/submit",
                     data={
                         "event": CURRENT_EVENT,
                         "clear": "match",
                         "auth": serverinfo.AUTH,
                     },
                )
                skip = 0
                print(str(total-1) + " Total records")
                processed = 0
                for row in reader:
                    try:
                        if skip == 0:
                            skip = 1
                            continue
                        processed += 1
                        if((processed-1) %10 == 0):
                            print("Processed " + str(processed-1) + " of " + str(total-1) + " records")
                        matchData = dict(game.SCOUT_FIELDS)
                        comment = ""
                        for num, key in enumerate(game.IMPORT_COLUMNS):
                            if row[num]:
                                if key in ["EventCode", "Scouter", "Robot"]:
                                    continue
                                elif key == "StartingPosition":
                                    matchData[key] = game.StartingPosition[row[num].strip()].value
                                elif key in ["NoShow", "AStop", "OutpostPass", "Disabled", "Defense", "Defended"]:
                                    matchData[key] = game.Boolean[row[num].strip()].value
                                elif key in ["AutoFuelPickup", "AutoShootingLocation", "TeleFuelPickup", "TeleShootingLocation"]:
                                    for value in row[num].split(","):
                                        if value.strip() != "No":
                                            matchData[key + value.strip()] = True
                                elif key == "AutoHoardPass":
                                    matchData[key] = game.AutoHoardPass[row[num].strip()].value
                                elif key in ["AutoCrossField", "TeleCrossField"]:
                                    matchData[key] = game.CrossField[row[num].strip()].value
                                elif key == "AutoClimb":
                                    matchData[key] = game.AutoClimb[row[num].strip()].value
                                elif key == "TeleRobotAction":
                                    for value in row[num].split(","):
                                        if value.strip() != "No":
                                            matchData[value.strip()] = True
                                elif key == "ClimbPosition":
                                    matchData[key] = game.ClimbPosition[row[num].strip()].value
                                elif key == "ClimbLevel":
                                    matchData[key] = game.ClimbLevel[row[num].strip()].value
                                elif key == "Card":
                                    matchData[key] = game.Cards[row[num].strip()].value
                                elif key == "Comments":
                                    comment = row[num]
                                elif key == "PassingMethod":
                                    matchData[key] = game.PassType[row[num].strip()].value
                                else:
                                    matchData[key] = round(float(row[num].strip()))
                        requests.post(
                            "http://127.0.0.1:8000/submit",
                            data={
                                "event": CURRENT_EVENT,
                                "data": str(matchData),
                                "auth": serverinfo.AUTH,
                                "comment": comment
                            },
                        )
                        with open("queue.txt", "a+") as file:
                            file.write(str(matchData) + "\n")
                    except Exception as e:
                        print("Error processing line " + str(processed+1))
                        print (e.args)
        else:
            with open(filepath, "r") as file:
                if os.path.isfile("pitQueue.txt"):
                    os.remove("pitQueue.txt")
                reader = csv.reader(file)
                skip = 0
                for row in reader:
                    if skip == 0:
                        skip = 1
                        continue
                    pitData = dict(game.PIT_SCOUT_FIELDS)
                    comment = ""
                    for num, key in enumerate(game.PIT_IMPORT_COLUMNS):
                        if row[num]:
                            if (key in pitData) or key in ["Comments", "ShootLocation", "ClimbPosition"]:
                                if key == "Drivetrain":
                                    pitData[key] = game.Drivetrain[row[num]].value
                                elif key == "Comments":
                                    comment = row[num]
                                elif key in ["TeamNumber", "Batteries", "Weight", "Width"]:
                                    pitData[key] = row[num]
                                elif key == "FuelPickup":
                                    pitData[key] = game.FuelPickup[row[num]].value
                                elif key == "BumpTrench":
                                    pitData[key] = game.BumpTrench[row[num]].value
                                elif key == "ClimbLevel":
                                    pitData[key] = game.ClimbLevel[row[num]].value
                                elif key in ["ShootLocation", "ClimbPosition"]:
                                    for value in row[num].split(","):
                                        if value.strip() != "No":
                                            pitData[key + value.strip()] = True
                    requests.post(
                        "http://127.0.0.1:8000/submit",
                        data={
                            "event": CURRENT_EVENT,
                            "pitData": str(pitData),
                            "auth": serverinfo.AUTH,
                            "comment": comment
                        },
                    )
                    with open("pitQueue.txt", "a+") as file:
                        file.write(str(pitData) + "\n")
        print("Processing complete")
        return 1

    # Shifts all fields down by amount
    # Useful for when there are two (or more) matches on one sheet of paper
    # After reading the first match, shift down and read again
    def shiftDown(self, amount):
        self.shift = amount

    # Gets the shading value of a grid unit
    # 0 is completely shaded, 102000 is completely unshaded
    def getvalue(self, loc):
        col, row = loc
        box = self.sheet[row * 16 : (row + 1) * 16, col * 16 : (col + 1) * 16]
        return sum(map(sum, box))

    # Parses a location in Letter-Number form and returns a tuple of the pixel coordinates
    def parse(self, loc):
        col, row = loc.upper().split("-")
        return (
            ord(col) - 67 if len(col) == 1 else ord(col[1]) - 41,
            self.shift + int(row) - 3,
        )

    # Adds a data entry into the data dictionary
    def setMatchData(self, name, contents):
        self.matchData[name] = contents

    def setPitData(self, name, contents):
        self.pitData[name] = contents

    def setType(self, type):
        self.type = type

    # Invoked by the "Save Data Offline" button
    # Adds data to a queue to be uploaded online at a later time
    # Also stores in the local database
    def save(self, event):
        print("Queueing match for upload later")
        if self.type == game.SheetType.MATCH:
            with open("queue.txt", "a+") as file:
                file.write(str(self.matchData) + "\n")
            plt.close()
            requests.post(
                "http://127.0.0.1:8000/submit",
                data={
                    "event": CURRENT_EVENT,
                    "data": str(self.matchData),
                    "auth": serverinfo.AUTH,
                },
            )
        elif self.type == game.SheetType.PIT:
            with open("pitQueue.txt", "a+") as file:
                file.write(str(self.pitData) + "\n")
            plt.close()
            requests.post(
                "http://127.0.0.1:8000/submit",
                data={
                    "event": CURRENT_EVENT,
                    "pitData": str(self.pitData),
                    "auth": serverinfo.AUTH,
                },
            )

    # Invoked by the "Upload Data" button
    # Uploads all data (including queue) to the online database
    # Uploads a copy to the local database as backup
    def upload(self, event):
        plt.close()
        print("Attempting upload to server")

        try:  # post it to piscout's ip address
            if self.type == game.SheetType.MATCH:
                requests.post(
                    serverinfo.SERVER + "/submit",
                    data={
                        "event": CURRENT_EVENT,
                        "data": str(self.matchData),
                        "auth": serverinfo.AUTH,
                    },
                )
                print("Uploading this match was successful")
                if os.path.isfile("queue.txt"):
                    try:
                        with open("queue.txt", "r") as file:
                            print("Uploading queued matches")
                            lines = file.readlines()
                            total = len(lines)
                            for num, line in enumerate(lines[:]):
                                print(
                                    "Uploading match "
                                    + str(num + 1)
                                    + "of "
                                    + str(total)
                                )
                                requests.post(
                                    serverinfo.SERVER + "/submit",
                                    data={
                                        "event": CURRENT_EVENT,
                                        "data": line,
                                        "auth": serverinfo.AUTH,
                                    },
                                )
                                lines.remove(line)
                        os.remove("queue.txt")
                    except:
                        with open("queue.txt", "w") as file:
                            file.seek(0)
                            for line in lines:
                                file.write(line)
                            file.truncate()
                            raise
                if os.path.isfile("editQueue.txt"):
                    try:
                        with open("editQueue.txt", "r") as file:
                            print("Edit Queue found, attempting upload")
                            lines = file.readlines()
                            total = len(lines)
                            for num, line in enumerate(lines[:]):
                                print(
                                    "Uploading edit "
                                    + str(num + 1)
                                    + "of "
                                    + str(total)
                                )
                                editData = ast.literal_eval(line)
                                editData['auth'] = serverinfo.AUTH
                                requests.post(
                                    serverinfo.SERVER + "/edit",
                                    data=editData,
                                )
                                lines.remove(line)
                        os.remove("editQueue.txt")
                    except:
                        with open("editQueue.txt", "w") as file:
                            file.seek(0)
                            for line in lines:
                                file.write(line)
                            file.truncate()
                            raise
                if os.path.isfile("deleteQueue.txt"):
                    try:
                        with open("deleteQueue.txt", "r") as file:
                            print("Delete Queue found, attempting upload")
                            lines = file.readlines()
                            total = len(lines)
                            for num, line in enumerate(lines[:]):
                                print(
                                    "Uploading delete "
                                    + str(num + 1)
                                    + " of "
                                    + str(total)
                                )
                                key = ast.literal_eval(line)
                                requests.post(
                                    serverinfo.SERVER + "/delete",
                                    data={
                                        "key": key,
                                        "auth": serverinfo.AUTH
                                    },
                                )
                                lines.remove(line)
                        os.remove("deleteQueue.txt")
                    except:
                        with open("deleteQueue.txt", "w") as file:
                            file.seek(0)
                            for line in lines:
                                file.write(line)
                            file.truncate()
                            raise
                requests.post(
                    "http://127.0.0.1:8000/submit",
                    data={
                        "event": CURRENT_EVENT,
                        "data": str(self.matchData),
                        "auth": serverinfo.AUTH,
                    },
                )
            elif self.type == game.SheetType.PIT:
                requests.post(
                    serverinfo.SERVER + "/submit",
                    data={
                        "event": CURRENT_EVENT,
                        "pitData": str(self.pitData),
                        "auth": serverinfo.AUTH,
                    },
                )
                print("Uploading this team was successful")
                if os.path.isfile("pitQueue.txt"):
                    with open("pitQueue.txt", "r") as file:
                        print("PitScout queue found, uploading")
                        lines = file.readlines()
                        total = len(lines)
                        for num, line in enumerate(lines[:]):
                            print(
                                "Uploading pit team "
                                + str(num + 1)
                                + "of "
                                + str(total)
                            )
                            requests.post(
                                serverinfo.SERVER + "/submit",
                                data={
                                    "event": CURRENT_EVENT,
                                    "pitData": line,
                                    "auth": serverinfo.AUTH,
                                },
                            )
                    os.remove("pitQueue.txt")
                requests.post(
                    "http://127.0.0.1:8000/submit",
                    data={
                        "event": CURRENT_EVENT,
                        "pitData": str(self.pitData),
                        "auth": serverinfo.AUTH,
                    },
                )
        except:
            print("Failed miserably")
            r = self.message(
                "Upload Failed",
                "Upload failed. Retry? Otherwise, data will be stored in the queue for upload later.",
                type=5,
            )
            if r == 4:
                self.upload(event)
            else:
                self.save(event)

    # Displays a message box
    def message(self, title, message, type=0):
        return ctypes.windll.user32.MessageBoxW(0, message, title, type)


if len(sys.argv) > 1:
    if sys.argv[1] == "-fast":
        fastMode = True
        print("Warp Speed!")
PiScout()
