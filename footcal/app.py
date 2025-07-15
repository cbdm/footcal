from dotenv import load_dotenv

load_dotenv()

from datetime import datetime, timedelta
from os import getenv
from zoneinfo import ZoneInfo

import arrow
import cache
import matches
import requests
import search
from custom_types import SearchQuotaExceeded
from flask import Flask, flash, make_response, render_template, request
from icalendar import Calendar, Event

app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = getenv("FLASK_SECRET_KEY", "abc")

cache.setupDB(app)


@app.route("/", methods=("GET",))
def index():
    return render_template(
        "index.html",
        team_list=sorted(cache.list_cached_calendars(team=True), key=lambda x: x[1]),
        comp_list=sorted(cache.list_cached_calendars(team=False), key=lambda x: x[1]),
    )


@app.route("/search/", methods=("GET", "POST"))
def search_ID():
    if request.method == "POST":
        query = request.form.get("query", "").strip()

        if not query:
            flash("Cannot perform a blank search, please go back and try again.")

        else:
            try:
                teams = search.search_teams(query)
                return render_template(
                    "results.html", query=query, team=True, teams=teams
                )
            except SearchQuotaExceeded:
                flash(
                    "The search couldn't be performed because we have exceeded our daily quota for performing searches. Sorry about that!\nYou can try again later."
                )

    return render_template("search.html", team=True)


@app.route("/search-comp/", methods=("GET", "POST"))
def search_comp_ID():
    if request.method == "POST":
        query = request.form.get("query", "").strip()

        if not query:
            flash("Cannot perform a blank search, please go back and try again.")

        else:
            try:
                comps = search.search_comps(query)
                return render_template(
                    "results.html", query=query, team=False, comps=comps
                )
            except SearchQuotaExceeded:
                flash(
                    "The search couldn't be performed because we have exceeded our daily quota for performing searches. Sorry about that!\nYou can try again later."
                )

    return render_template("search.html", team=False)


@app.route("/help/", methods=("GET",))
def help_page():
    return render_template("help.html")


def _create_calendar(team, id):
    # Get the API data from cache.
    cache_data = matches.fetch(team=team, id=id)
    # Create calendar with required properties.
    cal = Calendar()
    cal.add("PRODID", "-//Footcal//footcal.cbdm.app//EN")
    cal.add("VERSION", "2.0")
    cal.add("CALSCALE", "GREGORIAN")
    cal.add("METHOD", "PUBLISH")
    cal.add("X-WR-CALNAME", cache_data["info"].name)
    cal.add("X-WR-TIMEZONE", "UTC")
    # Add one event for each match.
    dtstamp = datetime.now(tz=ZoneInfo("UTC"))
    for m in cache_data["matches"]:
        e = Event()
        sep = "-"
        if m.status in {"FT", "AET", "PEN"}:
            sep = f"({m.home_score}) - ({m.away_score})"
        notes = matches.status_map.get(m.status, "")

        start_dt = datetime.fromtimestamp(m.match_utc_ts, tz=ZoneInfo("UTC"))
        e.add("DTSTART", start_dt)
        e.add("DTEND", start_dt + timedelta(hours=2))
        e.add("DTSTAMP", dtstamp)
        local_uid = f"{start_dt.date()}_{m.league_id}_{m.home_team_id}_{m.away_team_id}"
        local_uid = local_uid.replace(" ", "_")
        e.add(
            "UID",
            f"{local_uid}@footcal.cbdm.app",
        )
        e.add("CREATED", dtstamp)
        e.add("DESCRIPTION", f"Ref: {m.ref_name}")
        e.add("LAST-MODIFIED", dtstamp)
        e.add("LOCATION", f"{m.venue_name}, {m.venue_city}")
        e.add("SEQUENCE", 0)
        e.add("STATUS", "CONFIRMED")
        e.add(
            "SUMMARY",
            f"[{m.league_name}] {notes}{m.home_team_name} {sep} {m.away_team_name}",
        )
        e.add("TRANSP", "OPAQUE")
        cal.add_component(e)
    return cal


@app.route("/team/<team_id>/", methods=("GET",))
def team_cal(team_id):
    cal = _create_calendar(team=True, id=team_id)
    response = make_response(f"{cal.to_ical(sorted=False).decode('utf-8')}")
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    response.headers["Content-Type"] = "text/calendar; charset=utf-8"
    return response


@app.route("/team/<team_id>/calendar.ics", methods=("GET",))
def team_cal_ics(team_id):
    return team_cal(team_id)


@app.route("/comp/<comp_id>/", methods=("GET",))
def comp_cal(comp_id):
    cal = _create_calendar(team=False, id=comp_id)
    response = make_response(f"{cal.to_ical(sorted=False).decode('utf-8')}")
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    response.headers["Content-Type"] = "text/calendar; charset=utf-8"
    return response


@app.route("/comp/<comp_id>/calendar.ics", methods=("GET",))
def comp_cal_ics(comp_id):
    return comp_cal(comp_id)


@app.route("/next/<type>/<id>/", methods=("GET",))
def next_match(type, id):
    cur_time = arrow.utcnow()

    if type not in ("team", "comp"):
        return {
            "teams": "N/A",
            "competition": "N/A",
            "start_time": f"{(cur_time + timedelta(days=29)).isoformat()}",
            "extra_info": f"ERROR: invalid type; accepted options are 'team' and 'comp', but receive '{type}'",
            "venue": "N/A",
            "ref": "N/A",
        }

    cal = _create_calendar(team=(type == "team"), id=id)
    next = None
    min_diff = timedelta(days=365)

    for e in cal.events:
        match_end = e.get("DTEND").dt
        time_diff = match_end - cur_time
        if time_diff < timedelta(seconds=0):
            continue
        if time_diff < min_diff:
            min_diff = time_diff
            next = e

    if next is None:
        return {
            "teams": "N/A",
            "competition": "N/A",
            "start_time": f"{(cur_time + timedelta(days=29)).isoformat()}",
            "extra_info": "Couldn't find a match in the next 4 weeks.",
            "venue": "N/A",
            "ref": "N/A",
        }

    brace_index = next.get("summary").index("]")
    competition = next.get("summary")[1:brace_index]
    teams = next.get("summary")[brace_index + 2 :]
    venue = next.get("location")
    ref = next.get("description")
    ref = ref[len("Ref: ") :]

    return {
        "teams": teams,
        "competition": competition,
        "start_time": f"{next.get('dtstart').dt.isoformat()}",
        "venue": venue,
        "ref": ref,
        "extra_info": "N/A",
    }


@app.route("/logo/<type>/<id>/", methods=("GET",))
def get_logo(type, id):
    # Check if the logo is cached.
    cache_key = f"logo/{type}/{id}"
    logo, unused_is_fresh = cache.query(cache_key, max_age=timedelta(weeks=104))
    if not logo:
        # If it is not cached yet, request the logo from the API.
        logo_base_url = "https://media.api-sports.io/football/{type}/{id}.png"
        new_logo_url = logo_base_url.format(
            id=id, type="teams" if type == "team" else "leagues"
        )
        resp = requests.get(new_logo_url, timeout=10)

        # If the request wasn't successful, return the same response.
        if resp.status_code != 200:
            return resp.content, resp.status_code, resp.headers.items()

        # If the request was succesful, cache the logo received.
        logo = resp.content
        cache.update(cache_key, logo)

    # Respond with the logo.
    return logo, 200, {"Content-Type": "image/png", "Content-Length": len(logo)}


if __name__ == "__main__":
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
