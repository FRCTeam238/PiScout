import csv
import os
import sys
import requests
import serverinfo
import gamespecific as game
from event import CURRENT_EVENT

if len(sys.argv) < 1:
    print("No file provided. Please try again.")

print("Attempting upload to server")
skip = 0
try:  # post it to piscout's ip address
    if os.path.isfile(sys.argv[1]):
        with open(sys.argv[1], "r") as file:

            reader = csv.reader(file)
            for row in reader:
                matchData = dict(game.SCOUT_FIELDS)
                importData = dict(game.IMPORT_FIELDS)
                if skip == 0:
                    skip = 1
                    continue
                for num, key in enumerate(game.SCOUT_FIELDS):
                    if row[num]:
                        matchData[key] = row[num]
                requests.post(
                    "http://127.0.0.1:8000/submit",
                    data={
                        "event": CURRENT_EVENT,
                        "data": str(matchData),
                        "auth": serverinfo.AUTH,
                    },
                )
except:
    print("Upload Failed. Check connectivity and try again.")
