from enum import IntEnum

import server as server
import proprietary as prop

# Defines the fields stored in the "Scout" table of the database. This database stores the record for each match scan
SCOUT_FIELDS = {
    "Team": 0,
    "Match": 0,
    "Mobility": 0,
    "AutoChargeAttempt": 0,
    "AutoDocked": 0,
    "AutoEngaged": 0,
    "ChargeAttempt": 0,
    "Docked": 0,
    "Engaged": 0,
    "Park": 0,
    "Disabled": 0,
    "Defense": 0,
    "Defended": 0,
    "LowCube": 0,
    "MidCube": 0,
    "HighCube": 0,
    "AutoLowCube": 0,
    "AutoMidCube": 0,
    "AutoHighCube": 0,
    "LowCone": 0,
    "MidCone": 0,
    "HighCone": 0,
    "AutoLowCone": 0,
    "AutoMidCone": 0,
    "AutoHighCone": 0,
    "MidfieldCone": 0,
    "MidfieldCube": 0,
    "Replay": 0,
    "Flag": 0,
}

# Defines the fields that are stored in the "averages" and similar tables of the database.
# These are the fields displayed on the home page of the website.
# Hidden average fields are only displayed when logged in or on local.
DISPLAY_FIELDS = {
    "Team": 0,
    "Cycles": 0,
    "GridPoints": 0,
    "Cones": 0,
    "Cubes": 0,
    "Auto": 0,
    "ChargeStation": 0,
    "Defense": 0,
}

HIDDEN_DISPLAY_FIELDS = {"FirstP": 0, "SecondP": 0}

# Define the fields collected from Pit Scouting to display on the team page
PIT_SCOUT_FIELDS = {
    "TeamNumber": 0,
    "Weight": 0,
    "PitOrganization": 0,
    "WiringQuality": 0,
    "BumperQuality": 0,
    "Batteries": 0,
    "SillyWheels": 0,
    "Swerve": 0,
    "TripleMech": 0,
    "Cone": 0,
    "Cube": 0,
    "FloorPickup": 0,
    "DoubleSub": 0,
    "Level1": 0,
    "Level2": 0,
    "Level3": 0,
    "Width": 0,
}

# Define which pit scout fields to display on alliance page
PIT_DISPLAY_FIELDS = {"Cone": 0, "Cube": 0, "SillyWheels": 0, "Swerve": 0, "Width": 0}

# Defines the fields displayed on the charts on the team and compare pages
CHART_FIELDS = {
    "match": 0,
    "Auto": 0,
    "ChargeStation": 0,
    "GridPoints": 0,
    "Cycles": 0,
    "Cones": 0,
    "Cubes": 0
}


class SheetType(IntEnum):
    MATCH = 0
    PIT = 1


def getDisplayFieldCreate():
    retVal = "Cones AS (AutoHighCone+HighCone+AutoMidCone+MidCone+AutoLowCone+LowCone) STORED, "
    retVal += "Cubes AS (AutoHighCube+HighCube+AutoMidCube+MidCube+AutoLowCube+LowCube) STORED, "
    retVal += "Cycles AS (Cones+Cubes) STORED, "
    retVal += "GridPoints AS (6*AutoHighCube+6*AutoHighCone+4*AutoMidCube+4*AutoMidCone+3*AutoLowCone+3*AutoLowCube+5*HighCone+5*HighCube+3*MidCone+3*MidCube+2*LowCone+2*LowCube) STORED, "
    retVal += "Auto AS (6*AutoHighCube+6*AutoHighCone+4*AutoMidCube+4*AutoMidCone+3*AutoLowCone+3*AutoLowCube+AutoEngaged+AutoDocked+Mobility) STORED, "
    retVal += "ChargeStation AS (Docked+Engaged) STORED, "
    retVal += (
        "FirstP AS (GridPoints*"
        + str(prop.FIRST_GRID_POINTS)
        + "*(1+Defended)+ChargeStation*"
        + str(prop.FIRST_BRIDGE)
        + ") STORED, "
    )
    retVal += (
        "SecondP AS (GridPoints*"
        + str(prop.SECOND_GRID_POINTS)
        + "*(1+Defended)+ChargeStation*"
        + str(prop.SECOND_BRIDGE)
        + "+Defense*"
        + str(prop.SECOND_DEFENSE)
        + "+Disabled*"
        + str(prop.SECOND_DISABLED)
        + ") STORED, "
    )
    return retVal


# Main method to process a full-page sheet
# Submits three times, because there are three matches on one sheet
# The sheet is developed in Google Sheets and the coordinates are
# defined in terms on the row and column numbers from the sheet.
def processSheet(scout):
    for s in (0, 16, 32):
        # Sets the shift value (used when turning cell coordinates into pixel coordinates)
        scout.shiftDown(s)

        type = scout.rangefield("E-5", 0, 1)
        scout.setType(type)
        if type == SheetType.MATCH:
            # Match scouting sheet
            num1 = scout.rangefield("AB-5", 0, 9)
            num2 = scout.rangefield("AB-6", 0, 9)
            num3 = scout.rangefield("AB-7", 0, 9)
            num4 = scout.rangefield("AB-8", 0, 9)
            scout.setMatchData("Team", 1000 * num1 + 100 * num2 + 10 * num3 + num4)

            match1 = scout.rangefield("J-6", 0, 1)
            match2 = scout.rangefield("J-7", 0, 9)
            match3 = scout.rangefield("J-8", 0, 9)
            scout.setMatchData("Match", 100 * match1 + 10 * match2 + match3)

            scout.setMatchData("Replay", scout.boolfield("S-6"))

            scout.setMatchData("AutoHighCube", scout.countfield("H-10", "K-10", 0))
            scout.setMatchData("AutoHighCone", scout.countfield("H-11", "K-11", 0))
            scout.setMatchData("AutoMidCube", scout.countfield("H-13", "K-13", 0))
            scout.setMatchData("AutoMidCone", scout.countfield("H-14", "K-14", 0))
            scout.setMatchData("AutoLowCube", scout.countfield("H-16", "K-16", 0))
            scout.setMatchData("AutoLowCone", scout.countfield("H-17", "K-17", 0))

            scout.setMatchData("Mobility", scout.boolfield("H-18"))

            scout.setMatchData("AutoEngaged", scout.boolfield("P-12")*12)
            if(not scout.boolfield("P-12")):
                scout.setMatchData("AutoDocked", scout.boolfield("P-11")*8)
                if(not scout.boolfield("P-11")):
                    scout.setMatchData("AutoChargeAttempt", scout.boolfield("P-10"))            

            scout.setMatchData("Engaged", scout.boolfield("Q-12")*10)
            if(not scout.boolfield("Q-12")):
                scout.setMatchData("Docked", scout.boolfield("Q-11")*6)
                if(not scout.boolfield("Q-11")):
                    scout.setMatchData("ChargeAttempt", scout.boolfield("Q-10"))
                    if(not scout.boolfield("Q-10")):
                        scout.setMatchData("Park", scout.boolfield("Q-13"))

            scout.setMatchData("MidfieldCone", scout.countfield("Q-17", "T-17", 0))
            scout.setMatchData("MidfieldCube", scout.countfield("Q-16", "T-16", 0))

            scout.setMatchData("Defense", scout.boolfield("W-10"))
            scout.setMatchData("Defended", scout.boolfield("W-11"))
            scout.setMatchData("Disabled", scout.boolfield("W-12"))

            scout.setMatchData("HighCube", scout.countfield("AB-10", "AK-10", 0))
            scout.setMatchData("HighCone", scout.countfield("AB-11", "AK-11", 0))
            scout.setMatchData("MidCube", scout.countfield("AB-13", "AK-13", 0))
            scout.setMatchData("MidCone", scout.countfield("AB-14", "AK-14", 0))
            scout.setMatchData("LowCube", scout.countfield("AB-16", "AK-16", 0))
            scout.setMatchData("LowCone", scout.countfield("AB-17", "AK-17", 0))

            scout.submit()
        elif type == SheetType.PIT:
            # Pit scouting sheet
            num1 = scout.rangefield("M-5", 0, 9)
            num2 = scout.rangefield("M-6", 0, 9)
            num3 = scout.rangefield("M-7", 0, 9)
            num4 = scout.rangefield("M-8", 0, 9)
            scout.setPitData("TeamNumber", 1000 * num1 + 100 * num2 + 10 * num3 + num4)

            weight1 = scout.rangefield("AB-5", 0, 1)
            weight2 = scout.rangefield("AB-6", 0, 9)
            weight3 = scout.rangefield("AB-7", 0, 9)
            scout.setPitData("Weight", 100 * weight1 + 10 * weight2 + weight3)

            scout.setPitData("TripleMech", scout.boolfield("Q-10"))
            scout.setPitData("Cone", scout.boolfield("Q-11"))
            scout.setPitData("Cube", scout.boolfield("Q-12"))
            scout.setPitData("FloorPickup", scout.boolfield("Q-13"))
            scout.setPitData("DoubleSub", scout.boolfield("Q-14"))
            scout.setPitData("Level1", scout.boolfield("Q-15"))
            scout.setPitData("Level2", scout.boolfield("Q-16"))
            scout.setPitData("Level3", scout.boolfield("Q-17"))

            scout.setPitData("SillyWheels", scout.boolfield("X-14"))
            scout.setPitData("Swerve", scout.boolfield("X-15"))

            scout.setPitData("PitOrganization", scout.rangefield("AF-13", 1, 3))
            scout.setPitData("WiringQuality", scout.rangefield("AF-14", 1, 3))
            scout.setPitData("BumperQuality", scout.rangefield("AF-15", 1, 3))
            scout.setPitData("Batteries", scout.rangefield("AC-17", 1, 7))

            width1 = scout.rangefield("AB-9", 0, 5)
            width2 = scout.rangefield("AB-10", 0, 9)
            scout.setPitData("Width", width1*10+width2)

            scout.submit()

        # Takes an entry from the Scout database table and generates text for display on the team page.
        # This page has 4 columns, currently used for auto, 2 teleop, and other (like fouls and end game)


def generateTeamText(e):
    text = {"auto": "", "teleop1": "", "teleop2": "", "other": ""}
    text["auto"] += "Low △: " + str(e["AutoLowCone"]) + ", " if e["AutoLowCone"] else ""
    text["auto"] += "Low ⬜: " + str(e["AutoLowCube"]) + ", " if e["AutoLowCube"] else ""
    text["auto"] += "Mid △: " + str(e["AutoMidCone"]) + ", " if e["AutoMidCone"] else ""
    text["auto"] += "Mid ⬜: " + str(e["AutoMidCube"]) + ", " if e["AutoMidCube"] else ""
    text["auto"] += "High △: " + str(e["AutoHighCone"]) + ", " if e["AutoHighCone"] else ""
    text["auto"] += "High ⬜: " + str(e["AutoHighCube"]) + ", " if e["AutoHighCube"] else ""
    text["auto"] += "Docked" + ", " if e["AutoDocked"] else ""
    text["auto"] += "Engaged" + ", " if e["AutoEngaged"] else ""
    text["auto"] += "ChargeAttempt" + ", " if e["AutoChargeAttempt"] else ""
    text["auto"] += "Mobility" + ", " if e["Mobility"] else ""
    text["auto"] = text["auto"][:-2]

    text["teleop1"] += "Low △: " + str(e["LowCone"]) + ", " if e["LowCone"] else ""
    text["teleop1"] += "Low ⬜: " + str(e["LowCube"]) + ", " if e["LowCube"] else ""
    text["teleop1"] += "Mid △: " + str(e["MidCone"]) + ", " if e["MidCone"] else ""
    text["teleop1"] += "Mid ⬜: " + str(e["MidCube"]) + ", " if e["MidCube"] else ""
    text["teleop1"] += "High △: " + str(e["HighCone"]) + ", " if e["HighCone"] else ""
    text["teleop1"] += "High ⬜: " + str(e["HighCube"]) + ", " if e["HighCube"] else ""
    text["teleop1"] = text["teleop1"][:-2]

    shorts = e["MidFieldCone"] + e["MidFieldCube"]
    text["teleop2"] += "Short △: " + str(e["MidfieldCone"]) + ", " if e["MidfieldCone"] else ""
    text["teleop2"] += "Short ⬜: " + str(e["MidfieldCube"]) + ", " if e["MidfieldCube"] else ""
    text["teleop2"] += "Docked" + ", " if e["Docked"] else ""
    text["teleop2"] += "Engaged" + ", " if e["Engaged"] else ""
    text["teleop2"] += "ChargeAttempt" + ", " if e["ChargeAttempt"] else ""
    text["teleop2"] = text["teleop2"][:-2]

    text["other"] += "Defense, " if e["Defense"] else ""
    text["other"] += "Defended, " if e["Defended"] else ""
    text["other"] += "Disabled, " if e["Disabled"] else ""
    text["other"] = text["other"][:-2]

    return text


# Takes an entry from the Scout database table and generates chart data.
# The fields in the returned dict must match the CHART_FIELDS definition at the top of this file
def generateChartData(e):
    dp = dict(CHART_FIELDS)
    dp["match"] = e["match"]

    dp["Cones"] += e["Cones"]
    dp["Cubes"] += e["Cubes"]
    dp["Auto"] += e["Auto"]
    dp["GridPoints"] += e["GridPoints"]
    dp["Cycles"] += e["Cycles"]
    dp["ChargeStation"] += e["ChargeStation"]

    return dp


# Takes a set of team numbers and a string indicating quals or playoffs
# and returns a prediction for the alliances score and whether or not they will achieve any additional ranking points
def predictScore(event, teams, level="quals"):
    linkRP = 0
    bridgeRP = 0
    highCones = 0
    highCubes = 0
    midCones = 0
    midCubes = 0
    low = 0
    autoBridge = 0

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

        low += entry["LowCone"] + entry["LowCube"] + entry["AutoLowCone"] + entry["AutoLowCube"]
        highCones += entry["HighCone"] + entry["AutoHighCone"]
        highCubes += entry["HighCube"] + entry["AutoHighCube"]
        midCones += entry["MidCone"] + entry["AutoMidCone"]
        midCubes += entry["MidCube"] + entry["AutoMidCube"]
        if entry["AutoDocked"] > 4 & autoBridge < 8:
            autoBridge = 8
        if entry["AutoEngaged"] > 6:
            autoBridge = 12
        pointsTotal += entry["AutoHighCone"] + entry["AutoHighCube"] + entry["AutoMidCone"] + entry["AutoMidCube"] + entry["AutoLowCone"] + entry["AutoLowCube"]

    if highCones > 6:
        midCones += highCones - 6
        highCones = 6
    if highCubes > 3:
        midCubes += highCubes - 3
        highCubes = 6
    if midCones > 6:
        low += midCones - 6
        midCones = 6
    if midCubes > 6:
        low += midCubes - 6
        midCubes = 6
    if low > 9:
        low = 9
    pointsTotal += highCones*5 + highCubes*5
    pointsTotal += midCones*3 + midCubes*3
    pointsTotal += low*2
    links = min(highCones/2, highCubes)
    links += min(midCones/2, midCubes)
    links += low/3
    pointsTotal += links*5
    pointsTotal += autoBridge
    if links > 3.75:
        linkRP = 1
    if autoBridge:
        bridgeRP = 1

    retVal = {"score": 0, "RP1": 0, "RP2": 0}

    retVal["score"] = pointsTotal
    retVal["RP1"] = bridgeRP
    retVal["RP2"] = linkRP

    return retVal


# Takes an entry from the Scout table and returns
# whether or not the entry should be flagged based on contradictory data.
def autoFlag(entry):
    return 0

