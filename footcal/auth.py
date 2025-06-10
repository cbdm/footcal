from os import getenv

APIURL = "https://api-football-v1.p.rapidapi.com/v3"
APIKEY = getenv("RAPIDAPIKEY", "XxXxXxXxXxXxXxXxXxXxXxXx")
HEADERS = {
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
    "x-rapidapi-key": APIKEY,
}
REQUEST_TIMEOUT_S = 45
