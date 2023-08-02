import matches
import search
from os import getenv
from flask import (
    Flask,
    make_response,
    request,
)
from ics import Calendar, Event
from datetime import timedelta
from custom_types import SearchQuotaExceeded
from auth import get_quota_reset
from cache import list_cached_calendars

app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = getenv("FLASK_SECRET_KEY", "abc")


@app.route("/", methods=("GET",))
def index():
    cal_list = []
    for (ID, name) in sorted(list_cached_calendars(), key=lambda x: x[1]):
        row = f"<tr>\n\t<td>{name}</td>\n"
        row += f"\t<td>{ID}</td>\n"
        cal_url = f"{request.host_url}team/{ID}"
        row += f'\t<td><a href="{cal_url}">{cal_url}</a></td>\n'
        row += "</tr>\n"
        cal_list.append(row)

    return (
        """<html>
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
    If you're kinda lost, please check <a href="/help">/help</a>.<br/>
    <br/>
    This is still a very rough draft from a WIP project, very few things have been implemented so far.<br/>
    Please feel free to contribute with PRs, suggestions, requests, etc. at <a href="https://github.com/cbdm/footcal">https://github.com/cbdm/footcal</a><br/>
    <br/>
    If you know the api-football ID for the team you want, you can create a calendar with /team/ID in this URL.<br/>
    You can find the already created calendars in the table below:
    <table>
    <tr>
        <th>Team Name</th>
        <th>Team ID</th>
        <th>Calendar URL</th>
    </tr>
    """
        + "\n".join(cal_list)
        + """
    </table>
    <br/>
    If you need an ID for a different team, you can try going to <a href="/search">/search</a>.<br/>
    Feel free to reach out with any questions <a href="mailto:footcal@cbdm.app">footcal@cbdm.app</a>
    </body>
    </html>
    """
    )


@app.route("/search/", methods=("GET", "POST"))
def search_ID():
    if request.method == "POST":
        query = request.form.get("query", "").strip()

        result_html = """<html>
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
            <body><h1>Search results</h1>\n"""
        result_html += f"<h2>Search query: {query}</h2>\n"

        if not query:
            result_html += (
                "Cannot perform a blank search, please go back and try again."
            )

        else:
            try:
                teams = search.search_teams(query)
                result_html += """<table>
                    <tr>
                        <th></th>
                        <th>ID</th>
                        <th>Team Name</th>
                        <th>Short Name</th>
                        <th>Country</th>
                        <th>Founded</th>
                        <th>Club</th>
                    </tr>"""

                for t in teams:
                    result_html += f"""<tr>
                        <td><img src="{t.logo}" alt="{t.name}'s logo"></td>
                        <td>{t.id}</td>
                        <td>{t.name}</td>
                        <td>{t.short_name}</td>
                        <td>{t.country}</td>
                        <td>{t.founded}</td>
                        <td>{t.club}</td>
                    </tr>"""

                result_html += "</table>\n"

            except SearchQuotaExceeded:
                result_html += "The search couldn't be performed because we have exceeded our daily quota for performing searches. Sorry about that!\n"
                result_html += (
                    f"You can try again when it resets in {get_quota_reset()}s."
                )

        return result_html

    elif request.method == "GET":
        return """<h1>Search</h1>
        You can use the search box below to look for a team ID if you don't know it yet.<br/>
        <br/>
        <form method="post">
        <label for="query">Search query:</label>
        <input type="text" name="query" id="query"/>
        <input type="submit" value="Search">
        </form>
        """


@app.route("/help/", methods=("GET",))
def help_page():
    return f"""<h1>Help</h1>
    The goal of this website is to provide a calendar with football matches from your favorite teams.
    Each calendar would have a different URL, and then you can import these URLs into whatever app you use (e.g., Google Calendar).
    So you'd be able to see when that next important match is happening and be aware of conflicts when scheduling other things.<br/>
    <br/>
    So how do you get a calendar for, e.g., Atletico Mineiro (<a href="https://en.wikipedia.org/wiki/Clube_Atl%C3%A9tico_Mineiro">wiki</a>)?<br/>
    <ol>
        <li>
            The first thing you need to do is find out the ID for the club. If you don't know that yet, you can go to <a href="{request.host_url}search">{request.host_url}search</a> to look for it.
            You can type "atletico" in the search box and hit the button, then you should see a long list with a bunch of Atleticos there.
            For each team you should see their logo (if available), name, country, year it was founded, and ID.
            You can use these pieces of information together to find the correct row you need.
            For example, if you search for atletico, the first row seems to have the correct name we want "Aletico Mineiro".
            But all the other fields are missing: no logo, no year, no country.
            If we scroll down, you will find "Atletico-MG", which has the correct logo, year, and country.
            So this is the correct entry!
            From this row, we know that the ID for Atletico Mineiro is 1062.
        </li>
        <li>
            Next, once you know the ID for the team you want, you can create a URL that will have that team's game.
            Using the example above, we know the team ID is 1062.
            Then, we can get the base url for this websice ({request.host_url}) and add /team/1062 at the end.
            This would create a final url with <a href="{request.host_url}team/1062">{request.host_url}team/1062</a>, which is the calendar URL we need for the next step.
            If you want the calendar of a different team, you would just use the different ID in this part, replacing the information after the /team/.
        </li>
        <li>
            Finally, you can enter this URL into your calendar service.
            Keep in mind that by default (and with no current plans of changing), we only serve results from at most a week ago, and future matches that happen up to the end of the next calendar month.
            So, for example, if you're getting a calendar on 2023-07-20, it should have results from 2023-07-13 to 2023-07-19, and future matches from 2023-07-20 to 2023-08-31.<br/>
            But you don't need to worry!
            Since your calendar should request updates occasionally, you only need to add it once, and everything else should be self-updating.
            Whenever your calendar service asks for an update, it will be at a later day, and thus this window-ed calendar will move forward.
            The only downside is that we don't give you past results, but that's not the goal of this app :)
        </li>
    </ol>

    <h3>Google Calendar</h3>

    If you're using Google calendar, by default, custom calendars you subscribe with URLs are only visible in the web version.
    You'll need to go to syncselect (<a href="https://calendar.google.com/calendar/u/0/syncselect">https://calendar.google.com/calendar/u/0/syncselect</a>) to be able to access this calendar on your other devices.<br/>
    Other services might have something similar to this, but I'm not familiar with those, sorry.
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
