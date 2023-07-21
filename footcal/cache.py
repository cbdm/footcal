from upstash_redis import Redis
from os import getenv
from datetime import datetime, timedelta
from jsonpickle import dumps, loads
from typing import Any


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


if __name__ == "__main__":
    print(db.keys("*"))
