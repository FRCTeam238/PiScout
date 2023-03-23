import cherrypy
import sqlite3 as sql
import os
import json
from ast import literal_eval
import requests
import math

import server
from event import CURRENT_EVENT
import gamespecific as game
import serverinfo
import sys
import re
from genshi.template import TemplateLoader
import proprietary as prop

localInstance = False
loader = TemplateLoader(
    os.path.join(os.path.dirname(__file__), "web/templates"), auto_reload=True
)


class ScoutServer(object):
    # Make sure that database for current event exists on startup
    def __init__(self):
        self.database_exists()

    # Home page
    @cherrypy.expose
    def index(self, m="", e=""):
        # Add auth value to session if not present
        sessionCheck()

        # Handle event selection. When the event is changed, a POST request is sent here.
        if e != "":
            cherrypy.session["event"] = e
            if "Referer" in cherrypy.request.headers:
                raise cherrypy.HTTPRedirect(cherrypy.request.headers["Referer"])

        # Handle mode selection. When the mode is changed, a POST request is sent here.
        if m != "":
            cherrypy.session["mode"] = m
            if "Referer" in cherrypy.request.headers:
                raise cherrypy.HTTPRedirect(cherrypy.request.headers["Referer"])

        data = getAggregateData(Event=getEvent())
        if cherrypy.session["mode"] == "Season":
            conn = sql.connect(self.datapath())
            conn.row_factory = sql.Row
            teams = (
                conn.cursor()
                .execute(
                    "SELECT DISTINCT TeamNumber from Participation WHERE EventCode=?",
                    (getEvent(),),
                )
                .fetchall()
            )
            data = []
            for i, team in enumerate(teams):
                averages = getAggregateData(Team=str(team[0]), Mode="Averages")
                if len(averages):
                    data.append(averages[0])

        # Pass off the normal set of columns or columns with the hidden fields depending on authentication
        # if checkAuth(False):
        #    columns = game.DISPLAY_FIELDS
        #else:
        columns = {**game.DISPLAY_FIELDS, **game.HIDDEN_DISPLAY_FIELDS}

        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        eventName = (
            conn.cursor()
            .execute("SELECT Name from Events WHERE EventCode=?", (getEvent(),))
            .fetchall()
        )
        events = conn.cursor().execute("SELECT * from Events").fetchall()
        conn.close()
        tmpl = loader.load("index.xhtml")
        page = tmpl.generate(
            columns=columns,
            title="Home",
            eventName=eventName[0]["Name"],
            session=cherrypy.session,
            data=data,
            events=events,
        )
        return page.render("html", doctype="html")

    # Page for creating picklist
    @cherrypy.expose
    def picklist(self, list="", dnp="", unassigned=""):
        sessionCheck()
        if not checkAuth(False):
            raise cherrypy.HTTPError(
                401, "Not authorized to view picklist. Please log in and try again."
            )

        if checkAuth(True):
            auth = "admin"
        else:
            auth = "user"

        if list:
            conn = sql.connect(self.datapath())
            conn.row_factory = sql.Row
            pattern = re.compile("team\[\]=(\d*)")
            pickList = pattern.findall(list)
            for order, team in enumerate(pickList):
                sqlCommand = "UPDATE Picklist SET list=?, rank=? WHERE TeamNumber=? AND EventCode=?"
                conn.cursor().execute(sqlCommand, ("Pick", order + 1, team, getEvent()))
            conn.commit()
            conn.close()

        if dnp:
            conn = sql.connect(self.datapath())
            conn.row_factory = sql.Row
            pattern = re.compile("team\[\]=(\d*)")
            dnpList = pattern.findall(dnp)
            for order, team in enumerate(dnpList):
                sqlCommand = "UPDATE Picklist SET list=?, rank=? WHERE TeamNumber=? AND EventCode=?"
                conn.cursor().execute(sqlCommand, ("DNP", order + 1, team, getEvent()))
            conn.commit()
            conn.close()

        if unassigned:
            conn = sql.connect(self.datapath())
            conn.row_factory = sql.Row
            pattern = re.compile("team\[\]=(\d*)")
            orderedList = pattern.findall(unassigned)
            for order, team in enumerate(orderedList):
                sqlCommand = "UPDATE Picklist SET list=?, rank=? WHERE TeamNumber=? AND EventCode=?"
                conn.cursor().execute(
                    sqlCommand, ("Unassigned", order + 1, team, getEvent())
                )
            conn.commit()
            conn.close()

        # This section generates the table of averages
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        columns = {**game.DISPLAY_FIELDS, **game.HIDDEN_DISPLAY_FIELDS}

        sqlAvgCommandBase = "SELECT "
        sqlMaxCommandBase = "SELECT "
        for key in columns:
            sqlMaxCommandBase += "MAX(" + key + ") AS " + key + ", "
        for key in columns:
            sqlAvgCommandBase += "round(AVG(" + key + "),2) AS " + key + ", "
        sqlMaxCommandBase = sqlMaxCommandBase[:-2]
        sqlAvgCommandBase = sqlAvgCommandBase[:-2]
        if getMode() == "Variance":
            sqlCommandBase = sqlMaxCommandBase
        else:
            sqlCommandBase = sqlAvgCommandBase
        noDefense = " AND Defense=0" if getMode() == "NoDefense" else ""
        eventString = " AND ScoutRecords.EventCode='" + getEvent() + "'"

        joinString = "ScoutRecords join Picklist on ScoutRecords.Team=Picklist.TeamNumber AND ScoutRecords.EventCode=Picklist.EventCode "
        listString = " AND LIST='Pick'"
        table = (
            " FROM (Select * from (SELECT *, row_number() over (partition by Team order by match desc) as match_rank from "
            + joinString
            + "WHERE Flag=0"
            + eventString
            + listString
            + ") where match_rank <= 3)"
            if getMode() == "Trends"
            else " FROM " + joinString + "WHERE Flag=0" + eventString + listString
        )
        sqlCommand = (
            sqlCommandBase + table + noDefense + " GROUP BY Team ORDER BY Rank ASC"
        )
        pickListData = conn.cursor().execute(sqlCommand).fetchall()
        if getMode() == "Trends":
            avgData = (
                conn.cursor()
                .execute(
                    sqlCommandBase
                    + " FROM ScoutRecords WHERE Flag=0"
                    + eventString
                    + " GROUP BY Team ORDER BY Rank ASC",
                )
                .fetchall()
            )
            latestData = pickListData.copy()
            pickListData = []
            for i, row in enumerate(latestData):
                rowData = dict(columns)
                for key in rowData:
                    if key == "Team":
                        rowData[key] = row[key]
                    else:
                        rowData[key] = round(row[key] - avgData[i][key], 2)
                pickListData.append(rowData)
        if getMode() == "Variance":
            avgData = (
                conn.cursor()
                .execute(
                    sqlAvgCommandBase
                    + " FROM ScoutRecords WHERE Flag=0"
                    + eventString
                    + " GROUP BY Team ORDER BY Rank ASC",
                )
                .fetchall()
            )
            maxData = pickListData.copy()
            picklistData = []
            for i, row in enumerate(maxData):
                rowData = dict(columns)
                for key in rowData:
                    if key == "Team":
                        rowData[key] = row[key]
                    else:
                        rowData[key] = round(row[key] - avgData[i][key], 2)
                pickListData.append(rowData)

        listString = " AND LIST='DNP'"
        table = (
            " FROM (Select * from (SELECT *, row_number() over (partition by Team order by match desc) as match_rank from "
            + joinString
            + "WHERE Flag=0"
            + eventString
            + listString
            + ") where match_rank <= 3)"
            if getMode() == "Trends"
            else " FROM " + joinString + "WHERE Flag=0" + eventString + listString
        )
        sqlCommand = (
            sqlCommandBase + table + noDefense + " GROUP BY Team ORDER BY Rank ASC"
        )
        dnpData = conn.cursor().execute(sqlCommand).fetchall()
        if getMode() == "Trends":
            avgData = (
                conn.cursor()
                .execute(
                    sqlCommandBase
                    + " FROM ScoutRecords WHERE Flag=0"
                    + eventString
                    + " GROUP BY Team ORDER BY Rank ASC",
                )
                .fetchall()
            )
            latestData = dnpData.copy()
            dnpData = []
            for i, row in enumerate(latestData):
                rowData = dict(columns)
                for key in rowData:
                    if key == "Team":
                        rowData[key] = row[key]
                    else:
                        rowData[key] = round(row[key] - avgData[i][key], 2)
                dnpData.append(rowData)
        if getMode() == "Variance":
            avgData = (
                conn.cursor()
                .execute(
                    sqlAvgCommandBase
                    + " FROM ScoutRecords WHERE Flag=0"
                    + eventString
                    + " GROUP BY Team ORDER BY Rank ASC",
                )
                .fetchall()
            )
            maxData = dnpData.copy()
            dnpData = []
            for i, row in enumerate(maxData):
                rowData = dict(columns)
                for key in rowData:
                    if key == "Team":
                        rowData[key] = row[key]
                    else:
                        rowData[key] = round(row[key] - avgData[i][key], 2)
                dnpData.append(rowData)

        listString = " AND LIST='Unassigned'"
        table = (
            " FROM (Select * from (SELECT *, row_number() over (partition by Team order by match desc) as match_rank from "
            + joinString
            + "WHERE Flag=0"
            + eventString
            + listString
            + ") where match_rank <= 3)"
            if getMode() == "Trends"
            else " FROM " + joinString + "WHERE Flag=0" + eventString + listString
        )
        sqlCommand = (
            sqlCommandBase + table + noDefense + " GROUP BY Team ORDER BY Rank ASC"
        )
        teamData = conn.cursor().execute(sqlCommand).fetchall()
        if getMode() == "Trends":
            avgData = (
                conn.cursor()
                .execute(
                    sqlCommandBase
                    + " FROM ScoutRecords WHERE Flag=0"
                    + eventString
                    + " GROUP BY Team ORDER BY Rank ASC",
                )
                .fetchall()
            )
            latestData = teamData.copy()
            teamData = []
            for i, row in enumerate(latestData):
                rowData = dict(columns)
                for key in rowData:
                    if key == "Team":
                        rowData[key] = row[key]
                    else:
                        rowData[key] = round(row[key] - avgData[i][key], 2)
                teamData.append(rowData)
        if getMode() == "Variance":
            avgData = (
                conn.cursor()
                .execute(
                    sqlAvgCommandBase
                    + " FROM ScoutRecords WHERE Flag=0"
                    + eventString
                    + " GROUP BY Team ORDER BY Rank ASC",
                )
                .fetchall()
            )
            maxData = teamData.copy()
            teamData = []
            for i, row in enumerate(maxData):
                rowData = dict(columns)
                for key in rowData:
                    if key == "Team":
                        rowData[key] = row[key]
                    else:
                        rowData[key] = round(row[key] - avgData[i][key], 2)
                teamData.append(rowData)

        events = conn.cursor().execute("SELECT * from Events").fetchall()
        conn.close()
        tmpl = loader.load("picklist.xhtml")
        page = tmpl.generate(
            columns=columns,
            session=cherrypy.session,
            teams=teamData,
            dnp=dnpData,
            picklist=pickListData,
            auth=auth,
            events=events,
        )
        return page.render("html", doctype="html")

    # Page to show result of login attempt
    @cherrypy.expose()
    def login(self, auth=""):
        sessionCheck()
        loginResult = "Login failed! Please check password"
        if auth == serverinfo.AUTH:
            cherrypy.session["auth"] = auth
            loginResult = "Login successful"
        if auth == serverinfo.ADMIN:
            cherrypy.session["admin"] = auth
            cherrypy.session["auth"] = serverinfo.AUTH
            loginResult = "Admin Login successful"

        referrer = ""
        if "Referer" in cherrypy.request.headers:
            referer = cherrypy.request.headers["Referer"]
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        events = conn.cursor().execute("SELECT * from Events").fetchall()
        conn.close()
        tmpl = loader.load("login.xhtml")
        page = tmpl.generate(
            result=loginResult, session=cherrypy.session, referer=referer, events=events
        )
        return page.render("html", doctype="html")

        # Show a detailed summary for a given team

    @cherrypy.expose()
    def team(self, n="238"):
        sessionCheck()
        if not n.isdigit():
            raise cherrypy.HTTPRedirect("/")

        # Grab team data
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()
        entries = cursor.execute(
            "SELECT rowid,* FROM ScoutRecords WHERE Team=? AND EventCode=? ORDER BY Match ASC",
            (n, getEvent()),
        ).fetchall()
        sql_averages = getAggregateData(Team=n, Event=getEvent())
        commentsRow = cursor.execute(
            "SELECT Comments FROM Teams WHERE TeamNumber=?", (n,)
        ).fetchone()
        if commentsRow[0] is not None:
            comments = convertStringToArray(commentsRow[0])
        else:
            comments = []
        sqlCommand = "SELECT "
        for key in game.PIT_SCOUT_FIELDS:
            sqlCommand += key + ", "
        sqlCommand = sqlCommand[:-2]
        sqlCommand += " FROM Teams WHERE TeamNumber=?"
        sql_pit = cursor.execute(sqlCommand, (n,)).fetchall()
        assert len(sql_averages) < 2  # ensure there aren't two entries for one team
        assert len(sql_pit) < 2
        if len(sql_averages):
            averages = sql_averages[0]
        else:
            averages = dict(game.DISPLAY_FIELDS)
            averages.update(game.HIDDEN_DISPLAY_FIELDS)
        if len(sql_pit):
            pit = sql_pit[0]
        else:
            pit = 0

        # If we have less than 4 entries, see if we can grab data from a previous event
        lastEvent = 0
        oldAverages = []
        if len(entries) < 3:
            seasonEntries = cursor.execute(
                "SELECT rowid,* FROM ScoutRecords WHERE Team=? ORDER BY Match DESC",
                (n,),
            ).fetchall()
            if len(seasonEntries) >= 3:
                oldAverages = getAggregateData(Team=n)[0]

        events = conn.cursor().execute("SELECT * from Events").fetchall()
        conn.close()

        # Clear out comments if not logged in
        if not checkAuth(False):
            comments = []

        dataset = []
        tableData = []
        for e in entries:
            # Generate chart data and table text for this match entry
            dp = game.generateChartData(e)
            text = game.generateTeamText(e)
            tableEntry = {}
            tableEntry["Match"] = e["Match"]
            tableEntry["Text"] = text
            tableEntry["Flag"] = e["Flag"]
            tableEntry["FlagAttr"] = [("style", "color: #B20000")] if e["Flag"] else ""
            tableEntry["Key"] = e["ROWID"]
            tableData.append(tableEntry)
            for key, val in dp.items():
                dp[key] = round(val, 2)
            if not e["Flag"]:
                dataset.append(
                    dp
                )  # add it to dataset, which is an array of data that is fed into the graphs
        # dataset.reverse()  # reverse data so that graph is in the correct order

        # Grab the image from the blue alliance
        headers = {
            "X-TBA-Auth-Key": "n8QdCIF7LROZiZFI7ymlX0fshMBL15uAzEkBgtP1JgUpconm2Wf49pjYgbYMstBF"
        }
        m = []
        try:
            # get the picture for a given team
            m = self.get(
                "http://www.thebluealliance.com/api/v3/team/frc{0}/media/2022".format(
                    n
                ),
                params=headers,
            ).json()
            if m.status_code == 400:
                m = []
        except:
            pass  # swallow the error
        image_url = ""
        for media in m:
            # media['type'] == 'instagram-image' does not currently work correctly on TBA
            if media["type"] == "imgur":
                image_url = "https://i.imgur.com/" + media["foreign_key"] + "m.jpg"
                break
            elif media["type"] == "cdphotothread":
                image_url = media["direct_url"]
                break

        if checkAuth(False):
            auth = 1
            columns = {**game.DISPLAY_FIELDS, **game.HIDDEN_DISPLAY_FIELDS}
        else:
            auth = 0
            columns = game.DISPLAY_FIELDS

        tmpl = loader.load("team.xhtml")
        page = tmpl.generate(
            session=cherrypy.session,
            chartData=str(dataset).replace("'", '"'),
            image=image_url,
            auth=auth,
            old_averages=oldAverages,
            pitColumns=game.PIT_SCOUT_FIELDS,
            pitScout=pit,
            columns=columns,
            averages=averages,
            comments=comments,
            chartFields=game.CHART_FIELDS,
            matches=tableData,
            events=events,
        )
        return page.render("html", doctype="html")

    # Called to toggle flag on a data entry. Also does a recalc to add/remove entry from stats
    @cherrypy.expose()
    def flag(self, num="", match="", flagval=0):
        sessionCheck()
        if not checkAuth(True):
            raise cherrypy.HTTPError(
                401, "Not authorized to flag match data. Please log in and try again"
            )
        if not (num.isdigit() and match.isdigit()):
            raise cherrypy.HTTPError(400, "Team and match must be numeric")
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ScoutRecords SET Flag=? WHERE Team=? AND Match=? AND EventCode=?",
            (int(not int(flagval)), num, match, getEvent()),
        )
        conn.commit()
        conn.close()
        return ""

    # Input interface to choose teams to compare
    @cherrypy.expose()
    def compareTeams(self):
        sessionCheck()
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        events = conn.cursor().execute("SELECT * from Events").fetchall()
        conn.close()
        tmpl = loader.load("compareTeams.xhtml")
        page = tmpl.generate(session=cherrypy.session, events=events)
        return page.render("html", doctype="html")

    # Input interface to choose alliances to compare
    @cherrypy.expose
    def compareAlliances(self):
        sessionCheck()
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        events = conn.cursor().execute("SELECT * from Events").fetchall()
        conn.close()
        tmpl = loader.load("compareAlliances.xhtml")
        page = tmpl.generate(session=cherrypy.session, events=events)
        return page.render("html", doctype="html")

    # Output for team comparison
    @cherrypy.expose()
    def teams(self, n1="", n2="", n3="", n4="", stat1="", stat2=""):
        sessionCheck()
        nums = [n1, n2, n3, n4]
        nums = [i for i in nums if i != ""]
        if stat2 == "none":
            stat2 = ""
        if not stat1:
            stat1 = list(game.CHART_FIELDS)[1]

        averages = []
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()
        output = "<div>"

        stats_data = []
        # Grab data for each team, and generate a statbox
        for index, n in enumerate(nums):
            if not n:
                continue
            if not n.isdigit():
                raise cherrypy.HTTPError(400, "You fool! Enter NUMBERS, not letters.")
            average = getAggregateData(Team=n, Event=getEvent())
            assert len(average) < 2
            if len(average):
                entry = average[0]
            else:
                entry = dict(game.DISPLAY_FIELDS)
                entry.update(game.HIDDEN_DISPLAY_FIELDS)
            stats_data.append(entry)

        dataset = []
        # For each team, grab each match entry and generate chart data, then add them to the graph
        for idx, n in enumerate(nums):
            if not n:
                continue
            entries = cursor.execute(
                "SELECT * FROM ScoutRecords WHERE Team=? AND EventCode=? ORDER BY Match ASC",
                (n, getEvent()),
            ).fetchall()

            for index, e in enumerate(entries):
                if not isinstance(e, tuple):
                    dp = game.generateChartData(e)

                    for key, val in dp.items():
                        dp[key] = round(val, 2)
                    if not e["Flag"]:
                        if len(dataset) < (index + 1):
                            if stat2:
                                dataPoint = {
                                    "match": (index + 1),
                                    "team" + n + "stat1": dp[stat1],
                                    "team" + n + "stat2": dp[stat2],
                                }
                            else:
                                dataPoint = {
                                    "match": (index + 1),
                                    "team" + n + "stat1": dp[stat1],
                                }
                            dataset.append(dataPoint)
                        else:
                            dataset[index]["team" + n + "stat1"] = dp[stat1]
                            if stat2:
                                dataset[index]["team" + n + "stat2"] = dp[stat2]

        events = conn.cursor().execute("SELECT * from Events").fetchall()
        conn.close()
        tmpl = loader.load("teams.xhtml")
        page = tmpl.generate(
            session=cherrypy.session,
            chart_data=str(dataset).replace("'", '"'),
            columns=game.DISPLAY_FIELDS,
            chartColumns=game.CHART_FIELDS,
            stat1=stat1,
            stat2=stat2,
            teams=nums,
            stat_data=stats_data,
            events=events,
        )
        return page.render("html", doctype="html")

    # Output for alliance comparison
    @cherrypy.expose()
    def alliances(self, b1="", b2="", b3="", r1="", r2="", r3="", level=""):
        sessionCheck()
        if level == "":
            level = "quals"
        numsBlue = [b1, b2, b3]
        numsRed = [r1, r2, r3]
        averages = []
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()

        blueData = []
        redData = []
        # iterate through all six teams and grab data
        for i, n in enumerate(numsBlue):
            if not n.isdigit():
                raise cherrypy.HTTPError(400, "Enter six valid team numbers!")
            entries = cursor.execute(
                "SELECT * FROM ScoutRecords WHERE Team=? AND EventCode=? ORDER BY Match DESC",
                (n, getEvent()),
            ).fetchall()
            prevEvent = 0
            teamData = []
            teamData.append(getPitDisplayData(n))
            if len(entries) < 3:
                seasonEntries = cursor.execute(
                    "SELECT * FROM ScoutRecords WHERE Team=? ORDER BY Match DESC", (n,)
                ).fetchall()
                if len(seasonEntries) >= 3:
                    oldAverages = getAggregateData(Team=n, Mode="Averages")
                    assert (
                        len(oldAverages) < 2
                    )  # ensure there aren't two entries for one team
                    if len(oldAverages):
                        teamData.append(oldAverages[0])
                        prevEvent = 1

            if prevEvent == 0:
                average = getAggregateData(Team=n, Event=getEvent(), Mode="Averages")
                if not len(average):
                    average = dict(game.SCOUT_FIELDS)
                    average.update(game.DISPLAY_FIELDS)
                    average.update(game.HIDDEN_DISPLAY_FIELDS)
                    average["Team"] = n
                    teamData.append(average)
                else:
                    teamData.append(average[0])
            blueData.append(teamData)

        for i, n in enumerate(numsRed):
            if not n.isdigit():
                raise cherrypy.HTTPError(400, "Enter six valid team numbers!")
            entries = cursor.execute(
                "SELECT * FROM ScoutRecords WHERE Team=? AND EventCode=? ORDER BY Match DESC",
                (n, getEvent()),
            ).fetchall()
            prevEvent = 0
            teamData = []
            teamData.append(getPitDisplayData(n))
            if len(entries) < 3:
                seasonEntries = cursor.execute(
                    "SELECT * FROM ScoutRecords WHERE Team=? ORDER BY Match DESC", (n,)
                ).fetchall()
                if len(seasonEntries) >= 3:
                    oldAverages = getAggregateData(Team=n, Mode="Averages")
                    assert (
                        len(oldAverages) < 2
                    )  # ensure there aren't two entries for one team
                    if len(oldAverages):
                        teamData.append(oldAverages[0])
                        prevEvent = 1

            if prevEvent == 0:
                average = getAggregateData(Team=n, Event=getEvent(), Mode="Averages")
                if not len(average):
                    average = dict(game.SCOUT_FIELDS)
                    average.update(game.DISPLAY_FIELDS)
                    average.update(game.HIDDEN_DISPLAY_FIELDS)
                    average["Team"] = n
                    teamData.append(average)
                else:
                    teamData.append(average[0])
            redData.append(teamData)

        # Predict scores
        blue_score = game.predictScore(getEvent(), numsBlue, level)["score"]
        red_score = game.predictScore(getEvent(), numsRed, level)["score"]
        blue_score = int(blue_score)
        red_score = int(red_score)

        # Calculate win probability. Currently uses regression from 2016 data, this should be updated
        prob_red = 1 / (1 + math.e ** (-0.08099 * (red_score - blue_score)))
        red_win=round(prob_red * 100, 1)
        events = conn.cursor().execute("SELECT * from Events").fetchall()
        conn.close()

        tmpl = loader.load("alliances.xhtml")
        page = tmpl.generate(
            session=cherrypy.session,
            red_win=red_win,
            blue_win=round(100-red_win,1),
            red_score=red_score,
            blue_score=blue_score,
            red_data=redData,
            blue_data=blueData,
            columns=game.DISPLAY_FIELDS,
            events=events,
            pitColumns=game.PIT_DISPLAY_FIELDS,
        )
        return page.render("html", doctype="html")

    # Lists schedule data from TBA
    @cherrypy.expose()
    def matches(self, n=""):
        sessionCheck()

        # Get match data
        m = self.getMatches(getEvent())

        output = ""

        if "feed" in m:
            raise cherrypy.HTTPError(503, "Unable to retrieve data about this event.")

        # assign weights, so we can sort the matches
        for match in m:
            match["value"] = match["match_number"]
            type = match["comp_level"]
            if type == "qf":
                match["value"] += 1000
            elif type == "sf":
                match["value"] += 2000
            elif type == "f":
                match["value"] += 3000

        m = sorted(m, key=lambda k: k["value"])

        # For each match, generate a row in the table
        for match in m:
            level = "quals"
            if match["comp_level"] != "qm":
                match["num"] = (
                    match["comp_level"].upper()
                    + str(match["set_number"])
                    + "_"
                    + str(match["match_number"])
                )
                level = "playoffs"
            else:
                match["num"] = match["match_number"]
                if match["alliances"]["blue"]["score"] == -1:
                    match["alliances"]["blue"]["score"] = ""
                if match["alliances"]["red"]["score"] == -1:
                    match["alliances"]["red"]["score"] = ""
            blueTeams = [
                match["alliances"]["blue"]["team_keys"][0][3:],
                match["alliances"]["blue"]["team_keys"][1][3:],
                match["alliances"]["blue"]["team_keys"][2][3:],
            ]
            match["bluePredict"] = game.predictScore(getEvent(), blueTeams, level)
            redTeams = [
                match["alliances"]["red"]["team_keys"][0][3:],
                match["alliances"]["red"]["team_keys"][1][3:],
                match["alliances"]["red"]["team_keys"][2][3:],
            ]
            match["redPredict"] = game.predictScore(getEvent(), redTeams, level)

        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        events = conn.cursor().execute("SELECT * from Events").fetchall()
        conn.close()
        tmpl = loader.load("matches.xhtml")
        page = tmpl.generate(session=cherrypy.session, matches=m, events=events)
        return page.render("html", doctype="html")

    # Used by the scanning program to submit data, and used by comment system to submit data
    @cherrypy.expose()
    def submit(self, auth="", data="", pitData="", event="", team="", comment=""):
        if not (data or team or pitData):
            return """
                <h1>FATAL ERROR</h1>
                <h3>DATA CORRUPTION</h3>"""

        if data == "json":
            return "[]"  # bogus json for local version

        if not event:
            event = getEvent()
        self.database_exists()
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()

        # If team is defined, this should be a comment
        if team:
            if not comment:
                conn.close()
                raise cherrypy.HTTPRedirect("/team?n=" + str(team))
            if not checkAuth(False):
                conn.close()
                raise cherrypy.HTTPError(
                    401,
                    "Error: Not authorized to submit comments. Please login and try again",
                )
            comments = cursor.execute(
                "SELECT Comments FROM Teams WHERE TeamNumber=?", (team,)
            ).fetchone()
            if comments[0] is None:
                cursor.execute(
                    "UPDATE Teams SET Comments=? WHERE TeamNumber=?", (comment, team)
                )
            else:
                existing = convertStringToArray(comments[0])
                existing.append(comment)
                cursor.execute(
                    "UPDATE Teams SET Comments=? WHERE TeamNumber=?",
                    (convertArrayToString(existing), team),
                )
            conn.commit()
            conn.close()
            raise cherrypy.HTTPRedirect("/team?n=" + str(team))

        # If team is not defined, this should be scout data. First check auth key
        if auth == serverinfo.AUTH:
            if data:
                d = literal_eval(data)

                # Check if data should be flagged due to conflicting game specific values
                flag = game.autoFlag(d)

                # If match schedule is available, check if this is a real match and flag if bad
                try:
                    m = self.getMatches(event)
                    if m:
                        match = next(
                            (
                                item
                                for item in m
                                if (item["match_number"] == d["Match"])
                                and (item["comp_level"] == "qm")
                            )
                        )
                        teams = (
                            match["alliances"]["blue"]["team_keys"]
                            + match["alliances"]["red"]["team_keys"]
                        )
                        if not "frc" + str(d["Team"]) in teams:
                            flag = 1
                except:
                    pass

                # If replay is marked, replace previous data
                if d["Replay"]:  # replay
                    cursor.execute(
                        "DELETE from ScoutRecords WHERE Team=? AND Match=? AND EventCode=?",
                        (str(d["Team"]), str(d["Match"]), event),
                    )

                # Insert data into database
                cursor.execute(
                    "INSERT OR IGNORE INTO Teams(TeamNumber) VALUES(?)", (d["Team"],)
                )
                cursor.execute(
                    "INSERT OR IGNORE INTO Participation VALUES (NULL,?,?)",
                    (d["Team"], event),
                )
                cursor.execute(
                    "INSERT OR IGNORE INTO Picklist(EventCode,TeamNumber,List) VALUES(?,?,?)",
                    (event, (d["Team"]), "Unassigned"),
                )
                cursor.execute(
                    "INSERT INTO ScoutRecords VALUES (?,"
                    + ",".join([str(a) for a in d.values()])
                    + ")",
                    (event,),
                )
                conn.commit()
                conn.close()

                return ""
            elif pitData:
                d = literal_eval(pitData)
                values = ""
                for i, key in enumerate(game.PIT_SCOUT_FIELDS):
                    if key == "TeamNumber":
                        continue
                    values += key + "=" + str(d[key]) + ", "
                values = values[:-2]
                cursor.execute(
                    "INSERT OR IGNORE INTO Teams(TeamNumber) VALUES(?)", (d["TeamNumber"],)
                )
                cursor.execute(
                    "UPDATE Teams SET " + values + " WHERE TeamNumber=?",
                    (d["TeamNumber"],),
                )
                conn.commit()
                conn.close()
                return ""
        else:
            raise cherrypy.HTTPError(401, "Error: Not authorized to submit match data")

    #page fo deleting match data
    @cherrypy.expose()
    def delete(self, key="", auth="", **params):
        sessionCheck()
        if not checkAuth(False):
            if not auth == serverinfo.AUTH:
                raise cherrypy.HTTPError(
                    401, "Not authorized to delete match data. Please log in and try again"
                )
        if server.localInstance:
            with open("deleteQueue.txt", "a+") as file:
                file.write(str(key) + "\n")
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()
        cursor.execute("DELETE from ScoutRecords WHERE rowid=?",(key,))
        conn.commit()
        conn.close()

    # Page for editing match data
    @cherrypy.expose()
    def edit(self, key="", auth="", **params):
        sessionCheck()
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()

        if not checkAuth(False):
            if not auth == serverinfo.AUTH:
                raise cherrypy.HTTPError(
                    401, "Not authorized to edit match data. Please log in and try again"
                )

        # If there is data, this is a post and data should be used to update the entry
        if len(params) > 1:
            sqlCommand = "UPDATE ScoutRecords SET "
            for name, value in params.items():
                sqlCommand += name + "=" + (value if value else "NULL") + " , "
            sqlCommand = sqlCommand[:-2]
            sqlCommand += "WHERE rowid=" + str(key)
            cursor.execute(sqlCommand)
            conn.commit()
            conn.close()
            if server.localInstance:
                with open("editQueue.txt", "a+") as file:
                    params['key']= key
                    file.write(str(params) + "\n")

        # Grab all match data entries from the event, with flagged entries first, then sorted by team, then match
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()
        entries = cursor.execute(
            "SELECT rowid,* from ScoutRecords WHERE EventCode=? ORDER BY flag DESC, Team ASC, Match ASC",
            (getEvent(),),
        ).fetchall()

        if key == "":
            key = entries[0][0]

        # Grab the currently selected entry
        entry = cursor.execute(
            "SELECT rowid,* from ScoutRecords WHERE rowid=?", (key,)
        ).fetchone()
        events = conn.cursor().execute("SELECT * from Events").fetchall()
        conn.close()
        conn.close()

        tmpl = loader.load("edit.xhtml")
        page = tmpl.generate(
            session=cherrypy.session,
            entries=entries,
            entry=entry,
            scout_fields=game.SCOUT_FIELDS,
            events=events,
        )
        return page.render("html", doctype="html")

    # Page to show current rankings, and predict final rankings
    @cherrypy.expose()
    def rankings(self):
        sessionCheck()
        self.database_exists()
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()
        events = conn.cursor().execute("SELECT * from Events").fetchall()
        conn.close()

        rankings = {}

        # Grab latest rankings and match data from TBA
        headers = {
            "X-TBA-Auth-Key": "n8QdCIF7LROZiZFI7ymlX0fshMBL15uAzEkBgtP1JgUpconm2Wf49pjYgbYMstBF"
        }
        m = requests.get(
            "http://www.thebluealliance.com/api/v3/event/{0}/matches".format(
                getEvent()
            ),
            params=headers,
        )
        r = requests.get(
            "http://www.thebluealliance.com/api/v3/event/{0}/rankings".format(
                getEvent()
            ),
            params=headers,
        )
        if "feed" in m:
            raise cherrypy.HTTPError(503, "Unable to retrieve data about this event.")
        if r.text != "[]":
            r = r.json()
        else:
            raise cherrypy.HTTPError(
                503, "Unable to retrieve rankings data for this event."
            )
        if m.text != "[]":
            m = m.json()
        else:
            raise cherrypy.HTTPError(
                503, "Unable to retrieve match data for this event."
            )

        # Process current rankings into dict
        for item in r["rankings"]:
            rankings[item["team_key"][3:]] = {
                "rp": round(item["sort_orders"][0] * item["matches_played"], 0),
                "matchScore": round(item["sort_orders"][1] * item["matches_played"], 0),
                "currentRP": round(item["sort_orders"][0] * item["matches_played"], 0),
                "currentMatchScore": round(
                    item["sort_orders"][1] * item["matches_played"], 0
                ),
            }

        # Iterate through all matches
        for match in m:
            if match["comp_level"] == "qm":
                # Un-played matches show a score of -1. Predict the outcome
                if match["alliances"]["blue"]["score"] == -1:
                    blueTeams = [
                        match["alliances"]["blue"]["team_keys"][0][3:],
                        match["alliances"]["blue"]["team_keys"][1][3:],
                        match["alliances"]["blue"]["team_keys"][2][3:],
                    ]
                    blueResult = game.predictScore(getEvent(), blueTeams)
                    blueRP = blueResult["RP1"] + blueResult["RP2"]
                    redTeams = [
                        match["alliances"]["red"]["team_keys"][0][3:],
                        match["alliances"]["red"]["team_keys"][1][3:],
                        match["alliances"]["red"]["team_keys"][2][3:],
                    ]
                    redResult = game.predictScore(getEvent(), redTeams)
                    redRP = redResult["RP1"] + redResult["RP2"]
                    if blueResult["score"] > redResult["score"]:
                        blueRP += 2
                    elif redResult["score"] > blueResult["score"]:
                        redRP += 2
                    else:
                        redRP += 1
                        blueRP += 1
                    for team in blueTeams:
                        if team not in rankings:
                            rankings[team] = {
                                "rp": 0,
                                "matchScore": 0,
                                "currentRP": 0,
                                "currentMatchScore": 0,
                            }
                        rankings[team]["rp"] += blueRP
                        rankings[team]["matchScore"] += blueResult["score"]
                    for team in redTeams:
                        if team not in rankings:
                            rankings[team] = {
                                "rp": 0,
                                "matchScore": 0,
                                "currentRP": 0,
                                "currentMatchScore": 0,
                            }
                        rankings[team]["rp"] += redRP
                        rankings[team]["matchScore"] += redResult["score"]

        # Sort rankings, then output into table
        sorted_rankings = sorted(
            rankings.items(),
            key=keyFromItem(lambda k, v: (v["rp"], v["matchScore"])),
            reverse=True,
        )
        tmpl = loader.load("rankings.xhtml")
        page = tmpl.generate(
            rankings=sorted_rankings, session=cherrypy.session, events=events
        )
        return page.render("html", doctype="html")

    # Return the path to the database for this event
    def datapath(self):
        return "data.db"

    # Return the selected event
    def getevent(self):
        if "event" not in cherrypy.session:
            cherrypy.session["event"] = CURRENT_EVENT
        return cherrypy.session["event"]

    def getMatches(self, event, team=""):
        headers = {
            "X-TBA-Auth-Key": "n8QdCIF7LROZiZFI7ymlX0fshMBL15uAzEkBgtP1JgUpconm2Wf49pjYgbYMstBF"
        }
        try:
            if team:
                # request a specific team
                m = requests.get(
                    "http://www.thebluealliance.com/api/v3/team/frc{0}/event/{1}/matches".format(
                        team, event
                    ),
                    params=headers,
                )
            else:
                # get all the matches from this event
                m = requests.get(
                    "http://www.thebluealliance.com/api/v3/event/{0}/matches".format(
                        event
                    ),
                    params=headers,
                )
            if m.status_code == 400 or m.status_code == 404:
                raise Exception
            if m.text != "[]":
                with open(event + "_matches.json", "w+") as file:
                    file.write(str(m.text))
                m = m.json()
            else:
                m = []
        except:
            try:
                with open(event + "_matches.json") as matches_data:
                    m = json.load(matches_data)
            except:
                m = []
        return m

    # Wrapper for requests, ensuring nothing goes terribly wrong
    # Used to avoid errors when running without internet
    def get(self, req, params=""):
        a = None
        try:
            a = requests.get(req, params=params)
            if a.status_code == 404:
                raise Exception
        except:
            a = "[]"
        return a

    def database_exists(self):
        datapath = "data.db"
        if not os.path.isfile(datapath):
            # Generate a new database with the tables
            conn = sql.connect(datapath)
            cursor = conn.cursor()
            tableFields = ""
            for key in game.PIT_SCOUT_FIELDS:
                if key != "Team":
                    tableFields += key + " INTEGER, "

            cursor.execute(
                """CREATE TABLE "Events" ("EventCode" TEXT, "StartDate" TEXT, "EndDate" TEXT, "Name" TEXT, PRIMARY KEY("EventCode"))"""
            )
            cursor.execute(
                """CREATE TABLE "Teams" ("Name" TEXT, "Comments" TEXT, """
                + tableFields
                + """ PRIMARY KEY("TeamNumber"))"""
            )
            cursor.execute(
                """CREATE TABLE "Matches" ("EventCode" TEXT, "MatchNumber" INTEGER, PRIMARY KEY("EventCode","MatchNumber"), FOREIGN KEY("EventCode") REFERENCES "Events"("EventCode"))"""
            )
            cursor.execute(
                """CREATE TABLE "Participation" (key INTEGER PRIMARY KEY, "TeamNumber" INTEGER, "EventCode" TEXT, FOREIGN KEY("EventCode") REFERENCES "Events"("EventCode"), FOREIGN KEY("TeamNumber") REFERENCES "Teams"("TeamNumber"))"""
            )
            cursor.execute(
                """CREATE TABLE "Picklist" ( "EventCode" TEXT, "TeamNumber" INTEGER, "List" TEXT, "Rank" INTEGER, PRIMARY KEY("EventCode","TeamNumber"), FOREIGN KEY("EventCode") REFERENCES "Events"("EventCode"))"""
            )

            tableFields = ""
            for key in game.SCOUT_FIELDS:
                tableFields += key + " integer, "
            tableFields += game.getDisplayFieldCreate()
            cursor.execute(
                """CREATE TABLE "ScoutRecords" ("EventCode" TEXT, """
                + tableFields
                + """ PRIMARY KEY("Match","EventCode","Team"), FOREIGN KEY("EventCode") REFERENCES "Events"("EventCode"), FOREIGN KEY("Team") REFERENCES "Teams"("TeamNumber"))"""
            )

            conn.close()
        # END OF CLASS


# Execution starts here
datapath = "data.db"


# Helper function used in rankings sorting
def keyFromItem(func):
    return lambda item: func(*item)


def sessionCheck():
    getMode()
    getEvent()


def checkAuth(AdminRequired):
    if "auth" not in cherrypy.session:
        if server.localInstance:
            cherrypy.session["auth"] = serverinfo.AUTH
            cherrypy.session["admin"] = serverinfo.ADMIN
            return True
        else:
            cherrypy.session["auth"] = ""
            cherrypy.session["admin"] = ""
            return False
    else:
        if AdminRequired:
            return cherrypy.session["admin"] == serverinfo.ADMIN
        else:
            return cherrypy.session["auth"] == serverinfo.AUTH


def getAggregateData(Team="", Event="", Mode=""):
    # This section grabs the averages data from the database to hand to the webpage
    conn = sql.connect(datapath)
    conn.row_factory = dict_factory

    if Mode == "":
        Mode = getMode()

    sqlAvgCommandBase = "SELECT "
    sqlMaxCommandBase = "SELECT "
    columns = {**game.SCOUT_FIELDS, **game.DISPLAY_FIELDS, **game.HIDDEN_DISPLAY_FIELDS}
    for key in columns:
        sqlMaxCommandBase += "MAX(" + key + ") AS " + key + ", "
    for key in columns:
        sqlAvgCommandBase += "round(AVG(" + key + "),2) AS " + key + ", "
    sqlMaxCommandBase = sqlMaxCommandBase[:-2]
    sqlAvgCommandBase = sqlAvgCommandBase[:-2]
    if Mode == "Variance":
        sqlCommandBase = sqlMaxCommandBase
    else:
        sqlCommandBase = sqlAvgCommandBase
    noDefense = " AND Defense=0" if Mode == "NoDefense" else ""
    teamString = (" AND Team=" + Team) if Team else ""
    eventString = (" AND EventCode='" + Event + "'") if Event else ""
    if Mode == "Trends":
        table = (
            " FROM (Select * from (SELECT *, row_number() over (partition by Team order by match desc) as match_rank from ScoutRecords WHERE Flag=0"
            + eventString
            + teamString
            + ") where match_rank <= 3)"
        )
    elif not Event:
        table = (
            " FROM (Select * from (SELECT *, row_number() over (partition by Team order by EndDate desc, match desc) as match_rank from ScoutRecords INNER JOIN Events On ScoutRecords.EventCode=Events.EventCode WHERE Flag=0"
            + eventString
            + teamString
            + ") where match_rank <= 6)"
        )
    else:
        table = " FROM ScoutRecords WHERE Flag=0" + eventString + teamString
    sqlCommand = (
        sqlCommandBase + table + noDefense + " GROUP BY Team ORDER BY Team DESC"
    )
    data = conn.cursor().execute(sqlCommand).fetchall()
    if Mode == "Trends":
        avgData = (
            conn.cursor()
            .execute(
                sqlCommandBase
                + " FROM ScoutRecords WHERE Flag=0"
                + eventString
                + " GROUP BY Team ORDER BY Team DESC",
            )
            .fetchall()
        )
        latestData = data.copy()
        data = []
        for i, row in enumerate(latestData):
            rowData = dict(columns)
            for key in rowData:
                if key == "Team":
                    rowData[key] = row[key]
                else:
                    rowData[key] = round(row[key] - avgData[i][key], 2)
            data.append(rowData)
    if Mode == "Variance":
        avgData = (
            conn.cursor()
            .execute(
                sqlAvgCommandBase
                + " FROM ScoutRecords WHERE Flag=0"
                + eventString
                + " GROUP BY Team ORDER BY Team DESC",
            )
            .fetchall()
        )
        maxData = data.copy()
        data = []
        for i, row in enumerate(maxData):
            rowData = dict(columns)
            for key in rowData:
                if key == "Team":
                    rowData[key] = row[key]
                else:
                    rowData[key] = round(row[key] - avgData[i][key], 2)
            data.append(rowData)
    conn.close()
   # for team in data:
   #     team["FirstP"] = (
   #         team["CargoPoints"] * prop.FIRST_CARGO_POINTS
   #         + team["Hangar"] * prop.FIRST_HANGAR
   #     )
    return data


def getPitDisplayData(team):
    conn = sql.connect(datapath)
    conn.row_factory = sql.Row
    cursor = conn.cursor()
    sqlCommand = "SELECT "
    for key in game.PIT_DISPLAY_FIELDS:
        sqlCommand += key + ", "
    sqlCommand = sqlCommand[:-2]
    sqlCommand += " FROM Teams WHERE TeamNumber=?"
    sql_pit = cursor.execute(sqlCommand, (team,)).fetchall()
    if len(sql_pit):
        return sql_pit[0]
    else:
        return dict(game.PIT_DISPLAY_FIELDS)


def getMode():
    if "mode" not in cherrypy.session:
        cherrypy.session["mode"] = "Averages"
    return cherrypy.session["mode"]


def getEvent():
    if "event" not in cherrypy.session:
        cherrypy.session["event"] = CURRENT_EVENT
    return cherrypy.session["event"]


strSeparator = "__,__"


def convertArrayToString(array):
    str = ""
    for substring in array:
        str = str + substring + strSeparator
    str[: -1 * (len(strSeparator))]
    return str


def convertStringToArray(str):
    array = str.split(strSeparator)
    return array


# Configuration used for local instance of the server
localConf = {
    "/": {
        "tools.sessions.on": True,
        "tools.staticdir.root": os.path.abspath(os.getcwd()),
    },
    "/static": {"tools.staticdir.on": True, "tools.staticdir.dir": "./web/static"},
    "/favicon.ico": {
        "tools.staticfile.on": True,
        "tools.staticfile.filename": os.path.abspath(os.getcwd())
        + "./web/static/img/favicon.ico",
    },
    "global": {"server.socket_port": 8000},
}

# Configuration for remote instance of the server
remoteConf = {
    "/": {
        "tools.sessions.on": True,
        "tools.staticdir.root": os.path.abspath(os.getcwd()),
    },
    "/static": {"tools.staticdir.on": True, "tools.staticdir.dir": "./web/static"},
    "/favicon.ico": {
        "tools.staticfile.on": True,
        "tools.staticfile.filename": os.path.abspath(os.getcwd())
        + "./web/static/img/favicon.ico",
    },
    "global": {"server.socket_host": "0.0.0.0", "server.socket_port": 80},
}


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def main():
    # Determine which config to launch based on command line args
    if len(sys.argv) > 1:
        if sys.argv[1] == "-local":
            print("Starting local server")
            server.localInstance = True
            cherrypy.quickstart(ScoutServer(), "/", localConf)
        else:
            print("Starting remote server")
            cherrypy.quickstart(ScoutServer(), "/", remoteConf)
    else:
        print("Starting remote server")
        cherrypy.quickstart(ScoutServer(), "/", remoteConf)


if __name__ == "__main__":
    main()
