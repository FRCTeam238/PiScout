import math
from enum import IntEnum, Enum

import server as server
import proprietary as prop

class Boolean(Enum):
    FALSE = 0
    TRUE = 1

class StartingPosition(Enum):
    No = 0
    DS1 = 1
    Middle = 2
    DS3 = 3

class CagePosition(Enum):
    No = 0
    Deep = 1
    Shallow = 2

class CoralPickup(Enum):
    No = 0
    Ground = 1
    Cstation = 2
    Both = 3

class Endgame(Enum):
    No = 0
    Park = 2
    Shallow = 6
    Deep = 12
    Fail = -1

class Defense(Enum):
    No = 0
    Defense = 1
    Defended = 2
    Both = 3

class Cards(Enum):
    NoCard = 0
    Yellow = 1
    Red = 2

class Rating(Enum):
    No = 0
    Poor = 1
    OK = 2
    Good = 3

class Drivetrain(Enum):
    No = 0
    Omni = 1
    Swerve = 2
    Tank = 3
    Other = 4

# Defines the fields stored in the "Scout" table of the database. This database stores the record for each match scan
IMPORT_FIELDS = {
    "EventCode": "",
    "Scouter": "",
    "Match": 0,
    "Robot": "",
    "Team": 0,
    "StartingPosition": "",
    "NoShow": Boolean,
    "CagePosition": "",
    "AutoTimer": 0,
    "Leave": False,
    "AutoCoralLvl1": 0,
    "AutoCoralLvl2": 0,
    "AutoCoralLvl3": 0,
    "AutoCoralLvl4": 0,
    "AutoCoralPickup": "",
    "AutoNet": 0,
    "AutoProcessor": 0,
    "AutoDislodge": False,
    "AStop": False,
    "TeleCoralLvl1": 0,
    "TeleCoralLvl2": 0,
    "TeleCoralLvl3": 0,
    "TeleCoralLvl4": 0,
    "TeleCoralPickup": "",
    "TeleNet": 0,
    "TeleProcessor": 0,
    "TeleDislodge": False,
    "CrossedField": False,
    "CageFoul": False,
    "EndgameTime": 0,
    "Endgame": "",
    "OffenseSkill": 0,
    "DefenseDefended": "",
    "DefenseSkill": 0,
    "Card": "",
    "Disabled": False,
    "Coop": False,
    "Comments": ""
}
SCOUT_FIELDS = {
    "Match": 0,
    "Team": 0,
    "StartingPosition": 0,
    "NoShow": 0,
    "CagePosition": 0,
    "AutoTimer": 0,
    "Leave": 0,
    "AutoCoralLvl1": 0,
    "AutoCoralLvl2": 0,
    "AutoCoralLvl3": 0,
    "AutoCoralLvl4": 0,
    "AutoCoralPickup": 0,
    "AutoNet": 0,
    "AutoProcessor": 0,
    "AutoDislodge": 0,
    "AStop": 0,
    "TeleCoralLvl1": 0,
    "TeleCoralLvl2": 0,
    "TeleCoralLvl3": 0,
    "TeleCoralLvl4": 0,
    "TeleCoralPickup": 0,
    "TeleNet": 0,
    "TeleProcessor": 0,
    "TeleDislodge": 0,
    "CrossedField": 0,
    "CageFoul": 0,
    "EndgameTime": 0,
    "Barge": 0,
    "FailedClimb": 0,
    "OffenseSkill": 0,
    "Defense": 0,
    "Defended": 0,
    "DefenseSkill": 0,
    "Card": 0,
    "Disabled": 0,
    "Coop": 0,
    "Flag": 0
}

# Defines the fields that are stored in the "averages" and similar tables of the database.
# These are the fields displayed on the home page of the website.
# Hidden average fields are only displayed when logged in or on local.
DISPLAY_FIELDS = {
    "Team": 0,
    "Points": 0,
    "CoralPoints": 0,
    "AlgaePoints": 0,
    "Barge": 0,
    "AutoCoral": 0,
    "TeleCoral": 0,
    "Defense": 0,
}

HIDDEN_DISPLAY_FIELDS = {}

# Define the fields collected from Pit Scouting to display on the team page
PIT_IMPORT_FIELDS = {
    "EventCode": 0,
    "Scouter": 0,
    "TeamNumber": 0,
    "PitOrganization": 0,
    "WiringQuality": 0,
    "BumperQuality": 0,
    "Batteries": 0,
    "Drivetrain": 0,
    "Weight": 0,
    "Width": 0,
    "Coral": 0,
    "Pickup": 0,
    "L1": 0,
    "L2": 0,
    "L3": 0,
    "L4": 0,
    "Algae": 0,
    "Net": 0,
    "Proc": 0,
    "HP": 0,
    "Shallow": 0,
    "Deep": 0,
    "Comments": 0
}

PIT_SCOUT_FIELDS = {
    "TeamNumber": 0,
    "PitOrganization": 0,
    "WiringQuality": 0,
    "BumperQuality": 0,
    "Batteries": 0,
    "Drivetrain": 0,
    "Weight": 0,
    "Width": 0,
    "Pickup": 0,
    "L1": 0,
    "L2": 0,
    "L3": 0,
    "L4": 0,
    "Net": 0,
    "Proc": 0,
    "HP": 0,
    "Shallow": 0,
    "Deep": 0,
}

# Define which pit scout fields to display on alliance page
PIT_DISPLAY_FIELDS = {
    "L1": 0,
    "L2": 0,
    "L3": 0,
    "L4": 0,
    "Net": 0,
    "Proc": 0,
    "Shallow": 0,
    "Deep": 0,}

# Defines the fields displayed on the charts on the team and compare pages
CHART_FIELDS = {
    "match": 0,
    "Points": 0,
    "AutoCoral": 0,
    "TeleCoral": 0,
    "CoralPoints": 0,
    "AlgaePoints": 0,
    "Barge": 0,
}


class SheetType(IntEnum):
    MATCH = 0
    PIT = 1


def getDisplayFieldCreate():
    retVal = "AlgaePoints AS (2*AutoProcessor+2*TeleProcessor+4*AutoNet+4*TeleNet) STORED, "
    retVal += "AutoCoral AS (AutoCoralLvl1+AutoCoralLvl2+AutoCoralLvl3+AutoCoralLvl4) STORED, "
    retVal += "TeleCoral AS (TeleCoralLvl1+TeleCoralLvl2+TeleCoralLvl3+TeleCoralLvl4) STORED, "
    retVal += "CoralPoints AS (AutoCoralLvl1*3+AutoCoralLvl2*4+AutoCoralLvl3*6+AutoCoralLvl4*7+TeleCoralLvl1*2+TeleCoralLvl2*3+TeleCoralLvl3*4+TeleCoralLvl4*5) STORED, "
    retVal += "Points AS (AlgaePoints+CoralPoints+Barge+3*Leave) STORED, "
    return retVal

# Takes an entry from the Scout database table and generates text for display on the team page.
# This page has 4 columns, currently used for auto, 2 teleop, and other (like fouls and end game)
def generateTeamText(e):
    text = {"auto": "", "teleop1": "", "teleop2": "", "other": ""}
    text["auto"] += StartingPosition(e["StartingPosition"]).name + ", "
    text["auto"] += "L1:" + str(e["AutoCoralLvl1"]) + ", " if e["AutoCoralLvl1"] else ""
    text["auto"] += "L2:" + str(e["AutoCoralLvl2"]) + ", " if e["AutoCoralLvl2"] else ""
    text["auto"] += "L3:" + str(e["AutoCoralLvl3"]) + ", " if e["AutoCoralLvl3"] else ""
    text["auto"] += "L4:" + str(e["AutoCoralLvl4"]) + ", " if e["AutoCoralLvl4"] else ""
    text["auto"] += CoralPickup(e["AutoCoralPickup"]).name + ", " if e["AutoCoralPickup"] else ""
    text["auto"] += "Leave, " if e["Leave"] else ""
    text["auto"] += "Net:" + str(e["AutoNet"]) + ", " if e["AutoNet"] else ""
    text["auto"] += "Proc:" + str(e["AutoProcessor"]) + ", " if e["AutoProcessor"] else ""
    text["auto"] += "Dislodge, " if e["AutoDislodge"] else ""
    text["auto"] += "AStop, " if e["AStop"] else ""
    text["auto"] += str(e["AutoTimer"]) + " Sec, " if e["AutoTimer"] else ""
    text["auto"] = text["auto"][:-2]

    text["teleop1"] += "L1:" + str(e["TeleCoralLvl1"]) + ", " if e["TeleCoralLvl1"] else ""
    text["teleop1"] += "L2:" + str(e["TeleCoralLvl2"]) + ", " if e["TeleCoralLvl2"] else ""
    text["teleop1"] += "L3:" + str(e["TeleCoralLvl3"]) + ", " if e["TeleCoralLvl3"] else ""
    text["teleop1"] += "L4:" + str(e["TeleCoralLvl4"]) + ", " if e["TeleCoralLvl4"] else ""
    text["teleop1"] += CoralPickup(e["TeleCoralPickup"]).name + ", " if e["TeleCoralPickup"] else ""
    text["teleop1"] += "Net:" + str(e["TeleNet"]) + ", " if e["TeleNet"] else ""
    text["teleop1"] += "Proc:" + str(e["TeleProcessor"]) + ", " if e["TeleProcessor"] else ""
    text["teleop1"] += "Dislodge, " if e["TeleDislodge"] else ""
    text["teleop1"] = text["teleop1"][:-2]

    text["teleop2"] += "Cross, " if e["CrossedField"] else ""
    text["teleop2"] += "Failed Climb, " if e["FailedClimb"] else ""
    text["teleop2"] += Endgame(e["Barge"]).name + ", " if e["Barge"] else ""
    text["teleop2"] += str(e["EndgameTime"]) + "Sec, " if e["EndgameTime"] else ""
    text["teleop2"] += "OSkill:" + str(e["OffenseSkill"]) + ", " if e["OffenseSkill"] else ""
    text["teleop2"] += "DSkill:" + str(e["DefenseSkill"]) + ", " if e["DefenseSkill"] else ""
    text["teleop2"] += "Coop, " if e["Coop"] else ""
    text["teleop2"] = text["teleop2"][:-2]

    text["other"] += "Defense, " if e["Defense"] else ""
    text["other"] += "Defended, " if e["Defended"] else ""
    text["other"] += "Disabled, " if e["Disabled"] else ""
    text["other"] += "Coop, " if e["Coop"] else ""
    text["other"] += "NoShow, " if e["NoShow"] else ""
    text["other"] += "CageFoul:" + str(e["CageFoul"]) + ", " if e["CageFoul"] else ""
    text["other"] += Cards(e["Card"]).name + ", " if e["Card"] else ""
    text["other"] = text["other"][:-2]

    return text


# Takes an entry from the Scout database table and generates chart data.
# The fields in the returned dict must match the CHART_FIELDS definition at the top of this file
def generateChartData(e):
    dp = dict(CHART_FIELDS)
    dp["match"] = e["match"]
    dp["Points"] += e["Points"]
    dp["AutoCoral"] += e["AutoCoral"]
    dp["TeleCoral"] += e["TeleCoral"]
    dp["CoralPoints"] += e["CoralPoints"]
    dp["AlgaePoints"] += e["AlgaePoints"]
    dp["Barge"] += e["Barge"]

    return dp


# Takes a set of team numbers and a string indicating quals or playoffs
# and returns a prediction for the alliances score and whether or not they will achieve any additional ranking points
def predictScore(event, teams, level="quals"):
    Leave = 0
    AutoCoral = 0
    L4 = 0
    L3 = 0
    L2 = 0
    L1 = 0
    Net = 0
    Proc = 0
    Barge = 0
    pointsTotal = 0

    for n in teams:
        average = server.getAggregateData(Team=n, Event=event, Mode="Averages")
        assert len(average) < 2
        if len(average):
            entry = average[0]
        else:
            average = server.getAggregateData(Team=n, Mode="Averages")
            assert len(average) < 2
            if len(average):
                entry = average[0]
            else:
                entry = dict(SCOUT_FIELDS)
                entry.update(DISPLAY_FIELDS)
                entry.update(HIDDEN_DISPLAY_FIELDS)


        autoBonus = 2*entry["AutoCoralLvl4"]+2*entry["AutoCoralLvl3"]+entry["AutoCoralLvl2"]+entry["AutoCoralLvl1"]
        L4 += entry["AutoCoralLvl4"] + entry["TeleCoralLvl4"]
        L3 += entry["AutoCoralLvl3"] + entry["TeleCoralLvl3"]
        L2 += entry["AutoCoralLvl2"] + entry["TeleCoralLvl2"]
        L1 += entry["AutoCoralLvl1"] + entry["TeleCoralLvl1"]
        Net += entry["AutoNet"] + entry["TeleNet"]
        Proc += entry["AutoProcessor"] + entry["TeleProcessor"]
        Barge += entry["Barge"]
        pointsTotal += entry["Leave"] * 3 + entry["Barge"] + autoBonus
        if entry["Leave"] > .5:
            Leave += 1
        if entry["AutoCoralLvl4"]+entry["AutoCoralLvl3"]+entry["AutoCoralLvl2"]+entry["AutoCoralLvl1"] > .5:
            AutoCoral += 1

    pointsTotal += 4*min(Net, 9)
    Proc = min(Proc, 9-Net)
    pointsTotal += 2*Proc
    if L4 > 12:
        L4 = 12
        L3 += L4-12
    if L3 > 12:
        L3 = 12
        L2 += L3-12
    if L2 > 12:
        L2 = 12
        L1 += L2-12
    if L1 > 20:
        L1 = 20
    pointsTotal += L4*5 + L3*4 + L2*3 + L1*2

    retVal = {"score": 0, "RP1": 0, "RP2": 0, "RP3": 0}

    if Leave == 3 and AutoCoral:
        retVal["RP1"] = 1
    if Barge >= 12:
        retVal["RP3"] = 1
    Levels = 0
    Levels += 1 if (L4 >= 5) else 0
    Levels += 1 if (L3 >= 5) else 0
    Levels += 1 if (L2 >= 5) else 0
    Levels += 1 if (L1 >= 5) else 0
    Levels += 1 if (Proc >= 2) else 0
    if Levels >= 4:
        retVal["RP2"] = 1

    retVal["score"] = pointsTotal

    return retVal


# Takes an entry from the Scout table and returns
# whether or not the entry should be flagged based on contradictory data.
def autoFlag(entry):
    return 0

