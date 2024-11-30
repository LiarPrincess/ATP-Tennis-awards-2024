from typing import assert_never
from dataclasses import dataclass
from page import Page, Subtitle, Award, Table, Chart
from atp_api import (
    Player,
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
    player: Player
    player_rank: int
    game_win_count: int
    game_win_tie_break_count: int
    game_lost_count: int
    game_lost_tie_break_count: int

    @property
    def count_all(self) -> int:
        return (
            self.game_win_count
            + self.game_win_tie_break_count
            + self.game_lost_count
            + self.game_lost_tie_break_count
        )


def write_game_set_match_game_count(
    page: Page,
    players: list[Player],
    date_from: str,
    award_count: int,
):
    "Game count."

    # MARK: Data

    rows = list[_Row]()

    for p in players:
        p_rank = p.rank
        assert p_rank is not None
        row = _Row(p, p_rank, 0, 0, 0, 0)
        rows.append(row)

        for t in p.career_tournaments:
            if t.date < date_from:
                continue

            for m in t.matches:
                if isinstance(
                    m,
                    PlayerMatch_Played | PlayerMatch_Retire | PlayerMatch_Default,
                ):
                    for s in m.sets:
                        row.game_win_count += s.player
                        row.game_lost_count += s.opponent

                        if s.tie_break is not None:
                            # 7:6
                            if s.player == 7:
                                assert s.opponent == 6
                                row.game_win_count -= 1
                                row.game_win_tie_break_count += 1
                            elif s.opponent == 7:
                                assert s.player == 6
                                row.game_lost_count -= 1
                                row.game_lost_tie_break_count += 1
                            # 1:0
                            elif s.player == 1:
                                assert s.opponent == 0
                                row.game_win_tie_break_count += 1
                            elif s.opponent == 1:
                                assert s.player == 0
                                row.game_lost_tie_break_count += 1
                            else:
                                assert False, "Tie-break requires 7:6 or 1:0"

                elif isinstance(
                    m, PlayerMatch_Bye | PlayerMatch_NotPlayed | PlayerMatch_Walkover
                ):
                    pass
                else:
                    assert_never(m)

                pass

    # MARK: Chart

    date_from_short = substring_until(date_from, "T")
    page.add(Subtitle(f"Number of games since {date_from_short}"))

    chart = Chart()
    chart.set_show_grid(True)
    page.add(chart)

    ranks = [r.player_rank for r in rows]

    def add_bars(
        count: list[int],
        count_color: str,
        tie_count: list[int],
        tie_color: str,
    ):
        chart.add_bars(ranks, count, color=count_color)
        chart.add_bars(ranks, tie_count, bottom=count, color=tie_color)

    count = [r.game_win_count for r in rows]
    tie_count = [r.game_win_tie_break_count for r in rows]
    add_bars(count, "blue", tie_count, "black")

    count = [-r.game_lost_count for r in rows]
    tie_count = [-r.game_lost_tie_break_count for r in rows]
    add_bars(count, "pink", tie_count, "black")

    chart.add_legend(["Win", "Tie-break win", "Loss", "Tie-break loss"])

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player rank")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label("Game count")

    tick_count = 20
    spread = max(r.count_all for r in rows)
    y_axis.set_major_ticks(round_down(spread // tick_count, multiple_of=10))

    # MARK: Awards

    def add_award(emoji: str, text: str, rows: list[_Row]):
        table = Table()
        table.headers.append(Table.Header("Player", is_player_column=True))
        table.headers.append(Table.Header("Age"))
        table.headers.append(Table.Header("Win"))
        table.headers.append(Table.Header("Tie-break win"))
        table.headers.append(Table.Header("Loss"))
        table.headers.append(Table.Header("Tie-break loss"))
        table.headers.append(Table.Header("Total"))

        for r in rows:
            p = r.player
            assert p.age
            row = Table.Row(
                [
                    p,
                    p.age,
                    r.game_win_count,
                    r.game_win_tie_break_count,
                    r.game_lost_count,
                    r.game_lost_tie_break_count,
                    r.count_all,
                ]
            )
            table.rows.append(row)

        if rows:
            page.add(Award(emoji, text))
            page.add(table)

    # 🐎 Work horse award for the biggest game count
    award_rows = filter_award_max(
        rows,
        count=award_count,
        key=lambda r: r.count_all,
    )
    add_award(
        "🐎",
        "Work horse award for the most games played.",
        award_rows,
    )

    # 🐨 Koala award for the smallest game count
    award_rows = filter_award_min(
        rows,
        count=award_count,
        key=lambda r: r.count_all,
    )
    add_award(
        "🐨",
        "Koala award for the least games played.",
        award_rows,
    )
