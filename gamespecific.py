import math
from enum import IntEnum

import server as server
import proprietary as prop

# Defines the fields stored in the "Scout" table of the database. This database stores the record for each match scan
SCOUT_FIELDS = {
    "Team": 0,
    "Match": 0,
    "AutoSpeaker": 0,
    "Midfield1": 0,
    "Midfield2": 0,
    "Midfield3": 0,
    "Midfield4": 0,
    "Midfield5": 0,
    "AutoMidfield": 0,
    "Leave": 0,
    "AStop": 0,
    "GroundPickup": 0,
    "SourcePickup": 0,
    "SourceSteal": 0,
    "Disabled": 0,
    "Defense": 0,
    "Defended": 0,
    "Wing": 0,
    "Podium": 0,
    "Subwoofer": 0,
    "TeleSpeaker": 0,
    "TeleAmp": 0,
    "Amplified": 0,
    "Amplification": 0,
    "Coop": 0,
    "OnstageAttempt": 0,
    "Onstage": 0,
    "Trap": 0,
    "HighNotes": 0,
    "Park": 0,
    "Harmony": 0,
    "Replay": 0,
    "Flag": 0,
}

# Defines the fields that are stored in the "averages" and similar tables of the database.
# These are the fields displayed on the home page of the website.
# Hidden average fields are only displayed when logged in or on local.
DISPLAY_FIELDS = {
    "Team": 0,
    "TeleCycles": 0,
    "AutoSpeaker": 0,
    "TeleSpeaker": 0,
    "TeleAmp": 0,
    "Stage": 0,
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
    "FloorPickup": 0,
    "SourcePickup": 0,
    "Harmony": 0,
    "Amp": 0,
    "Speaker": 0,
    "Trap": 0,
    "Podium": 0,
    "AmpZone": 0,
    "UnderStage": 0,
}

# Define which pit scout fields to display on alliance page
PIT_DISPLAY_FIELDS = {"Amp": 0, "Speaker": 0, "SillyWheels": 0, "Swerve": 0, "UnderStage": 0}

# Defines the fields displayed on the charts on the team and compare pages
CHART_FIELDS = {
    "match": 0,
    "AutoSpeaker": 0,
    "TeleCycles": 0,
    "TeleSpeaker": 0,
    "TeleAmp": 0,
    "Stage": 0,
}


class SheetType(IntEnum):
    MATCH = 0
    PIT = 1


def getDisplayFieldCreate():
    retVal = "TeleCycles AS (TeleSpeaker+TeleAmp) STORED, "
    retVal += "Stage AS (3*Onstage+5*Trap+Spotlight+2*Harmony+Park) STORED, "
    retVal += (
        "FirstP AS (TeleCycles*"
        + str(prop.FIRST_CYCLES)
        + "*(1+Defended)*"
        + str(prop.FIRST_DEFENDED) +
        "+Stage*"
        + str(prop.FIRST_STAGE)
        + "+AUTO*"
        + str(prop.FIRST_AUTO)
        + ") STORED, "
    )
    retVal += (
        "SecondP AS (TeleCycles*"
        + str(prop.SECOND_CYCLES)
        + "+Stage*"
        + str(prop.SECOND_STAGE)
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

            scout.setMatchData("AutoSpeaker", scout.countfield("J-10", "O-10", 0))
            midfield1 = scout.boolfield("K-11")
            midfield2 = scout.boolfield("L-11")
            midfield3 = scout.boolfield("M-11")
            midfield4 = scout.boolfield("N-11")
            midfield5 = scout.boolfield("O-11")
            scout.setMatchData("Midfield1", midfield1)
            scout.setMatchData("Midfield2", midfield2)
            scout.setMatchData("Midfield3", midfield3)
            scout.setMatchData("Midfield4", midfield4)
            scout.setMatchData("Midfield5", midfield5)
            scout.setMatchData("AutoMidfield", midfield1+midfield2+midfield3+midfield4+midfield5)

            scout.setMatchData("Leave", scout.boolfield("J-12"))
            scout.setMatchData("AStop", scout.boolfield("J-13"))

            scout.setMatchData("GroundPickup", scout.boolfield("H-16"))
            scout.setMatchData("SourcePickup", scout.boolfield("H-17"))
            scout.setMatchData("SourceSteal", scout.boolfield("H-18"))

            scout.setMatchData("Defense", scout.boolfield("N-16"))
            scout.setMatchData("Defended", scout.boolfield("N-17"))
            scout.setMatchData("Disabled", scout.boolfield("N-18"))

            scout.setMatchData("Wing", scout.boolfield("T-16"))
            scout.setMatchData("Podium", scout.boolfield("T-17"))
            scout.setMatchData("Subwoofer", scout.boolfield("T-18"))

            scout.setMatchData("TeleopSpeaker", scout.countfield("X-10", "AK-10", 0))
            scout.setMatchData("TeleopAmp", scout.countfield("X-11", "AG-11", 0))
            scout.setMatchData("Amplified", scout.countfield("X-12", "AG-12", 0))
            scout.setMatchData("Amplification", scout.boolfield("X-13"))
            scout.setMatchData("Coop", scout.boolfield("X-14"))

            scout.setMatchData("OnstageAttempt", scout.boolfield("AC-16"))
            scout.setMatchData("Onstage", scout.boolfield("AD-16"))
            scout.setMatchData("Trap", scout.countfield("AC-14", "AF-14", 0))
            scout.setMatchData("HighNotes", scout.countfield("AC-15", "AF-15", 0))

            scout.setMatchData("Park", scout.boolfield("AJ-16"))
            scout.setMatchData("Harmony", scout.boolfield("AJ-17"))

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

            scout.setPitData("FloorPickup", scout.boolfield("N-10"))
            scout.setPitData("SourcePickup", scout.boolfield("M-11"))
            scout.setPitData("Harmony", scout.boolfield("N-12"))
            scout.setPitData("Amp", scout.boolfield("N-13"))
            scout.setPitData("Speaker", scout.boolfield("N-14"))
            scout.setPitData("Trap", scout.boolfield("N-15"))
            scout.setPitData("Podium", scout.boolfield("N-16"))
            scout.setPitData("AmpZone", scout.boolfield("N-17"))
            scout.setPitData("UnderStage", scout.boolfield("N-18"))

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
    text["auto"] += "Speaker: " + str(e["AutoSpeaker"]) + ", " if e["AutoSpeaker"] else ""
    text["auto"] += "Midfield: " if e["AutoMidfield"] else ""
    text["auto"] += "1," if e["Midfield1"] else ""
    text["auto"] += "2," if e["Midfield2"] else ""
    text["auto"] += "3," if e["Midfield3"] else ""
    text["auto"] += "4," if e["Midfield4"] else ""
    text["auto"] += "5," if e["Midfield5"] else ""
    text["auto"] += "  " if e["AutoMidfield"] else ""
    text["auto"] += "ASTOP!!!" + ", " if e["AStop"] else ""
    text["auto"] += "Leave" + ", " if e["Leave"] else ""
    text["auto"] = text["auto"][:-2]

    text["teleop1"] += "Speaker: " + str(e["TeleSpeaker"]) + ", " if e["TeleSpeaker"] else ""
    text["teleop1"] += "Amp: " + str(e["TeleAmp"]) + ", " if e["TeleAmp"] else ""
    text["teleop1"] += "Amplified: " + str(e["Amplified"]) + ", " if e["Amplified"] else ""
    text["teleop1"] += "Ground" + ", " if e["GroundPickup"] else ""
    text["teleop1"] += "Source" + ", " if e["SourcePickup"] else ""
    text["teleop1"] += "Wing" + ", " if e["Wing"] else ""
    text["teleop1"] += "Podium" + ", " if e["Podium"] else ""
    text["teleop1"] += "Subwoofer" + ", " if e["Subwoofer"] else ""
    text["teleop1"] = text["teleop1"][:-2]

    text["teleop2"] += "Trap: " + str(e["Trap"]) + ", " if e["Trap"] else ""
    text["teleop2"] += "Onstage" + ", " if e["Onstage"] else ""
    text["teleop2"] += "OnstageAttempt" + ", " if e["OnstageAttempt"] else ""
    text["teleop2"] += "HighNotes: " + str(e["HighNotes"]) + ", " if e["Spotlight"] else ""
    text["teleop2"] += "Park" + ", " if e["Park"] else ""
    text["teleop2"] += "Harmony" + ", " if e["Harmony"] else ""
    text["teleop2"] = text["teleop2"][:-2]

    text["other"] += "Defense, " if e["Defense"] else ""
    text["other"] += "Defended, " if e["Defended"] else ""
    text["other"] += "Disabled, " if e["Disabled"] else ""
    text["other"] += "Coop, " if e["Coop"] else ""
    text["other"] += "Amplification, " if e["Amplification"] else ""
    text["other"] = text["other"][:-2]

    return text


# Takes an entry from the Scout database table and generates chart data.
# The fields in the returned dict must match the CHART_FIELDS definition at the top of this file
def generateChartData(e):
    dp = dict(CHART_FIELDS)
    dp["match"] = e["match"]

    dp["AutoSpeaker"] += e["AutoSpeaker"]
    dp["TeleCycles"] += e["TeleCycles"]
    dp["TeleSpeaker"] += e["TeleSpeaker"]
    dp["TeleAmp"] += e["TeleAmp"]
    dp["Stage"] += e["Stage"]

    return dp


# Takes a set of team numbers and a string indicating quals or playoffs
# and returns a prediction for the alliances score and whether or not they will achieve any additional ranking points
def predictScore(event, teams, level="quals"):
    noteRP = 0
    stageRP = 0
    autoPreload = 0
    autoStaged = 0
    autoMidfield = 0
    maxCycles = 0
    maxAmps = 0
    traps = 0
    onstage = 0

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

        maxCycles += entry["TeleCycles"]
        maxAmps += entry["TeleCycles"] if entry["TeleAmp"] > .5 else 0
        autoPreload += 1 if entry["AutoSpeaker"] > .5 else 0
        autoStaged += max((entry["AutoSpeaker"] - 1 - entry["AutoMidfield"]), 0)
        autoMidfield += entry["AutoMidfield"]
        traps += entry["Trap"]
        onstage += 1 if entry["Onstage"] > .5 else 0
        pointsTotal += entry["Leave"] + 3*entry["Onstage"]+entry["Spotlight"]+2*entry["Harmony"]

    pointsTotal += max(5*traps, 15)
    pointsTotal += max(5*autoPreload, 15)
    pointsTotal += max(5*autoStaged, 15)
    pointsTotal += max(5*autoMidfield, 15)
    amps = math.floor(max(maxCycles/4, maxAmps))
    pointsTotal = amps * 12
    pointsTotal = 2*max(maxCycles-amps*4, 0)
    notes = max(autoPreload, 3)+max(autoStaged, 3)+max(autoMidfield, 3) + maxCycles
    if notes > 18:
        noteRP = 1
    if onstage >= 2:
        if onstage == 3 or traps:
            stageRP = 1


    retVal = {"score": 0, "RP1": 0, "RP2": 0}

    retVal["score"] = pointsTotal
    retVal["RP1"] = noteRP
    retVal["RP2"] = stageRP

    return retVal


# Takes an entry from the Scout table and returns
# whether or not the entry should be flagged based on contradictory data.
def autoFlag(entry):
    return 0

