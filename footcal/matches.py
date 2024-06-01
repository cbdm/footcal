import requests
import json
import cache
from auth import APIURL, HEADERS
from datetime import date, timedelta
from typing import List
from custom_types import Match

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
    cached = cache.query(lookup_key, max_age=timedelta(days=1))
    if cached:
        return cached

    # Don't have a fresh cached copy, so let's create it.
    today = date.today()
    if start_date is None:
        # Defaults to results from up to a week ago.
        start_date = today - timedelta(weeks=1, days=1)

    if end_date is None:
        # Future matches until end of next month.
        end_date = today + timedelta(weeks=4)

    if season is None:
        if team:
            # Get the latest season for the team.
            sresp = requests.get(
                f"{APIURL}/teams/seasons", params={"team": f"{id}"}, headers=HEADERS
            )
            sresults = json.loads(sresp.text)
            seasons = [
                s for s in sresults.get("response", [today.year]) if s <= today.year
            ]
            season = seasons[-1]

        else:
            # Get the latest season for the competition.
            sresp = requests.get(
                f"{APIURL}/leagues", params={"id": id}, headers=HEADERS
            )
            sresults = json.loads(sresp.text)
            try:
                season = sresults["response"][0]["seasons"][-1]["year"]
            except KeyError:
                season = [today.year]

    mresp = get_matches(team, id, start_date, end_date, season)
    new_data = parse_matches(mresp)

    # Add the newly created calendar.
    cache.update(lookup_key, new_data)

    return new_data


if __name__ == "__main__":
    print(fetch(team=True, id=1062))
    print(fetch(team=False, id=2))
    print(fetch(team=True, id=6))
