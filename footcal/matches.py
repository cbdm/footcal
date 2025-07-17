import json
from datetime import date, timedelta
from typing import List

import cache
import requests
from auth import APIURL, HEADERS, REQUEST_TIMEOUT_S
from custom_types import Competition, Match, Team

# Maps the api-football status to messages to be displayed.
status_map = {
    "PST": "(Postponed) ",
    "CANC": "(Cancelled) ",
    "ABD": "(Abandoned) ",
    "AWD": "(Not Played) ",
    "WO": "(Not Played) ",
    "TBD": "(TBD) ",
}


def get_matches_in_window(
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
        timeout=REQUEST_TIMEOUT_S,
    )

    return mresp.text


def get_next_n_matches(team_id: str, n: int) -> str:
    """Requests the next n matches for the given **team**."""
    mresp = requests.get(
        f"{APIURL}/fixtures",
        params={
            "team": team_id,
            "next": n,
        },
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT_S,
    )
    return mresp.text


def get_last_n_matches(team_id: str, n: int) -> str:
    """Requests the last n matches for the given **team**."""
    mresp = requests.get(
        f"{APIURL}/fixtures",
        params={
            "team": team_id,
            "last": n,
        },
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT_S,
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


def fetch_team(
    team_id: str,
    num_next_games: int = 10,
    num_last_games: int = 5,
) -> List[Match]:
    # Check if we have this calendar cached.
    lookup_key = f"team-cal/{team_id}"
    cached, fresh = cache.query(lookup_key, max_age=timedelta(days=1))

    # Return cached data if it's still fresh.
    if fresh:
        return cached

    # Replace None with an empty dict so it's easier to work with.
    if cached is None:
        cached = {}

    # Search information for the team or competition if it hasn't been cached or the season for competition is over.
    obj = cached.get("info")
    if obj is None:
        tresp = requests.get(
            f"{APIURL}/teams",
            params={"id": f"{team_id}"},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT_S,
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

    # Check if could not find any information for the given ID.
    if obj is None:
        return None

    # Request and parse matches.
    # For teams, use the next and last parameters so we don't have to figure out the season.
    next_matches = get_next_n_matches(team_id, num_next_games)
    last_matches = get_last_n_matches(team_id, num_last_games)
    matches = parse_matches(next_matches) + parse_matches(last_matches)

    # Create cache entry.
    new_data = {
        "info": obj,
        "season": "N/A",
        "matches": matches,
    }

    # Add the newly created calendar.
    cache.update(lookup_key, new_data)

    return new_data


def fetch_comp(
    comp_id: str,
    start_date: date = None,
    end_date: date = None,
    season: str = None,
) -> List[Match]:
    # Check if we have this calendar cached.
    lookup_key = f"comp-cal/{comp_id}"
    cached, fresh = cache.query(lookup_key, max_age=timedelta(days=1))

    # Return cached data if it's still fresh.
    if fresh:
        return cached

    # Replace None with an empty dict so it's easier to work with.
    if cached is None:
        cached = {}

    # Get today's date to find season's year and future games.
    today = date.today()

    # Search information for the team or competition if it hasn't been cached or the season for competition is over.
    obj = cached.get("info")
    if (obj is None) or (obj.season_end < today.isoformat()):
        cresp = requests.get(
            f"{APIURL}/leagues",
            params={"id": f"{comp_id}"},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT_S,
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

    # Request and parse matches.
    # For competitions, find matches using the original method.
    # For a given season, find all matches that happen between last week and 3 months from now.
    # Find the current season to query the matches.
    # TODO: Could add a timestamp of when the season was updated and only recheck after a week or so.
    season = season if season else cached.get("season")
    if season is None or (cached and (not cached.get("matches"))):
        # Get the latest season for the competition.
        season = obj.season
    mresp = get_matches_in_window(False, comp_id, start_date, end_date, season)
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


def fetch(team: bool, id: str) -> List[Match]:
    if team:
        return fetch_team(id)
    else:
        return fetch_comp(id)


if __name__ == "__main__":
    print(fetch(team=True, id=1062))
    print(fetch(team=False, id=2))
    print(fetch(team=True, id=6))
