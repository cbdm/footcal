from dotenv import load_dotenv

load_dotenv()

import matches
import search
from os import getenv
from flask import (
    Flask,
    make_response,
    request,
    render_template,
    flash,
)
from ics import Calendar, Event
from datetime import timedelta
from custom_types import SearchQuotaExceeded
from auth import get_quota_reset
from cache import setupDB, list_cached_calendars

app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = getenv("FLASK_SECRET_KEY", "abc")

setupDB(app)


@app.route("/", methods=("GET",))
def index():
    return render_template(
        "index.html",
        team_list=sorted(list_cached_calendars(team=True), key=lambda x: x[1]),
        comp_list=sorted(list_cached_calendars(team=False), key=lambda x: x[1]),
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
                    f"The search couldn't be performed because we have exceeded our daily quota for performing searches. Sorry about that!\nYou can try again when it resets in {get_quota_reset()}s."
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
                    f"The search couldn't be performed because we have exceeded our daily quota for performing searches. Sorry about that!\nYou can try again when it resets in {get_quota_reset()}s."
                )

    return render_template("search.html", team=False)


@app.route("/help/", methods=("GET",))
def help_page():
    return render_template("help.html")


def _create_calendar(team, id):
    cal = Calendar()
    for m in matches.fetch(team=team, id=id):
        e = Event()
        sep = "-"
        if m.status in ("FT", "PEN"):
            sep = f"({m.home_score}) - ({m.away_score})"
        notes = matches.status_map.get(m.status, "")
        e.name = f"[{m.league_name}] {notes}{m.home_team_name} {sep} {m.away_team_name}"
        e.begin = m.match_utc_ts
        e.duration = timedelta(hours=2)
        e.description = (
            f"""Venue: {m.venue_name} in {m.venue_city}.\nRef: {m.ref_name}."""
        )
        cal.events.add(e)
    return cal


@app.route("/team/<team_id>/", methods=("GET",))
def team_cal(team_id):
    cal = _create_calendar(team=True, id=team_id)
    response = make_response(f"{cal.serialize()}")
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    return response


@app.route("/comp/<comp_id>/", methods=("GET",))
def comp_cal(comp_id):
    cal = _create_calendar(team=False, id=comp_id)
    response = make_response(f"{cal.serialize()}")
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    return response


if __name__ == "__main__":
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
