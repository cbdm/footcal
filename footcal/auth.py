from os import getenv

APIURL = "https://v3.football.api-sports.io/"
APIKEY = getenv("APISPORTSKEY", "XxXxXxXxXxXxXxXxXxXxXxXx")
HEADERS = {"x-apisports-key": APIKEY}
