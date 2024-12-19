from datetime import datetime
from dataclasses import dataclass
from atp import (
    Player,
    PlayerTournament,
    PlayerMatch_Opponent,
    PlayerMatch_Played,
    PlayerMatch_Retire,
    PlayerMatch_Default,
    PlayerMatch_Set,
)
from chart import Chart
from helpers import *


@dataclass
class Page:

    @dataclass
    class PlayerStats:

        @dataclass
        class Tournament:
            tournament: PlayerTournament
            is_winner: bool

        player: Player
        tournaments: list[Tournament]
        match_count: int
        set_count: int
        game_count: int

    @dataclass
    class AwardIneligibility:
        player: Player
        reason: str

    djokovic: PlayerStats
    mensik: PlayerStats
    award_ineligibility: list[AwardIneligibility]


def page7_fin(players: list[Player], date_from: str) -> Page:
    djokovic = _get_player_stats(players, date_from, "Djokovic")
    mensik = _get_player_stats(players, date_from, "Mensik")

    award_ineligibility = list[Page.AwardIneligibility]()

    for p in players:
        r = p.award_ineligibility_reason

        if r == "Deceased":
            rr = Page.AwardIneligibility(p, "ATP status: Deceased")
            award_ineligibility.append(rr)
        else:
            assert r is None

    return Page(djokovic, mensik, award_ineligibility)


def _get_player_stats(
    players: list[Player],
    date_from: str,
    name_last: str,
) -> Page.PlayerStats:
    p = find(players, lambda p: p.name_last == name_last)

    tournaments = list[Page.PlayerStats.Tournament]()
    match_count = 0
    set_count = 0
    game_count = 0

    for t in p.career_tournaments:
        if t.date < date_from:
            continue

        last_m = t.matches[-1]
        is_win = last_m.round.id == "F" and last_m.win_loss == "W"
        dt = Page.PlayerStats.Tournament(t, is_win)
        tournaments.append(dt)

        for m in t.matches:
            match_count += 1

            sets = getattr(m, "sets", None)
            if sets is not None:
                assert isinstance(sets, list)

                for s in sets:
                    assert isinstance(s, PlayerMatch_Set)
                    set_count += 1

                    game_count += s.opponent
                    game_count += s.player

                    if s.tie_break is not None:
                        game_count += 1

    return Page.PlayerStats(p, tournaments, match_count, set_count, game_count)
