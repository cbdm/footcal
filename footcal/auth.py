import requests
import json
from os import getenv
from datetime import datetime, timedelta

APIURL = "https://v3.football.api-sports.io/"
APIKEY = getenv("APISPORTSKEY", "XxXxXxXxXxXxXxXxXxXxXxXx")
HEADERS = {"x-apisports-key": APIKEY}
MIN_LEFT_FOR_SEARCH = 20


def get_remaining_quota() -> int:
    """Returns how many requests the app can still make with the daily quota."""
    resp = requests.get(f"{APIURL}/status", headers=HEADERS)
    data = json.loads(resp.text)
    reqs = data.get("response", {}).get("requests", {})
    return reqs.get("limit_day", 0) - reqs.get("current", 0)


def get_quota_reset() -> timedelta:
    """Returns how much time until the API quota resets, assuming it resets on 00:00 UTC."""
    midnight = datetime.combine(
        datetime.utcnow().today(), datetime.min.time()
    ) + timedelta(days=1)
    return midnight - datetime.utcnow()


if __name__ == "__main__":
    print(get_remaining_quota())
    print(get_quota_reset())
