from typing import assert_never
from dataclasses import dataclass
from page import Page, Subtitle, Paragraph, Chart
from atp_api import (
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
class _Row:

    MatchData = (
        PlayerMatch_Played
        | PlayerMatch_Walkover
        | PlayerMatch_Retire
        | PlayerMatch_Default
    )

    @dataclass
    class Match:
        tournament: PlayerTournament
        match: "_Row.MatchData"
        opponent_rank: int
        opponent: Player

    rank: int
    player: Player
    matches: list[Match]


def write_game_set_match_versus(
    page: Page,
    players: list[Player],
    date_from: str,
    # award_count_raise: int,
    # award_count_drop: int,
):
    "Matrix who played with who."

    # MARK: Data

    rows = list[_Row]()
    id_to_player = {p.id: p for p in players}
    rank_lowest: int | None = None
    rank_highest: int | None = None

    for p in players:
        p_rank = p.rank
        assert p_rank is not None
        row = _Row(p_rank, p, [])
        rows.append(row)

        rank_lowest = max2(rank_lowest, p_rank)
        rank_highest = min2(rank_highest, p_rank)

        for t in p.career_tournaments:
            if t.date < date_from:
                continue

            for m in t.matches:
                if isinstance(m, _Row.MatchData):
                    o_id = m.opponent.id
                    o = id_to_player.get(o_id)

                    # None -> player not in the top 10/50/100 etc.
                    if o is not None:
                        assert o.rank is not None
                        match = _Row.Match(t, m, o.rank, o)
                        row.matches.append(match)

                elif isinstance(m, PlayerMatch_Bye | PlayerMatch_NotPlayed):
                    pass
                else:
                    assert_never(m)

    assert rank_lowest is not None
    assert rank_highest is not None
    rank_span = rank_lowest - rank_highest + 1

    # MARK: Chart

    date_from_short = substring_until(date_from, "T")
    page.add(Subtitle(f"Match count since {date_from_short}"))
    page.add(
        Paragraph(
            "All games, including Olympics etc. Only singles (as in 1 on 1 matches, not their marriage status)."
        )
    )

    chart = Chart()
    chart.set_show_grid(True)
    chart.set_aspect_rato(1.2, 1)
    page.add(chart)

    chart_data = [[0] * rank_span for _ in range(rank_span)]

    # Transpose to count per opponent
    for r in rows:
        # -1 for '0' indexing
        x = r.rank - 1

        for m in r.matches:
            y = m.opponent_rank - 1
            chart_data[x][y] += 1

    # 'pcolorfast' gives incorrect XY ticks
    ranks = range(rank_highest, rank_lowest + 1)
    heatmap = chart.add_heatmap(ranks, ranks, chart_data)
    chart.add_color_bar(heatmap, "Match count")

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player ranking")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label("Opponent ranking")
    chart.y_axis.set_major_ticks(5)
    chart.y_axis.set_minor_ticks(1)

