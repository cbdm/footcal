from upstash_redis import Redis
from os import getenv
from datetime import datetime, timedelta
from jsonpickle import dumps, loads
from typing import Any, List


db = Redis(
    url=getenv("REDIS_URL", "localhost"),
    token=getenv("REDIS_TOKEN", "********"),
)


def query(key: str, max_age: timedelta) -> Any:
    data = db.get(key)
    if not data:
        return None

    data = loads(data)
    if data["ts"] + max_age < datetime.utcnow():
        return None

    return data["value"]


def update(key: str, new_val: Any) -> None:
    data = {"value": new_val, "ts": datetime.utcnow()}
    db.set(key, dumps(data))


def list_cached_calendars(team: bool) -> List[str]:
    cached_cals = []
    for key in db.keys(f"{'team' if team else 'comp'}-cal/*"):
        team_id = key[len(f"{'team' if team else 'comp'}-cal/") :]
        calendar = loads(db.get(key))["value"]
        if not calendar:
            continue
        match = calendar[0]
        if team:
            name = (
                match.home_team_name
                if team_id == f"{match.home_team_id}"
                else match.away_team_name
            )
        else:
            name = match.league_name
        cached_cals.append((team_id, name))
    return cached_cals


if __name__ == "__main__":
    print(db.keys("*"))
