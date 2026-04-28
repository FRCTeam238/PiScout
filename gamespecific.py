import math
from enum import IntEnum, Enum

import server as server
import proprietary as prop

class Boolean(Enum):
    FALSE = 0
    TRUE = 1

class StartingPosition(Enum):
    No = 0
    Depot = 1
    Tower = 2
    OutPost = 3

class AutoHoardPass(Enum):
    No = 0
    Pass = 1
    Hoard = 2
    Both = 3

class CrossField(Enum):
    No = 0
    Trench = 1
    Bump = 2
    Both = 3

class AutoClimb(Enum):
    NoAttempt = 0
    Failed = -1
    Climbed = 15

class ClimbLevel(Enum):
    NoAttempt = 0
    L1 = 10
    L2 = 20
    L3 = 30
    Failed = -1

class ClimbPosition(Enum):
    No = 0
    Middle = 1
    Half = 2
    Nub = 3
    Failed = -1

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

class FuelPickup(Enum):
    No = 0
    OutPost = 1
    Floor = 2
    Both = 3

class BumpTrench(Enum):
    No = 0
    Bump = 1
    Trench = 2
    Both = 3

class PassType(Enum):
    No = 0
    Push = 1
    Shoot = 2
    Both = 3

#The columns in the QRScout CSV
IMPORT_COLUMNS = {
    "EventCode": "",
    "Scouter": "",
    "Match": 0,
    "Robot": "",
    "Team": 0,
    "StartingPosition": "",
    "NoShow": False,
    "AutoFuelPickup": "",
    "AutoFuel": 0,
    "AutoPassed": 0,
    "AutoCrossField": "",
    "AutoClimb": "",
    "AStop": False,
    "TeleFuelPickup": "",
    "TeleScored": 0,
    "TelePassed": 0,
    "TeleShootingLocation": "",
    "OutpostPass": "",
    "TeleCrossField": "",
    "PassingMethod": "",
    "ClimbPosition": "",
    "ClimbLevel": "",
    "DriveQuality": 0,
    "Defense": 0,
    "DefenseSkill": 0,
    "Defended": 0,
    "Card": 0,
    "Disabled": False,
    "Comments": ""
}

# Defines the fields stored in the "Scout" table of the database. This database stores the record for each match scan
SCOUT_FIELDS = {
    "Match": 0,
    "Team": 0,
    "StartingPosition": 0,
    "NoShow": False,
    "AutoFuel": 0,
    "AutoFuelPickupDepot": False,
    "AutoFuelPickupNeutralZ": False,
    "AutoFuelPickupOutPost": False,
    "AutoShootingLocationClose": False,
    "AutoShootingLocationMiddle": False,
    "AutoShootingLocationFar": False,
    "AutoCrossField": 0,
    "AutoClimb": 0,
    "AStop": False,
    "TeleFuelPickupDepot": False,
    "TeleFuelPickupNeutralZ": False,
    "TeleFuelPickupAllianceSide": False,
    "TeleFuelPickupOutPost": False,
    "TeleFuelPickupOpponentSide": False,
    "TeleScored": 0,
    "TelePassed": 0,
    "TeleShootingLocationClose": False,
    "TeleShootingLocationMiddle": False,
    "TeleShootingLocationFar": False,
    "OutpostPass": False,
    "TeleCrossField": 0,
    "Defense": False,
    "Defended": False,
    "Hoard": False,
    "ClimbPosition": 0,
    "ClimbLevel": 0,
    "Card": 0,
    "Disabled": False,
    "Flag": 0,
    "AutoPassed": 0,
    "PassingMethod": 0,
    "DriveQuality": 0,
    "DefenseSkill": 0,
}

# Defines the fields that are stored in the "averages" and similar tables of the database.
# These are the fields displayed on the home page of the website.
# Hidden average fields are only displayed when logged in or on local.
DISPLAY_FIELDS = {
    "Team": 0,
    "Points": 0,
    "AutoPoints": 0,
    "TelePoints": 0,
    "TelePassed": 0,
    "DriveQuality": 0,
    "Defense": 0,
    "Disabled": 0,
}

HIDDEN_DISPLAY_FIELDS = {}

# Define the fields collected from Pit Scouting to display on the team page
PIT_IMPORT_COLUMNS = {
    "EventCode": 0,
    "Scouter": 0,
    "TeamNumber": 0,
    "Batteries": 0,
    "Drivetrain": 0,
    "Weight": 0,
    "Width": 0,
    "FuelPickup": 0,
    "ShootLocation": 0,
    "BumpTrench": 0,
    "ClimbLevel": 0,
    "ClimbPosition": 0,
    "Comments": 0
}

PIT_SCOUT_FIELDS = {
    "TeamNumber": 0,
    "Batteries": 0,
    "Drivetrain": 0,
    "Weight": 0,
    "Width": 0,
    "FuelPickup": 0,
    "ShootLocationClose": 0,
    "ShootLocationMiddle": 0,
    "ShootLocationFar": 0,
    "BumpTrench": 0,
    "ClimbLevel": 0,
    "ClimbPositionHalf": 0,
    "ClimbPositionMiddle": 0,
    "ClimbPositionNub": 0,
}

# Define which pit scout fields to display on alliance page
PIT_DISPLAY_FIELDS = {
    "Drivetrain": 0,
    "ShootLocationClose": 0,
    "ShootLocationMiddle": 0,
    "ShootLocationFar": 0,
    "ClimbLevel": 0,
    "BumpTrench": 0,
}

# Defines the fields displayed on the charts on the team and compare pages
CHART_FIELDS = {
    "match": 0,
    "Points": 0,
    "AutoFuel": 0,
    "AutoClimb": 0,
    "TeleScored": 0,
    "TelePassed": 0,
    "ClimbLevel": 0,
}


class SheetType(IntEnum):
    MATCH = 0
    PIT = 1


def getDisplayFieldCreate():
    retVal = "AutoPoints AS (AutoClimb+AutoFuel) STORED, "
    retVal += "TelePoints AS (TeleScored+ClimbLevel) STORED, "
    retVal += "Points AS (AutoPoints+TelePoints) STORED, "
    return retVal

# Takes an entry from the Scout database table and generates text for display on the team page.
# This page has 4 columns, currently used for auto, 2 teleop, and other (like fouls and end game)
def generateTeamText(e):
    text = {"auto": "", "teleop1": "", "teleop2": "", "other": ""}
    text["auto"] += "Start: " + StartingPosition(e["StartingPosition"]).name + ", "
    text["auto"] += "Scored: " + str(e["AutoFuel"]) + ", " if e["AutoFuel"] else ""
    text["auto"] += "Passed: " + str(e["AutoPassed"]) + ", " if e["AutoPassed"] else ""
    text["auto"] += "Pickup:" if e["AutoFuelPickupDepot"] or e["AutoFuelPickupNeutralZ"] or e["AutoFuelPickupOutPost"] else ""
    text["auto"] += " Depot" if e["AutoFuelPickupDepot"] else ""
    text["auto"] += " NeutralZ" if e["AutoFuelPickupNeutralZ"] else ""
    text["auto"] += " Outpost" if e["AutoFuelPickupOutPost"] else ""
    text["auto"] += ", " if e["AutoFuelPickupDepot"] or e["AutoFuelPickupNeutralZ"] or e["AutoFuelPickupOutPost"] else ""
    text["auto"] += "Cross: " + CrossField(e["AutoCrossField"]).name + ", " if e["AutoCrossField"] else ""
    text["auto"] += AutoClimb(e["AutoClimb"]).name + ", " if e["AutoClimb"] else ""
    text["auto"] = text["auto"][:-2]

    text["teleop1"] += "Scored: " + str(e["TeleScored"]) + ", " if e["TeleScored"] else ""
    text["teleop1"] += "Passed: " + str(e["TelePassed"]) + ", " if e["TelePassed"] else ""
    text["teleop1"] += "Pickup:" if e["TeleFuelPickupDepot"] or e["TeleFuelPickupNeutralZ"] or e[
        "TeleFuelPickupOutPost"] or e["TeleFuelPickupAllianceSide"] or e["TeleFuelPickupOpponentSide"] else ""
    text["teleop1"] += " Depot" if e["TeleFuelPickupDepot"] else ""
    text["teleop1"] += " NeutralZ" if e["TeleFuelPickupNeutralZ"] else ""
    text["teleop1"] += " Outpost" if e["TeleFuelPickupOutPost"] else ""
    text["teleop1"] += " OppSide" if e["TeleFuelPickupOpponentSide"] else ""
    text["teleop1"] += " AllSide" if e["TeleFuelPickupAllianceSide"] else ""
    text["teleop1"] += ", " if e["TeleFuelPickupDepot"] or e["TeleFuelPickupNeutralZ"] or e[
        "TeleFuelPickupOutPost"] or e["TeleFuelPickupAllianceSide"] or e["TeleFuelPickupOpponentSide"] else ""
    text["teleop1"] += "Shoot:" if e["TeleShootingLocationClose"] or e["TeleShootingLocationMiddle"] or e[
        "AutoShootingLocationFar"] else ""
    text["teleop1"] += " Close" if e["TeleShootingLocationClose"] else ""
    text["teleop1"] += " Middle" if e["TeleShootingLocationMiddle"] else ""
    text["teleop1"] += " Far" if e["TeleShootingLocationFar"] else ""
    text["teleop1"] += ", " if e["TeleShootingLocationClose"] or e["TeleShootingLocationMiddle"] or e[
        "TeleShootingLocationFar"] else ""
    text["teleop1"] = text["teleop1"][:-2]

    text["teleop2"] += "Outpost Pass, " if e["OutpostPass"] else ""
    text["teleop2"] += "PassType: " + PassType(e["PassingMethod"]).name + ", " if e["PassingMethod"] else ""
    text["teleop2"] += "Cross: " + CrossField(e["AutoCrossField"]).name + ", " if e["AutoCrossField"] else ""
    text["teleop2"] += ClimbLevel(e["ClimbLevel"]).name + " " if e["ClimbLevel"] else ""
    text["teleop2"] += ClimbPosition(e["ClimbPosition"]).name + ", " if e["ClimbPosition"] else ""
    text["teleop2"] = text["teleop2"][:-2]

    text["other"] += "Drive: " + str(e["DriveQuality"]) + ", " if e["DriveQuality"] else ""
    text["other"] += "Defense, " if e["Defense"] else ""
    text["other"] += "Skill: " + str(e["DefenseSkill"]) + ", " if e["DefenseSkill"] else ""
    text["other"] += "Defended, " if e["Defended"] else ""
    text["other"] += "Disabled, " if e["Disabled"] else ""
    text["other"] += "NoShow, " if e["NoShow"] else ""
    text["other"] += Cards(e["Card"]).name + ", " if e["Card"] else ""
    text["other"] = text["other"][:-2]

    return text


# Takes an entry from the Scout database table and generates chart data.
# The fields in the returned dict must match the CHART_FIELDS definition at the top of this file
def generateChartData(e):
    dp = dict(CHART_FIELDS)
    for key in dp.keys():
        dp[key] += e[key]
    return dp


# Takes a set of team numbers and a string indicating quals or playoffs
# and returns a prediction for the alliances score and whether or not they will achieve any additional ranking points
def predictScore(event, teams, level="quals"):
    fuelTotal = 0
    climbTotal = 0
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


        pointsTotal += entry["Points"]
        fuelTotal += entry["AutoFuel"] + entry["TeleScored"]
        climbTotal += entry["AutoClimb"]+entry["ClimbLevel"]

    retVal = {"score": 0, "RP1": 0, "RP2": 0, "RP3": 0}

    if fuelTotal > 360:
        retVal["RP1"] = 1
    if fuelTotal > 500:
        retVal["RP2"] = 1
    if climbTotal > 50:
        retVal["RP3"] = 1

    retVal["score"] = pointsTotal

    return retVal


# Takes an entry from the Scout table and returns
# whether or not the entry should be flagged based on contradictory data.
def autoFlag(entry):
    return 0

