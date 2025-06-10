import json
from datetime import timedelta
from typing import List

import cache
import requests
from auth import APIURL, HEADERS, REQUEST_TIMEOUT_S
from custom_types import Competition, Team


def get_teams(user_query: str) -> str:
    resp = requests.get(
        f"{APIURL}/teams",
        params={"search": user_query},
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT_S,
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
    cached, fresh = cache.query(lookup_key, max_age=timedelta(days=30))
    if fresh:
        return cached

    tresp = get_teams(user_query)
    new_data = parse_teams(tresp)

    # Add the search results to the cache.
    cache.update(lookup_key, new_data)

    return new_data


def get_comps(user_query: str) -> str:
    resp = requests.get(
        f"{APIURL}/leagues",
        params={"search": user_query},
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT_S,
    )
    return resp.text


def parse_comps(tresp: str) -> List[Competition]:
    data = json.loads(tresp)["response"]
    return [
        Competition(
            id=d["league"]["id"],
            name=d["league"]["name"],
            type=d["league"]["type"],
            logo=d["league"]["logo"],
            country_name=d["country"]["name"],
            country_code=d["country"]["code"],
            season=d["seasons"][-1]["year"],
            season_start=d["seasons"][-1]["start"],
            season_end=d["seasons"][-1]["end"],
        )
        for d in data
    ]


def search_comps(user_query: str) -> List[Competition]:
    # Check if we have this search cached.
    lookup_key = f"comp-search/{user_query}"
    cached, fresh = cache.query(lookup_key, max_age=timedelta(days=30))
    if fresh:
        return cached

    tresp = get_comps(user_query)
    new_data = parse_comps(tresp)

    # Add the search results to the cache.
    cache.update(lookup_key, new_data)

    return new_data


if __name__ == "__main__":
    for t in search_teams("atletico"):
        print(t)
    for c in search_comps("world cup"):
        print(c)
