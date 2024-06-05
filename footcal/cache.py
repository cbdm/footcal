from os import getenv
from datetime import datetime, timedelta
from jsonpickle import dumps, loads
from typing import Any, List
from flask_sqlalchemy import SQLAlchemy
from pymysql import install_as_MySQLdb
from sqlalchemy.sql import select

# Setup the mysql driver.
install_as_MySQLdb()

# Placeholder variables that will be assigned in the setupDB method.
db = None
table = None

# Get db config from environment variables.
# Default values should work with the 'testdb' in the repo.
db_config = {
    "host": getenv("DB_HOST", "localhost"),
    "port": getenv("DB_PORT", "40000"),
    "user": getenv("DB_USER", "root"),
    "passwd": getenv("DB_PASS", "root"),
    "database": getenv("DB_NAME", "footcal-db"),
}


def setupDB(app):
    global db
    global table

    # Setup the connection between app and DB.
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mysql://{user}:{passwd}@{host}:{port}/{database}".format(**db_config)
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)

    # Configure the DB table.
    class CachedData(db.Model):
        objkey = db.Column(db.String(200), primary_key=True)
        data = db.Column(db.LargeBinary)

        def __repr__(self):
            return f"<CachedData {self.objkey}>"

    table = CachedData


def query(key: str, max_age: timedelta) -> tuple[Any, bool]:
    """Returns a tuple with the stored value if any and a boolean indicating if the data is fresh."""
    record = table.query.get(key)
    if not record:
        return None, False

    data = loads(record.data) if record else None
    if data is None:
        return None, False

    return data["value"], data["ts"] + max_age >= datetime.utcnow()


def update(key: str, new_val: Any) -> None:
    record = table.query.get(key)
    if record:
        record.data = dumps({"value": new_val, "ts": datetime.utcnow()}).encode("utf8")

    else:
        record = table(
            objkey=key,
            data=dumps({"value": new_val, "ts": datetime.utcnow()}).encode("utf8"),
        )

    db.session.add(record)
    db.session.commit()


def list_cached_calendars(team: bool) -> List[str]:
    cached_cals = []
    for result in db.session.execute(select(table)):
        entry = result[0]

        # Ignore entries for other types.
        # TODO: could add a new column and filter these with the select query above.
        if not (
            (team and entry.objkey.startswith("team-cal"))
            or (not team and entry.objkey.startswith("comp-cal"))
        ):
            continue

        cal_id = entry.objkey[len(f"{'team' if team else 'comp'}-cal/") :]
        calendar = loads(entry.data)["value"]
        name = calendar["info"].name
        cached_cals.append((cal_id, name))

    return cached_cals


if __name__ == "__main__":
    print(list_cached_calendars(True))
    print(list_cached_calendars(False))
