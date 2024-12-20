from dataclasses import dataclass
from atp import (
    Player,
    PlayerTournament,
    PlayerMatch,
    PlayerMatch_Played,
    PlayerMatch_Retire,
    PlayerMatch_Default,
    PlayerMatch_Bye,
    PlayerMatch_NotPlayed,
    PlayerMatch_Walkover,
    PlayerMatch_Set,
)
from page3_game_set_match_2 import get_game_count_rows
from helpers import *


@dataclass
class Page:

    @dataclass
    class PlayerStats:

        @dataclass
        class Tournament:
            tournament: PlayerTournament
            matches: list[PlayerMatch]
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

    for t in p.career_tournaments:
        if t.date < date_from:
            continue

        matches = list[PlayerMatch]()

        for m in t.matches:
            if isinstance(
                m,
                PlayerMatch_Played
                | PlayerMatch_Walkover
                | PlayerMatch_Retire
                | PlayerMatch_Default
                | PlayerMatch_NotPlayed,
            ):
                matches.append(m)
            elif isinstance(m, PlayerMatch_Bye):
                pass
            else:
                assert_never(m)

        m = t.matches[-1]
        is_win = m.round.id == "F" and m.win_loss == "W"
        tournaments.append(Page.PlayerStats.Tournament(t, matches, is_win))

        for m in t.matches:
            match_count += 1
            sets = getattr(m, "sets", None)

            if sets is not None:
                assert isinstance(sets, list)
                set_count += len(sets)

    game_rows = get_game_count_rows(players, date_from)
    games_p = find(game_rows, lambda r: r.player.id == p.id)
    game_count = games_p.count_all

    return Page.PlayerStats(p, tournaments, match_count, set_count, game_count)
