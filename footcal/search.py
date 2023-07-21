import requests
from auth import APIURL, HEADERS, MIN_LEFT_FOR_SEARCH, get_remaining_quota
from typing import List
from custom_types import Team, SearchQuotaExceeded
import json
import cache
from datetime import timedelta


def get_teams(user_query: str) -> str:
    if get_remaining_quota() < MIN_LEFT_FOR_SEARCH:
        raise SearchQuotaExceeded()

    resp = requests.get(
        f"{APIURL}/teams", params={"search": user_query}, headers=HEADERS
    )
    return resp.text


def parse_teams(tresp: str) -> List[Team]:
    data = json.loads(tresp)["response"]
    return [
        Team(
            id=d["team"]["id"],
            name=d["team"]["name"],
            short_name=d["team"]["code"],
            country=d["team"]["country"],
            founded=d["team"]["founded"],
            club=not d["team"]["national"],
            logo=d["team"]["logo"],
        )
        for d in data
    ]


def search_teams(user_query: str) -> List[Team]:
    # Check if we have this search cached.
    lookup_key = f"team-search/{user_query}"
    cached = cache.query(lookup_key, max_age=timedelta(days=30))
    if cached:
        return cached

    tresp = get_teams(user_query)
    new_data = parse_teams(tresp)

    # Add the search results to the cache.
    cache.update(lookup_key, new_data)

    return new_data


if __name__ == "__main__":
    for t in search_teams("atletico"):
        print(t)
