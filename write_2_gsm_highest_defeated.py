from typing import assert_never
from dataclasses import dataclass
from page import Page, Subtitle, Award, Table, Chart, Paragraph
from atp import (
    Player,
    PlayerTournament,
    PlayerMatch_Played,
    PlayerMatch_Walkover,
    PlayerMatch_Retire,
    PlayerMatch_Default,
    PlayerMatch_Bye,
    PlayerMatch_NotPlayed,
)
from helpers import *


@dataclass
class _Match:

    Data = (
        PlayerMatch_Played
        | PlayerMatch_Walkover
        | PlayerMatch_Retire
        | PlayerMatch_Default
    )

    tournament: PlayerTournament
    match: "_Match.Data"

    player: Player
    player_rank: int
    opponent: Player
    opponent_rank: int

    @property
    def rank_diff(self) -> int:
        return self.player_rank - self.opponent_rank


def write_game_set_match_highest_defeated(
    page: Page,
    players: list[Player],
    date_from: str,
    award_count_highest_diff: int,
):
    "Highest defeated opponent."

    matches = list[_Match]()
    id_to_player = {p.id: p for p in players}

    for p in players:
        p_rank = p.rank
        assert p_rank is not None

        for t in p.career_tournaments:
            if t.date < date_from:
                continue

            for m in t.matches:
                if m.win_loss == "W":
                    pass
                elif m.win_loss == "L":
                    continue
                else:
                    assert_never(m.win_loss)

                if isinstance(m, _Match.Data):
                    o_id = m.opponent.id
                    o = id_to_player.get(o_id)

                    if o is not None:
                        assert o.rank is not None
                        matches.append(_Match(t, m, p, p_rank, o, o.rank))

                elif isinstance(m, PlayerMatch_Bye | PlayerMatch_NotPlayed):
                    pass
                else:
                    assert_never(m)

    _write_chart(page, date_from, matches)
    _write_award_for_highest_ranking_diff(page, matches, award_count_highest_diff)
    _write_award_for_defeating_no1(page, players, matches)


# MARK: Chart


def _write_chart(page: Page, date_from: str, matches: list[_Match]):

    date_from_short = substring_until(date_from, "T")
    page.add(Subtitle(f"Highest rank of the defeated opponent since {date_from_short}"))

    chart = Chart()
    chart.set_show_grid(True)
    page.add(chart)

    rank_to_highest_win = dict[int, int]()

    for m in matches:
        p = m.player_rank
        new = m.opponent_rank
        current = rank_to_highest_win.get(p)

        if current is None or new < current:
            rank_to_highest_win[p] = new

    ranks = list(rank_to_highest_win)
    highest_win = [rank_to_highest_win[r] for r in ranks]

    color_map = chart.create_color_map(highest_win)
    colors = [color_map[b] for b in highest_win]
    chart.add_bars(ranks, highest_win, color=colors)

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player rank")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label("Opponent rank")
    y_axis.set_major_ticks(2)

    page.add(
        Paragraph(
            """
This chart is pretty interesting, as it can define what an "upset" is:
- 1-11 can comfortably go against the TOP 3
- 12-26 can win with TOP 5
- 27-50 TOP 4 if difficult, but TOP 10 is doable
"""
        )
    )


# MARK: Awards


def _write_award_for_highest_ranking_diff(
    page: Page,
    matches: list[_Match],
    award_count: int,
):
    award_rows = [
        m
        for m in matches
        if m.player.can_receive_award
        and m.opponent.can_receive_award
        and m.rank_diff > 0
    ]
    award_rows = filter_award_max(
        matches,
        count=award_count,
        key=lambda r: r.rank_diff,
    )

    table = Table()
    page.add(
        Award("🦈", f"Shark award for the win with the biggest ranking difference.")
    )
    page.add(table)

    table.headers.append(Table.Header("Player", is_player_column=True))
    table.headers.append(Table.Header("Opponent", is_player_column=True))
    table.headers.append(Table.Header("Rank diff."))
    table.headers.append(Table.Header("Result"))
    table.headers.append(Table.Header("Tournament"))
    table.headers.append(Table.Header("Round"))

    for m in award_rows:
        tournament = m.tournament.name
        round = m.match.round.id
        sets = to_str_sets(m.match)

        row = Table.Row([m.player, m.opponent, m.rank_diff, sets, tournament, round])
        table.rows.append(row)


def _write_award_for_defeating_no1(
    page: Page,
    players: list[Player],
    matches: list[_Match],
):
    defeated_1 = [
        m for m in matches if m.player.can_receive_award and m.opponent_rank == 1
    ]
    defeated_1.sort(key=lambda m: m.tournament.date)

    if not defeated_1:
        return

    player_1 = next((p for p in players if p.rank == 1), None)
    assert player_1 is not None
    assert player_1.age is not None
    player_1_str = to_str_player(player_1)

    page.add(
        Award(
            "🐡",
            f"Blowfish award for defeating {player_1_str}.",
        )
    )

    table = Table()
    page.add(table)

    table.headers.append(Table.Header("Player", is_player_column=True))
    table.headers.append(Table.Header("Age"))
    table.headers.append(Table.Header("Result"))
    table.headers.append(Table.Header("Tournament"))
    table.headers.append(Table.Header("Round"))

    for m in defeated_1:
        p = m.player
        age = p.age if p.age else ""
        tournament = m.tournament.name
        round = m.match.round.id
        sets = to_str_sets(m.match)

        row = Table.Row([p, age, sets, tournament, round])
        table.rows.append(row)
