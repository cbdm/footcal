import redis
from os import getenv
from datetime import datetime, timedelta
from pickle import dumps, loads
from typing import Any

db = redis.Redis(
    host=getenv("REDIS_HOST", "localhost"),
    port=getenv("REDIS_PORT", 6379),
    password=getenv("REDIS_PASS", "<password>"),
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
    print(db.keys())
