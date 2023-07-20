import requests
import json
from auth import APIURL, HEADERS
from datetime import date, timedelta
from typing import List
from custom_types import Match


def get_matches(team_id: str, start_date: date, end_date: date, season: str) -> str:
    """Requests the relevant matches for the given team."""
    mresp = requests.get(
        f"{APIURL}/fixtures",
        params={
            "team": team_id,
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
    team_id: str, start_date: date = None, end_date: date = None, season: str = None
) -> List[Match]:
    today = date.today()
    if start_date is None:
        # Defaults to results from up to a week ago.
        start_date = today - timedelta(weeks=1, days=1)

    if end_date is None:
        # Future matches until end of next month.
        end_date = date(today.year, (today.month + 1) % 12 + 1, 1)

    if season is None:
        # Get the latest season from the team.
        sresp = requests.get(
            f"{APIURL}/teams/seasons", params={"team": f"{team_id}"}, headers=HEADERS
        )
        sresults = json.loads(sresp.text)
        season = sresults.get("response", [today.year])[-1]

    mresp = get_matches(team_id, start_date, end_date, season)
    return parse_matches(mresp)


if __name__ == "__main__":
    print(fetch(team_id=1062))
