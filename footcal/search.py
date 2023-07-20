import requests
from auth import APIURL, HEADERS, MIN_LEFT_FOR_SEARCH, get_remaining_quota
from typing import List
from custom_types import Team, SearchQuotaExceeded
import json


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
    tresp = get_teams(user_query)
    return parse_teams(tresp)


if __name__ == "__main__":
    for t in search_teams("atletico"):
        print(t)
