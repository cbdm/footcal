import matches
from os import getenv
from flask import (
    Flask,
    make_response,
)
from ics import Calendar, Event
from datetime import timedelta

app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = getenv("FLASK_SECRET_KEY", "abc")


@app.route("/", methods=("GET",))
def index():
    return """<html>
    <head>
    <style>
    table {
    font-family: arial, sans-serif;
    border-collapse: collapse;
    width: 100%;
    }

    td, th {
    border: 1px solid #dddddd;
    text-align: left;
    padding: 8px;
    }

    tr:nth-child(even) {
    background-color: #dddddd;
    }
    </style>
    </head>
    <body>
    <h1>Hello!</h1>
    This is still a very rough draft from a WIP project, very few things have been implemented so far.<br/>
    Please feel free to contribute with PRs, suggestions, requests, etc. at <a href="https://github.com/cbdm/footcal">https://github.com/cbdm/footcal</a><br/>
    <br/>
    If you know the api-football ID for the team you want, you can create a calendar with /team/ID in this URL.<br/>
    If you used to use onefootball-ics before it stopped working, you can probably find the ID below:
    <table>
    <tr>
        <th>Old ID</th>
        <th>New ID</th>
    </tr>
    <tr>
        <td>atletico-mineiro-1683</td>
        <td>1062</td>
    </tr>
    <tr>
        <td>brazil-79</td>
        <td>6</td>
    </tr>
    <tr>
        <td>mexico-69</td>
        <td>16</td>
    </tr>
    <tr>
        <td>borussia-dortmund-155</td>
        <td>165</td>
    </tr>
    <tr>
        <td>internacional-1799</td>
        <td>119</td>
    </tr>
    </table>
    <br/>
    Feel free to reach out with any questions <a href="mailto:footcal@cbdm.app">footcal@cbdm.app</a>
    </body>
    </html>
    """


@app.route("/team/<team_id>/", methods=("GET",))
def team_cal(team_id):
    cal = Calendar()
    for m in matches.fetch(team_id):
        e = Event()
        sep = "-"
        if m.status == "FT":
            sep = f"({m.home_score}) - ({m.away_score})"
        e.name = f"[{m.league_name}] {m.home_team_name} {sep} {m.away_team_name}"
        e.begin = m.match_utc_ts
        e.duration = timedelta(hours=2)
        e.description = (
            f"""Venue: {m.venue_name} in {m.venue_city}.\nRef: {m.ref_name}."""
        )
        cal.events.add(e)

    response = make_response(f"{cal.serialize()}")
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    return response


if __name__ == "__main__":
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
