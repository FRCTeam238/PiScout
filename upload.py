import ast
import json
import os
import requests
import serverinfo
from event import CURRENT_EVENT

print("Attempting to upload matches...")
if os.path.isfile("queue.txt"):
    try:
        with open("queue.txt", "r") as file:
            print("Uploading matches")
            lines = file.readlines()
            total = len(lines)
            for num, line in enumerate(lines[:]):
                print("Uploading match " + str(num + 1) + " of " + str(total))
                requests.post(
                    serverinfo.SERVER + "/submit",
                    data={"event": CURRENT_EVENT, "data": line, "auth": serverinfo.AUTH},
                )
                lines.remove(line)
        os.remove("queue.txt")
    except:
        print("Failed miserably. Are you connected to the internet?")
        with open("queue.txt", "w") as file:
            file.seek(0)
            for line in lines:
                file.write(line)
            file.truncate()
            raise
else:
    print("The match queue doesn't exist.")

n = 0
if os.path.isfile("pitQueue.txt"):
    try:
        with open("pitQueue.txt", "r") as file:
            print("Uploading pit entries")
            for line in file:
                requests.post(
                    serverinfo.server + "/submit",
                    data={
                        "event": CURRENT_EVENT,
                        "pitData": line,
                        "auth": serverinfo.AUTH,
                    },
                )
                print("Uploaded pit entry number " + str(n))
                n += 1
        os.remove("pitQueue.txt")
    except:
        print("Failed miserably. Are you connected to the internet?")
else:
    print("The pit queue doesn't exist.")
    
n = 0
if os.path.isfile("editQueue.txt"):
    try:
        with open("editQueue.txt", "r") as file:
            print("Uploading edits")
            for line in file:
                editData = ast.literal_eval(line)
                editData['auth'] = serverinfo.AUTH
                requests.post(
                    serverinfo.SERVER + "/edit",
                    data=editData,
                )
                print("Uploaded edit entry number " + str(n))
                n += 1
        os.remove("editQueue.txt")
    except:
        print("Failed miserably. Are you connected to the internet?")
else:
    print("The edit queue doesn't exist.")

n = 0
if os.path.isfile("deleteQueue.txt"):
    try:
        with open("deleteQueue.txt", "r") as file:
            print("Uploading deletes")
            for line in file:
                key = ast.literal_eval(line)
                requests.post(
                    serverinfo.SERVER + "/delete",
                    data={
                        "key": key,
                        "auth": serverinfo.AUTH
                        },
                )
                print("Uploaded delete entry number " + str(n))
                n += 1
        os.remove("deleteQueue.txt")
    except:
        print("Failed miserably. Are you connected to the internet?")
else:
    print("The delete queue doesn't exist.")

print("Finished.")
input("Press Enter to exit")
