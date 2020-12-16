import cherrypy
import sqlite3 as sql
import os
import json
from ast import literal_eval
import requests
import math
from event import CURRENT_EVENT
import gamespecific as game
import serverinfo
import sys
import re
from genshi.template import TemplateLoader

DEFAULT_MODE = 'averages'
localInstance = False;
loader = TemplateLoader(
    os.path.join(os.path.dirname(__file__), 'web/templates'),
    auto_reload=True)


class ScoutServer(object):
    # Make sure that database for current event exists on startup
    def __init__(self):
        self.database_exists(CURRENT_EVENT)

    # Home page
    @cherrypy.expose
    def index(self, m='', e=''):

        # Add auth value to session if not present
        authCheck()

        # Handle event selection. When the event is changed, a POST request is sent here.
        if e != '':
            if os.path.isfile('data_' + e + '.db'):
                cherrypy.session['event'] = e
        if 'event' not in cherrypy.session:
            cherrypy.session['event'] = CURRENT_EVENT

        # Handle mode selection. When the mode is changed, a POST request is sent here.
        if m != '':
            cherrypy.session['mode'] = m
        if 'mode' not in cherrypy.session:
            cherrypy.session['mode'] = DEFAULT_MODE

        # This section grabs the averages data from the database to hand to the webpage
        table = ''
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        sqlCommand = "SELECT * FROM " + cherrypy.session['mode'] + " ORDER BY Team DESC"
        data = conn.cursor().execute(sqlCommand).fetchall()
        conn.close()

        # Pass off the normal set of columns or columns with the hidden fields depending on authentication
        if cherrypy.session['auth'] == serverinfo.AUTH:
            columns = {**game.AVERAGE_FIELDS, **game.HIDDEN_AVERAGE_FIELDS}
        else:
            columns = game.AVERAGE_FIELDS

        tmpl = loader.load('index.xhtml')
        page = tmpl.generate(columns=columns, title="Home", session=cherrypy.session, data=data)
        return page.render('html', doctype='html')

    # Page for creating picklist
    @cherrypy.expose
    def picklist(self, m='', list='', dnp=''):
        if not cherrypy.session['auth'] == serverinfo.AUTH:
            raise cherrypy.HTTPError(401, "Not authorized to view picklist. Please log in and try again.")

        if cherrypy.session['admin'] == serverinfo.ADMIN:
            fileName = "web/picklist.html"
        else:
            fileName = "web/picklistReadOnly.html"

        # Handle mode selection. When the mode is changed, a POST request is sent here.
        if m != '':
            cherrypy.session['mode'] = m
        if 'mode' not in cherrypy.session:
            cherrypy.session['mode'] = DEFAULT_MODE

        if list:
            pattern = re.compile('team\[\]=(\d*)')
            pickList = pattern.findall(list)
            with open(self.getevent() + "pickList.txt", "w+") as file:
                for team in pickList:
                    file.write(str(team) + '\n')
        else:
            try:
                with open(self.getevent() + "pickList.txt", "r+") as file:
                    pickList = file.readlines()
                    for i, item in enumerate(pickList):
                        pickList[i] = item[:-1]
            except:
                pickList = []

        if dnp:
            pattern = re.compile('team\[\]=(\d*)')
            dnpList = pattern.findall(dnp)
            with open(self.getevent() + "dnpList.txt", "w+") as file:
                for team in dnpList:
                    file.write(str(team) + '\n')
        else:
            try:
                with open(self.getevent() + "dnpList.txt", "r+") as file:
                    dnpList = file.readlines()
                    for i, item in enumerate(dnpList):
                        dnpList[i] = item[:-1]
            except:
                dnpList = []

        # This section generates the table of averages
        table = ''
        tableHeaders = ''
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        if cherrypy.session['mode'] == "trends":
            sqlCommand = "SELECT * FROM averages ORDER BY Team DESC"
            data = conn.cursor().execute(sqlCommand).fetchall()
        else:
            sqlCommand = "SELECT * FROM " + cherrypy.session['mode'] + " ORDER BY Team DESC"
            data = conn.cursor().execute(sqlCommand).fetchall()
        # First generate a header for each column. There are two blocks, 1 for regular and 1 for mobile
        for i, key in enumerate(game.AVERAGE_FIELDS):
            if key != "Team":
                tableHeaders += '''
                <th class="text-center hidden-xs col-sm-1 tablesorter-header tablesorter-headerUnSorted" data-column="{1}" tabindex="0" scope="col" role="columnheader" aria-disabled="false" unselectable="on" style="-moz-user-select: none;" aria-sort="none" aria-label="{0}: No sort applied, activate to apply an ascending sort"><div class="tablesorter-header-inner">{0}</div></th>
                
                <th class="titleColumn titleColumn{1} text-center hidden-sm hidden-md hidden-lg col-xs-3 tablesorter-header tablesorter-headerUnSorted hidden-xs" data-column="{1}" tabindex="0" scope="col" role="columnheader" aria-disabled="false" unselectable="on" style="-moz-user-select: none; display: none; color: #EEEE00;" aria-sort="none" aria-label="{0}: No sort applied, activate to apply an ascending sort"><div class="tablesorter-header-inner">{0}</div></th>'''.format(
                    key, i)
        j = len(game.AVERAGE_FIELDS)
        for i, key in enumerate(game.HIDDEN_AVERAGE_FIELDS):
            tableHeaders += '''
          <th class="text-center hidden-xs col-sm-1 tablesorter-header tablesorter-headerUnSorted" data-column="{1}" tabindex="0" scope="col" role="columnheader" aria-disabled="false" unselectable="on" style="-moz-user-select: none;" aria-sort="none" aria-label="{0}: No sort applied, activate to apply an ascending sort"><div class="tablesorter-header-inner">{0}</div></th>
          
          <th class="titleColumn titleColumn{1} text-center hidden-sm hidden-md hidden-lg col-xs-3 tablesorter-header tablesorter-headerUnSorted hidden-xs" data-column="{1}" tabindex="0" scope="col" role="columnheader" aria-disabled="false" unselectable="on" style="-moz-user-select: none; display: none; color: #EEEE00;" aria-sort="none" aria-label="{0}: No sort applied, activate to apply an ascending sort"><div class="tablesorter-header-inner">{0}</div></th>'''.format(
                key, i + j)

        tableHeaders += '''                            </tr>
                        </thead>'''
        table = tableHeaders
        dnpTable = tableHeaders
        table += '''<tbody id="main_table" aria-live="polite" aria-relevant="all">'''
        tableHeaders += '''<tbody class="picklist">'''
        dnpTable += '''<tbody class="dnp">'''

        if pickList:
            for team in pickList:
                if cherrypy.session['mode'] == "trends":
                    sqlCommand = "SELECT * FROM averages WHERE Team=?"
                    lastThreeData = conn.cursor().execute("SELECT * FROM lastThree WHERE Team=? ORDER BY Team DESC",
                                                          (team,)).fetchone()
                else:
                    sqlCommand = "SELECT * FROM " + cherrypy.session['mode'] + " WHERE Team=?"
                teamData = conn.cursor().execute(sqlCommand, (team,)).fetchone()
                tableHeaders += '''
                <tr role="row" id="team_{0}">
                    <td><a href="team?n={0}">{0}</a></td>'''.format(int(teamData['Team']))
                if cherrypy.session['mode'] == "trends":
                    for i, key in enumerate(game.AVERAGE_FIELDS):
                        if key != 'Team':
                            tableHeaders += '''
                            <td class="hidden-xs">{0}</td>
                            <td class="rankingColumn rankColumn{1} hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{0}</td>
                            '''.format(round(lastThreeData[key] - teamData[key], 2), i)
                else:
                    for i, key in enumerate(game.AVERAGE_FIELDS):
                        if key != 'Team':
                            tableHeaders += '''
                            <td class="hidden-xs">{0}</td>
                            <td class="rankingColumn rankColumn{1} hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{0}</td>
                            '''.format(teamData[key], i)
                j = len(game.AVERAGE_FIELDS)
                if cherrypy.session['mode'] == "trends":
                    for i, key in enumerate(game.HIDDEN_AVERAGE_FIELDS):
                        tableHeaders += '''
                      <td class="hidden-xs">{0}</td>
                      <td class="rankingColumn rankColumn{1} hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{0}</td>
                      '''.format(round(lastThreeData[key] - teamData[key], 2), i + j)
                else:
                    for i, key in enumerate(game.HIDDEN_AVERAGE_FIELDS):
                        tableHeaders += '''
                      <td class="hidden-xs">{0}</td>
                      <td class="rankingColumn rankColumn{1} hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{0}</td>
                      '''.format(teamData[key], i + j)
                tableHeaders += '''</tr>'''

        if dnpList:
            for team in dnpList:
                if cherrypy.session['mode'] == "trends":
                    sqlCommand = "SELECT * FROM averages WHERE Team=?"
                    lastThreeData = conn.cursor().execute("SELECT * FROM lastThree WHERE Team=? ORDER BY Team DESC",
                                                          (team,)).fetchone()
                else:
                    sqlCommand = "SELECT * FROM " + cherrypy.session['mode'] + " WHERE Team=?"
                teamData = conn.cursor().execute(sqlCommand, (team,)).fetchone()
                dnpTable += '''
                <tr role="row" id="team_{0}">
                    <td><a href="team?n={0}">{0}</a></td>'''.format(int(teamData['Team']))
                if cherrypy.session['mode'] == "trends":
                    for i, key in enumerate(game.AVERAGE_FIELDS):
                        if key != 'Team':
                            dnpTable += '''
                            <td class="hidden-xs">{0}</td>
                            <td class="rankingColumn rankColumn{1} hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{0}</td>
                            '''.format(round(lastThreeData[key] - teamData[key], 2), i)
                else:
                    for i, key in enumerate(game.AVERAGE_FIELDS):
                        if key != 'Team':
                            dnpTable += '''
                            <td class="hidden-xs">{0}</td>
                            <td class="rankingColumn rankColumn{1} hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{0}</td>
                            '''.format(teamData[key], i)
                j = len(game.AVERAGE_FIELDS)
                if cherrypy.session['mode'] == "trends":
                    for i, key in enumerate(game.HIDDEN_AVERAGE_FIELDS):
                        dnpTable += '''
                      <td class="hidden-xs">{0}</td>
                      <td class="rankingColumn rankColumn{1} hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{0}</td>
                      '''.format(round(lastThreeData[key] - teamData[key], 2), i + j)
                else:
                    for i, key in enumerate(game.HIDDEN_AVERAGE_FIELDS):
                        dnpTable += '''
                      <td class="hidden-xs">{0}</td>
                      <td class="rankingColumn rankColumn{1} hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{0}</td>
                      '''.format(teamData[key], i + j)
                dnpTable += '''</tr>'''

        # Generate a row for each team
        for team in data:
            if str(team['Team'])[:-2] not in pickList + dnpList:
                if cherrypy.session['mode'] == "trends":
                    lastThreeData = conn.cursor().execute("SELECT * FROM lastThree WHERE Team=? ORDER BY Team DESC",
                                                          (team['Team'],)).fetchone()
                table += '''
                <tr role="row" id="team_{0}">
                    <td><a href="team?n={0}">{0}</a></td>'''.format(int(team['Team']))
                if cherrypy.session['mode'] == "trends":
                    for i, key in enumerate(game.AVERAGE_FIELDS):
                        if key != 'Team':
                            table += '''
                            <td class="hidden-xs">{0}</td>
                            <td class="rankingColumn rankColumn{1} hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{0}</td>
                            '''.format(round(lastThreeData[key] - team[key], 2), i)
                else:
                    for i, key in enumerate(game.AVERAGE_FIELDS):
                        if key != 'Team':
                            table += '''
                            <td class="hidden-xs">{0}</td>
                            <td class="ranktableankColumn{1} hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{0}</td>
                            '''.format(team[key], i)
                j = len(game.AVERAGE_FIELDS)
                if cherrypy.session['mode'] == "trends":
                    for i, key in enumerate(game.HIDDEN_AVERAGE_FIELDS):
                        table += '''
                      <td class="hidden-xs">{0}</td>
                      <td class="rankingColumn rankColumn{1} hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{0}</td>
                      '''.format(round(lastThreeData[key] - team[key], 2), i + j)
                else:
                    for i, key in enumerate(game.HIDDEN_AVERAGE_FIELDS):
                        table += '''
                      <td class="hidden-xs">{0}</td>
                      <td class="rankingColumn rankColumn{1} hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{0}</td>
                      '''.format(team[key], i + j)
                table += '''</tr>'''
        conn.close()
        with open(fileName, 'r') as file:
            page = file.read()
        return page.format(table, cherrypy.session['event'], cherrypy.session['mode'], tableHeaders, dnpTable,
                           len(game.AVERAGE_FIELDS) + len(game.HIDDEN_AVERAGE_FIELDS) - 3)

    # Page to show result of login attempt
    @cherrypy.expose()
    def login(self, auth=''):
        loginResult = "Login failed! Please check password"
        if auth == serverinfo.AUTH:
            cherrypy.session['auth'] = auth
            loginResult = "Login successful"
        if auth == serverinfo.ADMIN:
            cherrypy.session['admin'] = auth
            cherrypy.session['auth'] = serverinfo.AUTH
            loginResult = "Admin Login successful"

        with open('web/login.html', 'r') as file:
            page = file.read()
        return page.format(loginResult)

        # Show a detailed summary for a given team

    @cherrypy.expose()
    def team(self, n="238"):
        authCheck()
        if not n.isdigit():
            raise cherrypy.HTTPRedirect('/')

        # Grab team data
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()
        entries = cursor.execute('SELECT * FROM scout WHERE Team=? ORDER BY Match DESC', (n,)).fetchall()
        sql_averages = cursor.execute('SELECT * FROM averages WHERE Team=?', (n,)).fetchall()
        comments = cursor.execute('SELECT * FROM comments WHERE team=?', (n,)).fetchall()
        sql_pit = cursor.execute('SELECT * FROM pitScout WHERE team=?', (n,)).fetchall()
        conn.close()
        assert len(sql_averages) < 2  # ensure there aren't two entries for one team
        assert len(sql_pit) < 2
        if len(sql_averages):
            averages = sql_averages[0]
        else:
            averages = dict(game.AVERAGE_FIELDS)
            averages.update(game.HIDDEN_AVERAGE_FIELDS)
        if len(sql_pit):
            pit = sql_pit[0]
        else:
            pit = 0

        statbox = ""
        # If we have less than 4 entries, see if we can grab data from a previous event
        lastEvent = 0
        if (len(entries) < 4):
            globalconn = sql.connect('global.db')
            globalconn.row_factory = sql.Row
            globalcursor = globalconn.cursor()
            teamEvents = globalcursor.execute('SELECT * FROM teamEvents WHERE Team=?', (n,)).fetchone()
            if teamEvents:
                for i in range(1, 10):
                    if teamEvents['Event' + str(i)]:
                        if teamEvents['Event' + str(i)] != cherrypy.session['event']:
                            lastEventCode = teamEvents['Event' + str(i)]
                            lastEvent = 1
        if lastEvent:
            try:
                oldconn = sql.connect('data_' + lastEventCode + '.db')
                oldconn.row_factory = sql.Row
                oldcursor = oldconn.cursor()
                oldAverages = oldcursor.execute('SELECT * FROM averages WHERE Team=?', (n,)).fetchall()
                assert len(oldAverages) < 2  # ensure there aren't two entries for one team
                if len(oldAverages):
                    oldData = oldAverages[0]
                    statbox += '''<div class="comparebox_container">
                  <p style="font-size: 32px;">Last Event - {0}</p>
                  <div class="statbox_container">
                      <div id="stats">'''.format(n)
                    for key in game.AVERAGE_FIELDS:
                        if (key != 'Team'):
                            statbox += '''<p class="statbox">{0}: {1}</p>'''.format(key, oldData[key])
                    if cherrypy.session['auth'] == serverinfo.AUTH:
                        for key in game.HIDDEN_AVERAGE_FIELDS:
                            statbox += '''<p class="statbox">{0}: {1}</p>'''.format(key, oldData[key])
                    statbox += '''       </div>
                                  </div>
                               </div>'''
            except:
                pass  # swallow the error

        # Generate Statbox
        statbox += '''<div class="comparebox_container">
                    <p style="font-size: 32px;">This Event</a></p>
                    <div class="statbox_container">
                        <div id="stats">'''.format(n)
        for key in game.AVERAGE_FIELDS:
            if (key != 'Team'):
                statbox += '''<p class="statbox">{0}: {1}</p>'''.format(key, averages[key])
        if cherrypy.session['auth'] == serverinfo.AUTH:
            for key in game.HIDDEN_AVERAGE_FIELDS:
                statbox += '''<p class="statbox">{0}: {1}</p>'''.format(key, averages[key])
        statbox += '''       </div>
                        </div>
                     </div>'''

        # If logged in, display pit scout data
        if cherrypy.session['auth'] == serverinfo.AUTH:
            if (pit):
                statbox += '''<div class="comparebox_container">
                    <p><a href="/team?n={0}" style="font-size: 32px;">Pit Scout</a></p>
                    <div class="statbox_container">
                        <div id="stats">'''
                for key in game.PIT_SCOUT_FIELDS:
                    if (key != 'Team') and (pit[key] != 0):
                        statbox += '''<p class="statbox">{0}: {1}</p>'''.format(key, pit[key])
                statbox += '''       </div>
                        </div>
                     </div>'''

        # Generate html for comments section
        commentstr = ''
        if cherrypy.session['auth'] == serverinfo.AUTH:
            for comment in comments:
                commentstr += '<div class="commentbox"><p>{0}</p></div>'.format(comment[1])

        output = ''

        teamChart = ''
        colors = ["#FF0000", "#000FFF", "#1DD300", "#C100E3", "#AF0000", "#000666", "#0D5B000", "#610172"]

        for index, field in enumerate(game.CHART_FIELDS):
            if field != 'match':
                teamChart += '''// GRAPH
                graph{0} = new AmCharts.AmGraph();
                graph{0}.title = "{1}";
                graph{0}.valueAxis = valueAxis;
                graph{0}.type = "smoothedLine"; // this line makes the graph smoothed line.
                graph{0}.lineColor = "{2}";
                graph{0}.bullet = "round";
                graph{0}.bulletSize = 8;
                graph{0}.bulletBorderColor = "#FFFFFF";
                graph{0}.bulletBorderAlpha = 1;
                graph{0}.bulletBorderThickness = 2;
                graph{0}.lineThickness = 2;
                graph{0}.valueField = "{1}";
                graph{0}.balloonText = "{1}<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                chart.addGraph(graph{0});
                '''.format(index, field, colors[index])

        dataset = []
        for e in entries:
            # Generate chart data and table text for this match entry
            dp = game.generateChartData(e)
            text = game.generateTeamText(e)

            # Generate a row in the table for each match
            output += '''
            <tr role="row" {5}>
                <td>{0}</td>
                <td>{1}</td>
                <td>{2}</td>
                <td>{3}</td>
                <td>{4}</td>
                <td><a class="flag" href="javascript:flag({6},{7});">X</a></td>
                <td class="hidden-xs"><a class="edit" href="/edit?key={8}">E</a></td>
            </tr>'''.format(e['Match'], *text.values(), 'style="color: #B20000"' if e['Flag'] else '', e['Match'],
                            e['Flag'], e['Key'])
            for key, val in dp.items():
                dp[key] = round(val, 2)
            if not e['Flag']:
                dataset.append(dp)  # add it to dataset, which is an array of data that is fed into the graphs
        dataset.reverse()  # reverse data so that graph is in the correct order

        # Grab the image from the blue alliance
        imcode = ''
        headers = {"X-TBA-Auth-Key": "n8QdCIF7LROZiZFI7ymlX0fshMBL15uAzEkBgtP1JgUpconm2Wf49pjYgbYMstBF"}
        m = []
        try:
            # get the picture for a given team
            m = self.get("http://www.thebluealliance.com/api/v3/team/frc{0}/media/2019".format(n),
                         params=headers).json()
            if m.status_code == 400:
                m = []
        except:
            pass  # swallow the error
        for media in m:
            if media['type'] == 'imgur':  # check if there's an imgur image on TBA
                imcode = '''<br>
                <div style="text-align: center">
                <p style="font-size: 32px;">Image</p>
                <img src=http://i.imgur.com/{}.jpg></img>
                </div>'''.format(media['foreign_key'])
                break
            if media['type'] == 'cdphotothread':
                imcode = '''<br>
                <div style="text-align: center">
                <p style="font-size: 32px;">Image</p>
                <img src=http://chiefdelphi.com/media/img/{}></img>
                </div>'''.format(media['details']['image_partial'].replace('_l', '_m'))
                break

        with open('web/team.html', 'r') as file:
            page = file.read()
        return page.format(n, output, statbox, str(dataset).replace("'", '"'), imcode, commentstr, teamChart)

    # Called to toggle flag on a data entry. Also does a recalc to add/remove entry from stats
    @cherrypy.expose()
    def flag(self, num='', match='', flagval=0):
        if not cherrypy.session['admin'] == serverinfo.ADMIN:
            raise cherrypy.HTTPError(401, "Not authorized to flag match data. Please log in and try again")
        if not (num.isdigit() and match.isdigit()):
            return '<img src="http://goo.gl/eAs7JZ" style="width: 1200px"></img>'
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()
        cursor.execute('UPDATE scout SET Flag=? WHERE Team=? AND Match=?', (int(not int(flagval)), num, match))
        conn.commit()
        conn.close()
        self.calcavg(num, self.getevent())
        return ''

    # Called to recalculate all calculated values
    @cherrypy.expose()
    def recalculate(self):
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()
        if not cherrypy.session['admin'] == serverinfo.ADMIN:
            raise cherrypy.HTTPError(401, "Not authorized to perform recalculate. Please log in and try again.")
        data = conn.cursor().execute('SELECT * FROM averages ORDER BY Team DESC').fetchall()
        for team in data:
            self.calcavg(team[0], self.getevent())
        with open('web/recalculate.html', 'r') as file:
            page = file.read()
        return page

    # Input interface to choose teams to compare
    @cherrypy.expose()
    def compareTeams(self):
        authCheck()
        with open('web/compareTeams.html', 'r') as file:
            page = file.read()
        return page

    # Input interface to choose alliances to compare
    @cherrypy.expose
    def compareAlliances(self):
        authCheck()
        with open('web/compareAlliances.html', 'r') as file:
            page = file.read()
        return page

    # Output for team comparison
    @cherrypy.expose()
    def teams(self, n1='', n2='', n3='', n4='', stat1='', stat2=''):
        authCheck()
        nums = [n1, n2, n3, n4]
        if stat2 == 'none':
            stat2 = ''
        if not stat1:
            stat1 = list(game.CHART_FIELDS)[1]

        averages = []
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()
        output = '<div>'

        # Grab data for each team, and generate a statbox
        for index, n in enumerate(nums):
            if not n:
                continue
            if not n.isdigit():
                raise cherrypy.HTTPError(400, "You fool! Enter NUMBERS, not letters.")
            average = cursor.execute('SELECT * FROM averages WHERE Team=?', (n,)).fetchall()
            assert len(average) < 2
            if len(average):
                entry = average[0]
            else:
                entry = dict(game.AVERAGE_FIELDS)
                entry.update(game.HIDDEN_AVERAGE_FIELDS)
            output += '''<div class="comparebox_container">
                    <p><a href="/team?n={0}" style="font-size: 32px;">Team {0}</a></p>
                    <div class="statbox_container">
                        <div id="stats">
                            <p class="statbox" style="font-weight:bold">Average match:</p>'''.format(int(entry['Team']))
            for key in game.AVERAGE_FIELDS:
                if (key != 'Team'):
                    output += '''<p class="statbox">{0}: {1}</p>'''.format(key, entry[key])
            if cherrypy.session['auth'] == serverinfo.AUTH:
                for key in game.HIDDEN_AVERAGE_FIELDS:
                    output += '''<p class="statbox">{0}: {1}</p>'''.format(key, entry[key])
            output += '''       </div>
                            </div>
                         </div>'''
            if ((len(nums) == 2 and index == 0) or (len(nums) != 2 and index == 1)):
                output += '</div><div>'
        output += '</div>'

        teamCharts = ''
        dataset = []
        colors = ["#FF0000", "#000FFF", "#1DD300", "#C100E3", "#AF0000", "#000666", "#0D5B000", "#610172"]

        # For each team, grab each match entry and generate chart data, then add them to the graph
        for idx, n in enumerate(nums):
            if not n:
                continue
            entries = cursor.execute('SELECT * FROM scout WHERE Team=? ORDER BY Match ASC', (n,)).fetchall()

            for index, e in enumerate(entries):
                if (not isinstance(e, tuple)):
                    dp = game.generateChartData(e)

                    for key, val in dp.items():
                        dp[key] = round(val, 2)
                    if not e['Flag']:
                        if len(dataset) < (index + 1):
                            if stat2:
                                dataPoint = {"match": (index + 1), "team" + n + "stat1": dp[stat1],
                                             "team" + n + "stat2": dp[stat2]}
                            else:
                                dataPoint = {"match": (index + 1), "team" + n + "stat1": dp[stat1]}
                            dataset.append(dataPoint)
                        else:
                            dataset[index]["team" + n + "stat1"] = dp[stat1]
                            if stat2:
                                dataset[index]["team" + n + "stat2"] = dp[stat2]

            teamCharts += '''// GRAPH
                            graph{0} = new AmCharts.AmGraph();
                            graph{0}.title = "{1}";
                            graph{0}.valueAxis = valueAxis;
                            graph{0}.type = "smoothedLine"; // this line makes the graph smoothed line.
                            graph{0}.lineColor = "{3}";
                            graph{0}.bullet = "round";
                            graph{0}.bulletSize = 8;
                            graph{0}.bulletBorderColor = "#FFFFFF";
                            graph{0}.bulletBorderAlpha = 1;
                            graph{0}.bulletBorderThickness = 2;
                            graph{0}.lineThickness = 2;
                            graph{0}.valueField = "{2}";
                            graph{0}.balloonText = "{1}<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                            chart.addGraph(graph{0});
                            '''.format(n + "_1", "Team " + n + stat1, "team" + n + "stat1", colors[idx])
            if stat2:
                teamCharts += '''// GRAPH
                graph{0} = new AmCharts.AmGraph();
                graph{0}.title = "{1}";
                graph{0}.valueAxis = valueAxis2;
                graph{0}.type = "smoothedLine"; // this line makes the graph smoothed line.
                graph{0}.lineColor = "{3}";
                graph{0}.bullet = "round";
                graph{0}.bulletSize = 8;
                graph{0}.bulletBorderColor = "#FFFFFF";
                graph{0}.bulletBorderAlpha = 1;
                graph{0}.bulletBorderThickness = 2;
                graph{0}.lineThickness = 2;
                graph{0}.valueField = "{2}";
                graph{0}.balloonText = "{1}<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                chart.addGraph(graph{0});
                '''.format(n + "_2", "Team " + n + stat2, "team" + n + "stat2", colors[4 + idx])

        statSelector = '''<div id="statSelect" style="margin:auto;">
                    <form method="post" action="" style="display:inline-block; margin:5px">
                            <select class="fieldsm" name="stat1">'''
        for key in game.CHART_FIELDS:
            if (key != "match"):
                statSelector += '''<option id="{0}" value="{0}">{0}</option>'''.format(key)
        statSelector += '''</select>
                          <select class="fieldsm" name="stat2">
                              <option id="none" value="none">None</option>'''
        for key in game.CHART_FIELDS:
            if (key != "match"):
                statSelector += '''<option id="{0}2" value="{0}">{0}</option>'''.format(key)
        statSelector += '''</select>
                          <button class="submit" type="submit">Submit</button>
                          </form>
                          </div>'''
        with open('web/teams.html', 'r') as file:
            page = file.read()
        return page.format(str(dataset).replace("'", '"'), teamCharts, stat1, stat2 + "2", output, statSelector)

    # Output for alliance comparison
    @cherrypy.expose()
    def alliances(self, b1='', b2='', b3='', r1='', r2='', r3='', mode='', level=''):
        authCheck()
        if mode == '':
            mode = 'averages'
        if level == '':
            level = 'quals'
        numsBlue = [b1, b2, b3]
        numsRed = [r1, r2, r3]
        averages = []
        conn = sql.connect(self.datapath())
        conn.row_factory = sql.Row
        cursor = conn.cursor()

        teamsBlue = []
        teamsRed = []
        blueStatbox = ""
        # iterate through all six teams and grab data
        for i, n in enumerate(numsBlue):
            if not n.isdigit():
                raise cherrypy.HTTPError(400, "You fool! Enter six valid team numbers!")
            entries = cursor.execute('SELECT * FROM scout WHERE Team=? ORDER BY Match DESC', (n,)).fetchall()
            prevEvent = 0
            if len(entries) < 3:
                globalconn = sql.connect('global.db')
                globalconn.row_factory = sql.Row
                globalcursor = globalconn.cursor()
                teamEvents = globalcursor.execute('SELECT * FROM teamEvents WHERE Team=?', (n,)).fetchone()
                if teamEvents:
                    for i in range(1, 10):
                        if teamEvents['Event' + str(i)]:
                            if teamEvents['Event' + str(i)] != cherrypy.session['event']:
                                lastEventCode = teamEvents['Event' + str(i)]
                                lastEvent = 1
                if lastEvent:
                    oldconn = sql.connect('data_' + lastEventCode + '.db')
                    oldconn.row_factory = sql.Row
                    oldcursor = oldconn.cursor()
                    oldAverages = oldcursor.execute('SELECT * FROM averages WHERE Team=?', (n,)).fetchall()
                    assert len(oldAverages) < 2  # ensure there aren't two entries for one team
                    if len(oldAverages):
                        oldData = oldAverages[0]
                        blueStatbox += '''<div class="comparebox_container">
                    <p><a href="/team?n={0}" style="font-size: 32px;">Last Event - {0}</a></p>
                    <div class="statbox_container">
                        <div id="stats">'''.format(n)
                        for key in game.AVERAGE_FIELDS:
                            if (key != 'Team'):
                                blueStatbox += '''<p class="statbox">{0}: {1}</p>'''.format(key, oldData[key])
                        blueStatbox += '''       </div>
                                    </div>
                                 </div>'''
                        prevEvent = 1

            if prevEvent == 0:
                if mode == 'averages':
                    average = cursor.execute('SELECT * FROM averages WHERE Team=?', (n,)).fetchall()
                else:
                    average = cursor.execute('SELECT * FROM maxes WHERE Team=?', (n,)).fetchall()
                assert len(average) < 2
                if len(average):
                    entry = average[0]
                else:
                    entry = dict(game.AVERAGE_FIELDS)
                    entry.update(game.HIDDEN_AVERAGE_FIELDS)
                blueStatbox += '''<div class="comparebox_container">
                      <p><a href="/team?n={0}" style="font-size: 32px;">Team {0}</a></p>
                      <div class="statbox_container">
                          <div id="stats">'''.format(n)
                for key in game.AVERAGE_FIELDS:
                    if (key != 'Team'):
                        blueStatbox += '''<p class="statbox">{0}: {1}</p>'''.format(key, entry[key])
                # if cherrypy.session['auth'] == serverinfo.AUTH:
                #  for key in game.HIDDEN_AVERAGE_FIELDS:
                #    blueStatbox += '''<p class="statbox">{0}: {1}</p>'''.format(key, entry[key])
                blueStatbox += '''       </div>
                              </div>
                           </div>'''

        redStatbox = ""
        for i, n in enumerate(numsRed):
            if not n.isdigit():
                raise cherrypy.HTTPError(400, "You fool! Enter six valid team numbers!")
            entries = cursor.execute('SELECT * FROM scout WHERE Team=? ORDER BY Match DESC', (n,)).fetchall()
            prevEvent = 0
            if len(entries) < 3:
                globalconn = sql.connect('global.db')
                globalconn.row_factory = sql.Row
                globalcursor = globalconn.cursor()
                teamEvents = globalcursor.execute('SELECT * FROM teamEvents WHERE Team=?', (n,)).fetchone()
                if teamEvents:
                    for i in range(1, 10):
                        if teamEvents['Event' + str(i)]:
                            if teamEvents['Event' + str(i)] != cherrypy.session['event']:
                                lastEventCode = teamEvents['Event' + str(i)]
                                lastEvent = 1
                if lastEvent:
                    oldconn = sql.connect('data_' + lastEventCode + '.db')
                    oldconn.row_factory = sql.Row
                    oldcursor = oldconn.cursor()
                    oldAverages = oldcursor.execute('SELECT * FROM averages WHERE Team=?', (n,)).fetchall()
                    assert len(oldAverages) < 2  # ensure there aren't two entries for one team
                    if len(oldAverages):
                        oldData = oldAverages[0]
                        redStatbox += '''<div class="comparebox_container">
                    <p><a href="/team?n={0}" style="font-size: 32px;">Last Event - {0}</a></p>
                    <div class="statbox_container">
                        <div id="stats">'''.format(n)
                        for key in game.AVERAGE_FIELDS:
                            if (key != 'Team'):
                                redStatbox += '''<p class="statbox">{0}: {1}</p>'''.format(key, oldData[key])
                        redStatbox += '''       </div>
                                    </div>
                                 </div>'''
                        prevEvent = 1
            if prevEvent == 0:
                if mode == 'averages':
                    average = cursor.execute('SELECT * FROM averages WHERE Team=?', (n,)).fetchall()
                else:
                    average = cursor.execute('SELECT * FROM maxes WHERE Team=?', (n,)).fetchall()
                assert len(average) < 2
                if len(average):
                    entry = average[0]
                else:
                    entry = dict(game.AVERAGE_FIELDS)
                    entry.update(game.HIDDEN_AVERAGE_FIELDS)
                redStatbox += '''<div class="comparebox_container">
                      <p><a href="/team?n={0}" style="font-size: 32px;">Team {0}</a></p>
                      <div class="statbox_container">
                          <div id="stats">'''.format(n)
                for key in game.AVERAGE_FIELDS:
                    if (key != 'Team'):
                        redStatbox += '''<p class="statbox">{0}: {1}</p>'''.format(key, entry[key])
                # if cherrypy.session['auth'] == serverinfo.AUTH:
                # for key in game.HIDDEN_AVERAGE_FIELDS:
                #  redStatbox += '''<p class="statbox">{0}: {1}</p>'''.format(key, entry[key])
                redStatbox += '''       </div>
                              </div>
                              </div>'''

        # Predict scores
        blue_score = game.predictScore(self.datapath(), numsBlue, level)['score']
        red_score = game.predictScore(self.datapath(), numsRed, level)['score']
        blue_score = int(blue_score)
        red_score = int(red_score)

        # Calculate win probability. Currently uses regression from 2016 data, this should be updated
        prob_red = 1 / (1 + math.e ** (-0.08099 * (red_score - blue_score)))
        conn.close()
        with open('web/alliances.html', 'r') as file:
            page = file.read()
        return page.format(round((1 - prob_red) * 100, 1), blue_score, blueStatbox, round(prob_red * 100, 1), red_score,
                           redStatbox)

    # Lists schedule data from TBA
    @cherrypy.expose()
    def matches(self, n=0):
        authCheck()
        n = int(n)
        event = self.getevent()
        datapath = 'data_' + event + '.db'
        self.database_exists(event)
        conn = sql.connect(datapath)
        conn.row_factory = sql.Row
        cursor = conn.cursor()

        # Get match data
        m = self.getMatches(event)

        output = ''

        if 'feed' in m:
            raise cherrypy.HTTPError(503, "Unable to retrieve data about this event.")

        # assign weights, so we can sort the matches
        for match in m:
            match['value'] = match['match_number']
            type = match['comp_level']
            if type == 'qf':
                match['value'] += 1000
            elif type == 'sf':
                match['value'] += 2000
            elif type == 'f':
                match['value'] += 3000

        m = sorted(m, key=lambda k: k['value'])

        # For each match, generate a row in the table
        for match in m:
            if match['comp_level'] != 'qm':
                match['num'] = match['comp_level'].upper() + str(match['set_number']) + '_' + str(match['match_number'])
            else:
                match['num'] = match['match_number']
                if match['alliances']['blue']['score'] == -1:
                    match['alliances']['blue']['score'] = ""
                if match['alliances']['red']['score'] == -1:
                    match['alliances']['red']['score'] = ""
            blueTeams = [match['alliances']['blue']['team_keys'][0][3:], match['alliances']['blue']['team_keys'][1][3:],
                         match['alliances']['blue']['team_keys'][2][3:]]
            blueResult = game.predictScore(self.datapath(), blueTeams)
            blueRP = blueResult['RP1'] + blueResult['RP2']
            redTeams = [match['alliances']['red']['team_keys'][0][3:], match['alliances']['red']['team_keys'][1][3:],
                        match['alliances']['red']['team_keys'][2][3:]]
            redResult = game.predictScore(self.datapath(), redTeams)
            redRP = redResult['RP1'] + redResult['RP2']
            if (redResult['score'] > blueResult['score']):
                prediction = "Red +" + str(round(redResult['score'] - blueResult['score'], 2))
                prediction += "+" if (redResult['RP1']) else ""
                prediction += "+" if (redResult['RP2']) else ""
                prediction += "-" if (blueResult['RP1']) else ""
                prediction += "-" if (blueResult['RP2']) else ""
            else:
                prediction = "Blue +" + str(round(blueResult['score'] - redResult['score'], 2))
                prediction += "+" if (blueResult['RP1']) else ""
                prediction += "+" if (blueResult['RP2']) else ""
                prediction += "-" if (redResult['RP1']) else ""
                prediction += "-" if (redResult['RP2']) else ""
            output += '''
                <tr role="row" id="match_{0}">
                    <td><a href="alliances?b1={1}&b2={2}&b3={3}&r1={4}&r2={5}&r3={6}">{0}</a></td>
                    <td id="team1_{0}" class="hidden-xs"><a href="/team?n={1}">{1}</a></td>
                    <td id="team2_{0}" class="hidden-xs"><a href="/team?n={2}">{2}</a></td>
                    <td id="team3_{0}" class="hidden-xs"><a href="/team?n={3}">{3}</a></td>
                    <td id="team4_{0}" class="hidden-xs"><a href="/team?n={4}">{4}</a></td>
                    <td id="team5_{0}" class="hidden-xs"><a href="/team?n={5}">{5}</a></td>
                    <td id="team6_{0}" class="hidden-xs"><a href="/team?n={6}">{6}</a></td>
                    <td class="hidden-xs">{7}</td>
                    <td class="hidden-xs">{8}</td>
                    <td class="hidden-xs">{9}</td>
                    
                    <td class="rankingColumn rankColumn1 hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{1}</td>
                    <td class="rankingColumn rankColumn2 hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{2}</td>
                    <td class="rankingColumn rankColumn3 hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{3}</td>
                    <td class="rankingColumn rankColumn4 hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{4}</td>
                    <td class="rankingColumn rankColumn5 hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{5}</td>
                    <td class="rankingColumn rankColumn6 hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{6}</td>
                    <td class="rankingColumn rankColumn7 hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{7}</td>
                    <td class="rankingColumn rankColumn8 hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{8}</td>
                    <td class="rankingColumn rankColumn9 hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{9}</td>
                </tr>
            '''.format(match['num'], match['alliances']['blue']['team_keys'][0][3:],
                       match['alliances']['blue']['team_keys'][1][3:], match['alliances']['blue']['team_keys'][2][3:],
                       match['alliances']['red']['team_keys'][0][3:], match['alliances']['red']['team_keys'][1][3:],
                       match['alliances']['red']['team_keys'][2][3:], match['alliances']['blue']['score'],
                       match['alliances']['red']['score'], prediction)

        with open('web/matches.html', 'r') as file:
            page = file.read()
        return page.format(output)

    # Used by the scanning program to submit data, and used by comment system to submit dat
    @cherrypy.expose()
    def submit(self, auth='', data='', pitData='', event='', team='', comment=''):
        if not (data or team or pitData):
            return '''
                <h1>FATAL ERROR</h1>
                <h3>DATA CORRUPTION</h3>'''

        if data == 'json':
            return '[]'  # bogus json for local version

        if not event:
            event = self.getevent()
        datapath = 'data_' + event + '.db'
        self.database_exists(event)
        conn = sql.connect(datapath)
        conn.row_factory = sql.Row
        cursor = conn.cursor()

        # If team is defined, this should be a comment
        if team:
            if not comment:
                conn.close()
                raise cherrypy.HTTPRedirect('/team?n=' + str(team))
            if not cherrypy.session['auth'] == serverinfo.AUTH:
                conn.close()
                raise cherrypy.HTTPError(401, "Error: Not authorized to submit comments. Please login and try again")
            cursor.execute('INSERT INTO comments VALUES (?, ?)', (team, comment))
            conn.commit()
            conn.close()
            raise cherrypy.HTTPRedirect('/team?n=' + str(team))

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
                        match = next((item for item in m if
                                      (item['match_number'] == d['Match']) and (item['comp_level'] == 'qm')))
                        teams = match['alliances']['blue']['team_keys'] + match['alliances']['red']['team_keys']
                        if not 'frc' + str(d['Team']) in teams:
                            flag = 1
                except:
                    pass

                # If replay is marked, replace previous data
                if d['Replay']:  # replay
                    cursor.execute('DELETE from scout WHERE Team=? AND Match=?', (str(d['Team']), str(d['Match'])))

                # Insert data into database
                cursor.execute('INSERT INTO scout VALUES (NULL,' + ','.join([str(a) for a in d.values()]) + ')')
                conn.commit()
                conn.close()

                # Recalc stats for new data
                self.calcavg(d['Team'], event)
                return ''
            elif pitData:
                d = literal_eval(pitData)
                try:
                    cursor.execute('DELETE from pitScout WHERE Team=?', str(d['Team']))
                except:
                    pass
                cursor.execute('INSERT INTO pitScout VALUES (' + ','.join([str(a) for a in d.values()]) + ')')
                conn.commit()
                conn.close()
                return ''
        else:
            raise cherrypy.HTTPError(401, "Error: Not authorized to submit match data")

    # Calculates average scores for a team
    def calcavg(self, n, event):
        datapath = 'data_' + event + '.db'
        conn = sql.connect(datapath)
        conn.row_factory = sql.Row
        cursor = conn.cursor()

        # Check if this team has been added for this event in the globalDB and add if not
        globalconn = sql.connect('global.db')
        globalconn.row_factory = sql.Row
        globalcursor = globalconn.cursor()
        teamEntry = globalcursor.execute('SELECT * FROM teamEvents WHERE Team=?', (n,)).fetchone()
        if (teamEntry):
            for i in range(1, 10):
                if teamEntry['Event' + str(i)] == event:
                    break;
                else:
                    if not teamEntry['Event' + str(i)]:
                        updateString = 'UPDATE teamEvents SET Event' + str(i) + " = '" + event + "' WHERE Team=" + str(
                            n)
                        globalcursor.execute(updateString)
                        break;
        else:
            globalcursor.execute('INSERT INTO teamEvents (Team,Event1) VALUES (?,?)', (n, event))
        globalconn.commit()
        globalconn.close()

        # Delete the existing entries, if a team has no matches they will be removed
        cursor.execute('DELETE FROM averages WHERE Team=?', (n,))
        cursor.execute('DELETE FROM median WHERE Team=?', (n,))
        cursor.execute('DELETE FROM maxes WHERE Team=?', (n,))
        cursor.execute('DELETE FROM lastThree WHERE Team=?', (n,))
        cursor.execute('DELETE FROM noDefense WHERE Team=?', (n,))
        cursor.execute('DELETE FROM trends WHERE Team=?', (n,))

        entries = cursor.execute('SELECT * FROM scout WHERE Team=? AND flag=0 ORDER BY Match DESC', (n,)).fetchall()
        # If match entries exist, calc stats and put into appropriate tables
        if entries:
            totals = game.calcTotals(entries)
            for key in totals:
                totals[key]['Team'] = n
                # replace the data entries with new ones
                cursor.execute(
                    'INSERT INTO ' + key + ' VALUES (' + ','.join([str(a) for a in totals[key].values()]) + ')')
        conn.commit()
        conn.close()

    # Return the path to the database for this event
    def datapath(self):
        return 'data_' + self.getevent() + '.db'

    # Return the selected event
    def getevent(self):
        if 'event' not in cherrypy.session:
            cherrypy.session['event'] = CURRENT_EVENT
        return cherrypy.session['event']

    def getMatches(self, event, team=''):
        headers = {"X-TBA-Auth-Key": "n8QdCIF7LROZiZFI7ymlX0fshMBL15uAzEkBgtP1JgUpconm2Wf49pjYgbYMstBF"}
        try:
            if team:
                # request a specific team
                m = requests.get(
                    "http://www.thebluealliance.com/api/v3/team/frc{0}/event/{1}/matches".format(team, event),
                    params=headers)
            else:
                # get all the matches from this event
                m = requests.get("http://www.thebluealliance.com/api/v3/event/{0}/matches".format(event),
                                 params=headers)
            if m.status_code == 400 or m.status_code == 404:
                raise Exception
            if m.text != '[]':
                with open(event + "_matches.json", "w+") as file:
                    file.write(str(m.text))
                m = m.json()
            else:
                m = []
        except:
            try:
                with open(event + '_matches.json') as matches_data:
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
            a = '[]'
        return a

    def database_exists(self, event):
        datapath = 'data_' + event + '.db'
        if not os.path.isfile(datapath):
            # Generate a new database with the tables
            conn = sql.connect(datapath)
            cursor = conn.cursor()
            tableCreate = "CREATE TABLE scout (key INTEGER PRIMARY KEY, "
            for key in game.SCOUT_FIELDS:
                tableCreate += key + " integer, "
            tableCreate = tableCreate[:-2]
            tableCreate += ")"
            cursor.execute(tableCreate)
            tableCreate = "CREATE TABLE pitScout ("
            for key in game.PIT_SCOUT_FIELDS:
                tableCreate += key + " integer, "
            tableCreate = tableCreate[:-2] + ")"
            cursor.execute(tableCreate)
            tableCreate = "("
            for key in game.AVERAGE_FIELDS:
                tableCreate += key + " real, "
            for key in game.HIDDEN_AVERAGE_FIELDS:
                tableCreate += key + " real, "
            tableCreate = tableCreate[:-2] + ")"
            cursor.execute('''CREATE TABLE averages ''' + tableCreate)
            cursor.execute('''CREATE TABLE maxes ''' + tableCreate)
            cursor.execute('''CREATE TABLE lastThree ''' + tableCreate)
            cursor.execute('''CREATE TABLE noDefense ''' + tableCreate)
            cursor.execute('''CREATE TABLE median ''' + tableCreate)
            cursor.execute('''CREATE TABLE trends''' + tableCreate)
            cursor.execute('''CREATE TABLE comments (team integer, comment text)''')
            conn.close()
        # next check for the global database
        if not os.path.isfile('global.db'):
            globalconn = sql.connect('global.db')
            globalcursor = globalconn.cursor()
            globalcursor.execute(
                '''CREATE TABLE teamEvents (Team integer, Event1 text, Event2 text, Event3 text, Event4 text, Event5 text, Event6 text, Event7 text, Event8 text, Event9 text, Event10 text)''')
            globalconn.commit()
            globalconn.close()

    # Page for editing match data
    @cherrypy.expose()
    def edit(self, key='', **params):
        datapath = 'data_' + self.getevent() + '.db'
        conn = sql.connect(datapath)
        conn.row_factory = sql.Row
        cursor = conn.cursor()

        if not cherrypy.session['auth'] == serverinfo.AUTH:
            raise cherrypy.HTTPError(401, "Not authorized to edit match data. Please log in and try again")

        # If there is data, this is a post and data should be used to update the entry
        if len(params) > 1:
            sqlCommand = 'UPDATE scout SET '
            for name, value in params.items():
                sqlCommand += name + '=' + (value if value else 'NULL') + " , "
            sqlCommand = sqlCommand[:-2]
            sqlCommand += 'WHERE key=' + str(key)
            cursor.execute(sqlCommand)
            conn.commit()
            conn.close()
            self.calcavg(params['Team'], self.getevent())

        # Grab all match data entries from the event, with flagged entries first, then sorted by team, then match
        conn = sql.connect(datapath)
        conn.row_factory = sql.Row
        cursor = conn.cursor()
        entries = cursor.execute('SELECT * from scout ORDER BY flag DESC, Team ASC, Match ASC').fetchall()

        if key == '':
            key = entries[0][0]
        combobox = ''

        # Generate the entry selection dropdown, placing a * in front of flagged entries
        for e in entries:
            combobox += '''<option id="{0}" value="{0}">{1} Team {2}: Match {3}</option>\n'''.format(e['Key'], "*" if e[
                'Flag'] else "", e['Team'], e['Match'])

        # Grab the currently selected entry
        entry = cursor.execute('SELECT * from scout WHERE key=?', (key,)).fetchone()
        conn.close()

        # Generate the Edit interface, with half the data on the left and half on the right
        i = 0
        leftEdit = ''
        rightEdit = ''
        for key in game.SCOUT_FIELDS:
            if (key == 'Replay'):
                continue
            if (i < len(game.SCOUT_FIELDS) / 2):
                leftEdit += '''<div><label for="team" class="editLabel">{0}</label>
                            <input class="editNum" type="number" name="{0}" value="{1}"></div>'''.format(key,
                                                                                                         entry[key])
            else:
                rightEdit += '''<div><label for="team" class="editLabel">{0}</label>
                            <input class="editNum" type="number" name="{0}" value="{1}"></div>'''.format(key,
                                                                                                         entry[key])
            i = i + 1
        with open('web/edit.html', 'r') as file:
            page = file.read()
        return page.format(combobox, entry['Team'], entry['Match'], entry['Key'], leftEdit, rightEdit)

    # Page to show current rankings, and predict final rankings
    @cherrypy.expose()
    def rankings(self):
        event = self.getevent()
        datapath = 'data_' + event + '.db'
        self.database_exists(event)
        conn = sql.connect(datapath)
        conn.row_factory = sql.Row
        cursor = conn.cursor()

        rankings = {}

        # Grab latest rankings and match data from TBA
        headers = {"X-TBA-Auth-Key": "n8QdCIF7LROZiZFI7ymlX0fshMBL15uAzEkBgtP1JgUpconm2Wf49pjYgbYMstBF"}
        m = requests.get("http://www.thebluealliance.com/api/v3/event/{0}/matches".format(event), params=headers)
        r = requests.get("http://www.thebluealliance.com/api/v3/event/{0}/rankings".format(event), params=headers)
        if 'feed' in m:
            raise cherrypy.HTTPError(503, "Unable to retrieve data about this event.")
        if r.text != '[]':
            r = r.json()
        else:
            raise cherrypy.HTTPError(503, "Unable to retrieve rankings data for this event.")
        if m.text != '[]':
            m = m.json()
        else:
            raise cherrypy.HTTPError(503, "Unable to retrieve match data for this event.")

        # Process current rankings into dict
        for item in r["rankings"]:
            rankings[item["team_key"][3:]] = {'rp': round(item["sort_orders"][0] * item["matches_played"], 0),
                                              'matchScore': item["sort_orders"][1],
                                              'currentRP': round(item["sort_orders"][0] * item["matches_played"], 0),
                                              'currentMatchScore': item["sort_orders"][1]}

        # Iterate through all matches
        for match in m:
            if match['comp_level'] == 'qm':
                # Un-played matches show a score of -1. Predict the outcome
                if match['alliances']['blue']['score'] == -1:
                    blueTeams = [match['alliances']['blue']['team_keys'][0][3:],
                                 match['alliances']['blue']['team_keys'][1][3:],
                                 match['alliances']['blue']['team_keys'][2][3:]]
                    blueResult = game.predictScore(self.datapath(), blueTeams)
                    blueRP = blueResult['RP1'] + blueResult['RP2']
                    redTeams = [match['alliances']['red']['team_keys'][0][3:],
                                match['alliances']['red']['team_keys'][1][3:],
                                match['alliances']['red']['team_keys'][2][3:]]
                    redResult = game.predictScore(self.datapath(), redTeams)
                    redRP = redResult['RP1'] + redResult['RP2']
                    if blueResult['score'] > redResult['score']:
                        blueRP += 2
                    elif redResult['score'] > blueResult['score']:
                        redRP += 2
                    else:
                        redRP += 1
                        blueRP += 1
                    for team in blueTeams:
                        rankings[team]['rp'] += blueRP
                        rankings[team]['matchScore'] += blueResult['score']
                    for team in redTeams:
                        rankings[team]['rp'] += redRP
                        rankings[team]['matchScore'] += redResult['score']

        # Sort rankings, then output into table
        output = ''
        for index, out in enumerate(
                sorted(rankings.items(), key=keyFromItem(lambda k, v: (v['rp'], v['matchScore'])), reverse=True)):
            output += '''
            <tr role="row">
                <td>{0}</td>
                <td><a href="/team?n={1}">{1}</a></td>
                <td class="hidden-xs">{2}</td>
                <td class="hidden-xs">{3}</td>
                <td class="hidden-xs">{4}</td>
                <td class="hidden-xs">{5}</td>
               

                
                <td class="rankingColumn rankColumn1 hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{2}</td>
                <td class="rankingColumn rankColumn2 hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{3}</td>
                <td class="rankingColumn rankColumn3 hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{4}</td>
                <td class="rankingColumn rankColumn4 hidden-sm hidden-md hidden-lg hidden-xs" style="display: none;">{5}</td>
               
            </tr>
            '''.format(index + 1, out[0], (int)(out[1]['rp']), (int)(out[1]['matchScore']), (int)(out[1]['currentRP']),
                       (int)(out[1]['currentMatchScore']))
        with open('web/rankings.html', 'r') as file:
            page = file.read()
        return page.format(output)
        # END OF CLASS


# Execution starts here
datapath = 'data_' + CURRENT_EVENT + '.db'


# Helper function used in rankings sorting
def keyFromItem(func):
    return lambda item: func(*item)


def authCheck():
    if 'auth' not in cherrypy.session:
        if localInstance:
            cherrypy.session['auth'] = serverinfo.AUTH
            cherrypy.session['admin'] = serverinfo.ADMIN
        else:
            cherrypy.session['auth'] = ""
            cherrypy.session['admin'] = ""


# Configuration used for local instance of the server
localConf = {
    '/': {
        'tools.sessions.on': True,
        'tools.staticdir.root': os.path.abspath(os.getcwd())
    },
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': './web/static'
    },
    '/favicon.ico': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': os.path.abspath(os.getcwd()) + './web/static/img/favicon.ico'
    },
    'global': {
        'server.socket_port': 8000
    }
}

# Configuration for remote instance of the server
remoteConf = {
    '/': {
        'tools.sessions.on': True,
        'tools.staticdir.root': os.path.abspath(os.getcwd())
    },
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': './web/static'
    },
    '/favicon.ico': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': os.path.abspath(os.getcwd()) + './web/static/img/favicon.ico'
    },
    'global': {
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 80
    }
}

# Determine which config to launch based on command line args
if len(sys.argv) > 1:
    if sys.argv[1] == "-local":
        print("Starting local server")
        localInstance = True
        cherrypy.quickstart(ScoutServer(), '/', localConf)
    else:
        print("Starting remote server")
        cherrypy.quickstart(ScoutServer(), '/', remoteConf)
else:
    print("Starting remote server")
    cherrypy.quickstart(ScoutServer(), '/', remoteConf)
