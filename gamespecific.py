import numpy as np
import sqlite3 as sql
from enum import IntEnum
import proprietary as prop

#Defines the fields stored in the "Scout" table of the database. This database stores the record for each match scan
SCOUT_FIELDS = {"Team":0, "Match":0, "Sandstorm":0, "HabClimb":0, "SupportClimb":0, "Defense":0, "Defended":0, "H_Ship":0, "H_R1":0, 
                "H_R2":0, "H_R3":0, "C_Ship":0, "C_R1":0, "C_R2":0, "C_R3":0, "Replay":0, "Flag":0}

#Defines the fields that are stored in the "averages" and similar tables of the database. These are the fields displayed on the home page of the website. Hidden average fields are only displayed when logged in or on local.
AVERAGE_FIELDS = {"Team":0, "Cycles":0, "Sandstorm":0, "HabClimb":0, "Cargo":0, "Hatches":0, "HighCargo":0, "HighHatches":0, "Defense":0}
HIDDEN_AVERAGE_FIELDS = {"CycleScore":0, "FirstP":0, "SecondP":0}

#Define the fields collected from Pit Scouting to display on the team page
PIT_SCOUT_FIELDS = {"Team":0, "Weight":0, "PitOrganization":0, "WiringQuality":0, "BumperQuality":0, "Batteries":0, "SillyWheels":0, "Pro775s":0, "Swerve":0, 
                    "Sandstorm2": 0, "ShipCenter":0, "ShipSide":0, "RocketBack":0, "RocketFront":0, "FloorPickup":0, "Cargo":0, "Hatches":0, "RocketLevel":0}

#Defines the fields displayed on the charts on the team and compare pages
CHART_FIELDS = {"match":0, "Sandstorm":0, "HabClimb":0, "Cargo":0, "Hatches":0, "Cycles":0}

class SheetType(IntEnum):
  MATCH = 0
  PIT = 1
        
     
# Main method to process a full-page sheet
# Submits three times, because there are three matches on one sheet
# The sheet is developed in Google Sheets and the coordinates are defined in terms on the row and column numbers from the sheet.
def processSheet(scout):
    for s in (0,16,32):
        #Sets the shift value (used when turning cell coordinates into pixel coordinates)
        scout.shiftDown(s)
        
        type = scout.rangefield('E-5', 0, 1)
        scout.setType(type)
        if(type == SheetType.MATCH):
          #Match scouting sheet
          num1 = scout.rangefield('AB-5', 0, 9)
          num2 = scout.rangefield('AB-6', 0, 9)
          num3 = scout.rangefield('AB-7', 0, 9)
          num4 = scout.rangefield('AB-8', 0, 9)
          scout.setMatchData("Team", 1000*num1 + 100*num2 + 10*num3 + num4)

          match1 = scout.rangefield('J-6', 0, 1)
          match2 = scout.rangefield('J-7', 0, 9)
          match3 = scout.rangefield('J-8', 0, 9)
          scout.setMatchData("Match", 100*match1 + 10*match2 + match3)
          
          scout.setMatchData("Replay", scout.boolfield('S-6'))

          scout.setMatchData("Sandstorm", scout.rangefield('J-12',0,2)*3)
          habClimbLevel = scout.rangefield('J-14', 0, 3)
          scout.setMatchData("HabClimb", habClimbLevel * 3 if habClimbLevel < 3 else 12)
          supportClimbLevel = scout.rangefield('J-15', 0, 3)
          scout.setMatchData("SupportClimb", supportClimbLevel * 3 if supportClimbLevel < 2 else 12)
          
          scout.setMatchData("Defense", scout.boolfield('J-18'))
          
          scout.setMatchData("Defended", scout.boolfield('P-18'))
          
          scout.setMatchData("H_Ship", scout.countfield('V-10', 'AD-10', 0))
          scout.setMatchData("H_R1", scout.countfield('V-11', 'Z-11', 0))
          scout.setMatchData("H_R2", scout.countfield('V-12', 'Z-12', 0))
          scout.setMatchData("H_R3", scout.countfield('V-13', 'Z-13', 0))
          
          scout.setMatchData("C_Ship", scout.countfield('V-15', 'AD-15', 0))
          scout.setMatchData("C_R1", scout.countfield('V-16', 'Z-16', 0))
          scout.setMatchData("C_R2", scout.countfield('V-17', 'Z-17', 0))
          scout.setMatchData("C_R3", scout.countfield('V-18', 'Z-18', 0))
          
          scout.submit()
        elif(type == SheetType.PIT):
          #Pit scouting sheet
          num1 = scout.rangefield('M-5', 0, 9)
          num2 = scout.rangefield('M-6', 0, 9)
          num3 = scout.rangefield('M-7', 0, 9)
          num4 = scout.rangefield('M-8', 0, 9)
          scout.setPitData("Team", 1000*num1 + 100*num2 + 10*num3 + num4)
          
          weight1 = scout.rangefield('AB-5', 0, 1)
          weight2 = scout.rangefield('AB-6', 0, 9)
          weight3 = scout.rangefield('AB-7', 0, 9)
          scout.setPitData("Weight", 100*weight1 + 10*weight2 + weight3)
          
          
          scout.setPitData("Sandstorm2", scout.boolfield('I-11'))
          scout.setPitData("ShipCenter", scout.boolfield('I-12'))
          scout.setPitData("ShipSide", scout.boolfield('I-13'))
          scout.setPitData("RocketBack", scout.boolfield('I-15'))
          scout.setPitData("RocketFront", scout.boolfield('I-16'))
          
          scout.setPitData("SillyWheels", scout.boolfield('V-12'))
          scout.setPitData("Pro775s", scout.boolfield('V-13'))
          scout.setPitData("Swerve", scout.boolfield('V-14'))
          
          scout.setPitData("FloorPickup", scout.boolfield('P-11')) 
          scout.setPitData("Cargo", scout.boolfield('P-12'))
          scout.setPitData("Hatches", scout.boolfield('P-13'))
          rocketLevel = scout.boolfield('P-14') + scout.boolfield('P-15')*2 + scout.boolfield('P-16')*3
          scout.setPitData("RocketLevel", rocketLevel)
          
          scout.setPitData("PitOrganization", scout.rangefield('AF-12', 1, 3))
          scout.setPitData("WiringQuality", scout.rangefield('AF-13', 1, 3))
          scout.setPitData("BumperQuality", scout.rangefield('AF-14', 1, 3))
          scout.setPitData("Batteries", scout.rangefield('AC-16', 1, 7))
          
          scout.submit()   
        
#Takes an entry from the Scout database table and generates text for display on the team page. This page has 4 columns, currently used for auto, 2 teleop, and other (like fouls and end game)
def generateTeamText(e):
    text = {'auto':"", 'teleop1':"", 'teleop2':"", 'other':""}
    text['auto'] += 'Sandstorm: ' + str(e['Sandstorm'])
    
    text['teleop1'] += 'Hatches - ' if (e['H_Ship']+e['H_R1']+e['H_R2']+e['H_R3']) else ''
    text['teleop1'] += 'Ship: ' + str(e['H_Ship']) + ', ' if e['H_Ship'] else ''
    text['teleop1'] += 'R1: ' + str(e['H_R1']) + ', ' if e['H_R1'] else ''
    text['teleop1'] += 'R2: ' + str(e['H_R2']) + ', ' if e['H_R2'] else ''
    text['teleop1'] += 'R3: ' + str(e['H_R3']) + ', ' if e['H_R3'] else ''
    text['teleop1'] = text['teleop1'][:-2]
    
    text['teleop2'] += 'Cargo - ' if (e['C_Ship']+e['C_R1']+e['C_R2']+e['C_R3']) else ''
    text['teleop2'] += 'Ship: ' + str(e['C_Ship']) + ', ' if e['C_Ship'] else ''
    text['teleop2'] += 'R1: ' + str(e['C_R1']) + ', ' if e['C_R1'] else ''
    text['teleop2'] += 'R2: ' + str(e['C_R2']) + ', ' if e['C_R2'] else ''
    text['teleop2'] += 'R3: ' + str(e['C_R3']) + ', ' if e['C_R3'] else ''
    text['teleop2'] = text['teleop2'][:-2]
    
    text['other'] += 'HabClimb: ' + str(e['HabClimb']) + ', ' if e['HabClimb'] else ''
    text['other'] += 'Supported: ' + str(e['SupportClimb']) + ', ' if e['SupportClimb'] else ''
    text['other'] += 'Defense, ' if e['Defense'] else ''
    text['other'] += 'Defended, ' if e['Defended'] else''
    text['other'] = text['other'][:-2]
    
    return text
    
#Takes an entry from the Scout database table and generates chart data. The fields in the returned dict must match the CHART_FIELDS definition at the top of this file
def generateChartData(e):
    dp = dict(CHART_FIELDS)
    dp["match"]= e['match']
    
    dp['Sandstorm'] += e['Sandstorm']
    dp['HabClimb'] += e['HabClimb']
    dp['Hatches'] += e['H_Ship'] + e['H_R1'] + e['H_R2'] + e['H_R3']
    dp['Cargo'] += e['C_Ship'] + e['C_R1'] + e['C_R2'] + e['C_R3']
    dp['Cycles'] += e['H_Ship'] + e['H_R1'] + e['H_R2'] + e['H_R3'] + e['C_Ship'] + e['C_R1'] + e['C_R2'] + e['C_R3']
    
    return dp
    
#Takes a set of team numbers and a string indicating quals or playoffs and returns a prediction for the alliances score and whether or not they will achieve any additional ranking points
def predictScore(datapath, teams, level='quals'):
        conn = sql.connect(datapath)
        conn.row_factory = sql.Row
        cursor = conn.cursor()
        
        rocketRP = 0
        climbRP = 0
        climbTotal = 0
        rocketHatches = 0
        rocketCargo = 0
        
        pointsTotal = 0

        for n in teams:
            average = cursor.execute('SELECT * FROM averages WHERE team=?', (n,)).fetchall()
            assert len(average) < 2
            if len(average):
              entry = average[0]
            else:
              entry = dict(AVERAGE_FIELDS)
              entry.update(HIDDEN_AVERAGE_FIELDS)
            
            pointsTotal += entry['Hatches']*2 + entry['Cargo']*3 + entry['Sandstorm'] + entry['HabClimb']
            rocketHatches += entry['HighHatches']
            rocketCargo += entry['HighCargo']
            
            if(entry['HabClimb'] > 12):
              climbRP = 1
            else:
              climbTotal += entry['HabClimb']
              
        if(rocketHatches > 3 and rocketCargo > 3):
          rocketRP = 1
              
        if (climbTotal > 15):
          climbRP = 1
              
        retVal = {'score': 0, 'RP1': 0, 'RP2': 0}
       
        retVal['score'] = pointsTotal
        retVal['RP1'] = rocketRP
        retVal['RP2'] = climbRP
        
        return retVal

#Takes an entry from the Scout table and returns whether or not the entry should be flagged based on contradictory data.
def autoFlag(entry):
    return 0

#Takes a list of Scout table entries and returns a nested dictionary of the statistical calculations (average, maxes, median, etc.) of each field in the AVERAGE_FIELDS definition
def calcTotals(entries):
    sums = dict(AVERAGE_FIELDS)
    sums.update(HIDDEN_AVERAGE_FIELDS)
    noDefense = dict(AVERAGE_FIELDS)
    noDefense.update(HIDDEN_AVERAGE_FIELDS)
    lastThree = dict(AVERAGE_FIELDS)
    lastThree.update(HIDDEN_AVERAGE_FIELDS)
    noDCount = 0
    lastThreeCount = 0
    for key in sums:
        sums[key] = []
    #For each entry, add components to the running total if appropriate
    for i, e in enumerate(entries):
        sums['Sandstorm'].append(e['Sandstorm'])
        sums['HabClimb'].append(e['HabClimb'] + e['SupportClimb'])
        sums['Cargo'].append(e['C_Ship'] + e['C_R1'] + e['C_R2'] + e['C_R3'])
        sums['Hatches'].append(e['H_Ship'] + e['H_R1'] + e['H_R2'] + e['H_R3'])
        sums['HighCargo'].append(e['C_R2'] + e['C_R3'])
        sums['HighHatches'].append(e['H_R2'] + e['H_R3'])
        sums['Cycles'].append(e['C_Ship'] + e['C_R1'] + e['C_R2'] + e['C_R3'] + e['H_Ship'] + e['H_R1'] + e['H_R2'] + e['H_R3'])
        sums['Defense'].append(e['Defense'])
        sums['CycleScore'].append(0)
        sums['FirstP'].append(0)
        sums['SecondP'].append(0)
        if not e['Defense']:
          noDefense['Sandstorm']+=(e['Sandstorm'])
          noDefense['HabClimb']+=(e['HabClimb'] + e['SupportClimb'])
          noDefense['Cargo']+=(e['C_Ship'] + e['C_R1'] + e['C_R2'] + e['C_R3'])
          noDefense['Hatches']+=(e['H_Ship'] + e['H_R1'] + e['H_R2'] + e['H_R3'])
          noDefense['HighCargo']+=(e['C_R2'] + e['C_R3'])
          noDefense['HighHatches']+=(e['H_R2'] + e['H_R3'])
          noDefense['Cycles']+=(e['C_Ship'] + e['C_R1'] + e['C_R2'] + e['C_R3'] + e['H_Ship'] + e['H_R1'] + e['H_R2'] + e['H_R3'])
          noDefense['Defense']+=(e['Defense'])
          noDCount += 1
        if i < 3:
          lastThree['Sandstorm']+=(e['Sandstorm'])
          lastThree['HabClimb']+=(e['HabClimb'] + e['SupportClimb'])
          lastThree['Cargo']+=(e['C_Ship'] + e['C_R1'] + e['C_R2'] + e['C_R3'])
          lastThree['Hatches']+=(e['H_Ship'] + e['H_R1'] + e['H_R2'] + e['H_R3'])
          lastThree['HighCargo']+=(e['C_R2'] + e['C_R3'])
          lastThree['HighHatches']+=(e['H_R2'] + e['H_R3'])
          lastThree['Cycles']+=(e['C_Ship'] + e['C_R1'] + e['C_R2'] + e['C_R3'] + e['H_Ship'] + e['H_R1'] + e['H_R2'] + e['H_R3'])
          lastThree['Defense']+=(e['Defense'])
          lastThreeCount += 1
    
    #If there is data, average out the last 3 or less matches
    if(lastThreeCount):
        for key,val in lastThree.items():
            lastThree[key] = round(val/lastThreeCount, 2)
          
    #If there were matches where the team didn't play D, average those out
    if(noDCount):
        for key,val in noDefense.items():
            noDefense[key] = round(val/noDCount, 2)
            
    average = dict(AVERAGE_FIELDS)
    median = dict(AVERAGE_FIELDS)
    maxes = dict(AVERAGE_FIELDS)
    trends = dict(AVERAGE_FIELDS)
    for key in sums:
        if key != 'Team':
            average[key] = round(np.mean(sums[key]), 2)
            median[key] = round(np.median(sums[key]), 2)
            maxes[key] = round(np.max(sums[key]), 2)
            trends[key] = round(lastThree[key]-average[key], 2)
    retVal = {'averages':average, 'median':median, 'maxes':maxes, 'noDefense':noDefense, 'lastThree':lastThree, 'trends':trends}
    
    #Calculate Proprietary metrics.
    for key in retVal:
        CycleScore = round((retVal[key]['Hatches']-retVal[key]['HighHatches'])*prop.LOW_HATCHES + retVal[key]['HighHatches']*prop.HIGH_HATCHES + (retVal[key]['Cargo']-retVal[key]['HighCargo'])*prop.LOW_CARGO + retVal[key]['HighCargo']*prop.HIGH_CARGO, 2)
        FirstPick = round((retVal[key]['Hatches']-retVal[key]['HighHatches'])*prop.FIRST_LOW_HATCHES + retVal[key]['HighHatches']*prop.FIRST_HIGH_HATCHES + (retVal[key]['Cargo']-retVal[key]['HighCargo'])*prop.FIRST_LOW_CARGO + retVal[key]['HighCargo']*prop.FIRST_HIGH_CARGO + retVal[key]['Sandstorm']*prop.FIRST_SANDSTORM + retVal[key]['HabClimb']*prop.FIRST_HAB_CLIMB, 2)
        SecondPick = round((retVal[key]['Hatches']-retVal[key]['HighHatches'])*prop.SECOND_LOW_HATCHES + retVal[key]['HighHatches']*prop.SECOND_HIGH_HATCHES + (retVal[key]['Cargo']-retVal[key]['HighCargo'])*prop.SECOND_LOW_CARGO + retVal[key]['HighCargo']*prop.SECOND_HIGH_CARGO + retVal[key]['Sandstorm']*prop.SECOND_SANDSTORM + retVal[key]['HabClimb']*prop.SECOND_HAB_CLIMB + retVal[key]['Defense']*prop.SECOND_DEFENSE, 2)
        
        retVal[key]['CycleScore'] = CycleScore
        retVal[key]['FirstP'] = FirstPick
        retVal[key]['SecondP'] = SecondPick
    
    return retVal
            
        