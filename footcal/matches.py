import requests
import json
import cache
from auth import APIURL, HEADERS, get_remaining_quota
from datetime import date, timedelta
from typing import List
from custom_types import Match, Team, Competition

# Maps the api-football status to messages to be displayed.
status_map = {
    "PST": "(Postponed) ",
    "CANC": "(Cancelled) ",
    "ABD": "(Abandoned) ",
    "AWD": "(Not Played) ",
    "WO": "(Not Played) ",
}


def get_matches(
    team: bool, id: str, start_date: date, end_date: date, season: str
) -> str:
    """Requests the relevant matches for the given team/competition."""
    mresp = requests.get(
        f"{APIURL}/fixtures",
        params={
            "team" if team else "league": id,
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "season": season,
        },
        headers=HEADERS,
    )

    return mresp.text


def parse_matches(mresp: str) -> List[Match]:
    """Parses the response into Match objects that will be used to create calendars."""
    data = json.loads(mresp)["response"]
    return [
        Match(
            id=match["fixture"]["id"],
            ref_name=match["fixture"]["referee"],
            match_utc_ts=match["fixture"]["timestamp"],
            venue_id=match["fixture"]["venue"]["id"],
            venue_name=match["fixture"]["venue"]["name"],
            venue_city=match["fixture"]["venue"]["city"],
            league_id=match["league"]["id"],
            league_name=match["league"]["name"],
            home_team_id=match["teams"]["home"]["id"],
            home_team_name=match["teams"]["home"]["name"],
            away_team_id=match["teams"]["away"]["id"],
            away_team_name=match["teams"]["away"]["name"],
            status=match["fixture"]["status"]["short"],
            home_score=match["score"].get("fulltime", {}).get("home"),
            away_score=match["score"].get("fulltime", {}).get("away"),
        )
        for match in data
    ]


def fetch(
    team: bool,
    id: str,
    start_date: date = None,
    end_date: date = None,
    season: str = None,
) -> List[Match]:
    # Check if we have this calendar cached.
    lookup_key = f"{'team' if team else 'comp'}-cal/{id}"
    cached, fresh = cache.query(lookup_key, max_age=timedelta(days=1))

    # Return cached data if it's still fresh.
    if fresh:
        return cached

    # Return cached data even if it's old if we're over the daily quota.
    if cached and (get_remaining_quota() <= 0):
        return cached

    # Replace None with an empty dict so it's easier to work with.
    if cached is None:
        cached = {}

    # Get today's date to find season's year and future games.
    today = date.today()

    # Search information for the team or competition if it hasn't been cached or the season for competition is over.
    obj = cached.get("info")
    if obj is None or ((not team) and (obj.season_end < today.isoformat())):
        if team:
            tresp = requests.get(
                f"{APIURL}/teams", params={"id": f"{id}"}, headers=HEADERS
            )
            data = json.loads(tresp.text)["response"][0]
            obj = Team(
                id=data["team"]["id"],
                name=data["team"]["name"],
                short_name=data["team"]["code"],
                country=data["team"]["country"],
                founded=data["team"]["founded"],
                club=not data["team"]["national"],
                logo=data["team"]["logo"],
            )

        else:
            cresp = requests.get(
                f"{APIURL}/leagues", params={"id": f"{id}"}, headers=HEADERS
            )
            data = json.loads(cresp.text)["response"][0]
            obj = Competition(
                id=data["league"]["id"],
                name=data["league"]["name"],
                type=data["league"]["type"],
                logo=data["league"]["logo"],
                country_name=data["country"]["name"],
                country_code=data["country"]["code"],
                season=data["seasons"][-1]["year"],
                season_start=data["seasons"][-1]["start"],
                season_end=data["seasons"][-1]["end"],
            )

    # Check if could not find any information for the given ID.
    if obj is None:
        return None

    # Create default calendar window if not given.
    if start_date is None:
        # Defaults to results from up to a week ago.
        start_date = today - timedelta(weeks=1, days=1)

    if end_date is None:
        # Future matches for the next three months.
        end_date = today + timedelta(weeks=12)

    # Find the current season to query the matches.
    # TODO: Could add a timestamp of when the season was updated and only recheck after a week or so.
    season = season if season else cached.get("season")
    if season is None or (cached and (not cached.get("matches"))):
        if team:
            # Get the latest season for the team.
            sresp = requests.get(
                f"{APIURL}/teams/seasons", params={"team": f"{id}"}, headers=HEADERS
            )
            sresults = json.loads(sresp.text)

            # Filter current/past years only.
            seasons = [
                s for s in sresults.get("response", [today.year]) if s <= today.year
            ]

            # Get most recent one.
            season = seasons[-1]

        else:
            # Get the latest season for the competition.
            season = obj.season

    # Request and parse matches.
    mresp = get_matches(team, id, start_date, end_date, season)
    matches = parse_matches(mresp)

    # Create cache entry.
    new_data = {
        "info": obj,
        "season": season,
        "matches": matches,
    }

    # Add the newly created calendar.
    cache.update(lookup_key, new_data)

    return new_data


if __name__ == "__main__":
    print(fetch(team=True, id=1062))
    print(fetch(team=False, id=2))
    print(fetch(team=True, id=6))
