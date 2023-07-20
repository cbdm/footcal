from dataclasses import dataclass


@dataclass
class Match:
    id: int
    ref_name: str
    match_utc_ts: str
    venue_id: str
    venue_name: str
    venue_city: str
    league_id: str
    league_name: str
    home_team_id: str
    away_team_id: str
    home_team_name: str
    away_team_name: str
    status: str
    home_score: int = None
    away_score: int = None


@dataclass
class Team:
    id: int
    name: str
    short_name: str
    country: str
    founded: int
    club: bool
    logo: str


class SearchQuotaExceeded(Exception):
    "Raised when there is no more available quota for search requests."
    pass
