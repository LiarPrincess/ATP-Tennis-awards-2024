from typing import Literal, assert_never
from dataclasses import dataclass
from api import Player, PlayerRank
from page import Page, Subtitle, Award, Table, Chart
from helpers import *


@dataclass
class _Row:
    player: Player
    rank_past: int
    "Rank at the start of the period."
    rank_now: int
    "Current rank."

    @property
    def diff(self) -> int:
        return self.rank_past - self.rank_now


def write_ranking_change(
    page: Page,
    past_date: str,
    past_ranking: list[Player],
    now_date: str,
    now_ranking: list[Player],
    award_count_raise: int,
    award_count_drop: int,
):
    "Compare current rank with the rank in the past."

    # MARK: Data

    rows = _get_rows(
        now_ranking,
        past_date=past_date,
        on_current_rank_none="throw",
    )

    rows_past = _get_rows(
        past_ranking,
        past_date=past_date,
        on_current_rank_none="ignore",
    )

    rows_sorted_by_diff = sorted(rows, key=lambda r: r.diff)

    # MARK: Chart

    past_date_short = substring_until(past_date, "T")
    now_date_short = substring_until(now_date, "T")
    page.add(Subtitle(f"Rank change since {past_date_short}"))

    chart = Chart()
    chart.set_show_grid(True)
    page.add(chart)

    color_map = chart.create_color_map(r.diff for r in rows)

    for r in rows:
        color = color_map[r.diff]
        chart.add_bar(r.rank_now, r.diff, color=color)

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player ranking")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label("Positions gained/lost")

    tick_count = 20
    min_diff = rows_sorted_by_diff[0].diff
    max_diff = rows_sorted_by_diff[-1].diff
    spread = max_diff - min_diff
    y_axis.set_major_ticks(round_down(spread // tick_count, multiple_of=10))

    # MARK: Awards

    def add_award(emoji: str, text: str, rows: list[_Row]):
        table = Table()
        table.headers.append(Table.Header("Player", is_player_column=True))
        table.headers.append(Table.Header("Age"))
        table.headers.append(Table.Header(past_date_short))
        table.headers.append(Table.Header(now_date_short))
        table.headers.append(Table.Header("Difference"))

        for r in rows:
            p = r.player
            assert p.age
            row = Table.Row([p, p.age, r.rank_past, r.rank_now, r.diff])
            table.rows.append(row)

        if rows:
            page.add(Award(emoji, text))
            page.add(table)

    # Biggest raise
    award_rows = filter_award_max(
        rows,
        count=award_count_raise,
        key=lambda r: r.diff,
    )
    award_rows = [r for r in award_rows if r.diff > 0]  # Only positive
    add_award(
        "🦄",
        "Unicorn award for the biggest raise. This is THE award to get, possibly more important than #1.",
        award_rows,
    )

    # Biggest drop
    award_rows: list[_Row] = filter_award_min(
        rows_past,
        count=award_count_drop,
        key=lambda r: r.diff,
    )
    award_rows = [r for r in award_rows if r.diff < 0]  # Only negative
    add_award("🦨", "Skunk award for the biggest drop.", award_rows)

    # No change
    award_rows = filter_award_equal(rows, key=lambda r: r.diff == 0)
    add_award("🦥", "Sloth award for sleeping the whole season.", award_rows)


# MARK: Helpers


def _get_rows(
    players: list[Player],
    past_date: str,
    on_current_rank_none: Literal["throw", "ignore"],
) -> list[_Row]:
    result = list[_Row]()

    for p in players:
        rank_now = p.rank

        if rank_now is None:
            if on_current_rank_none == "throw":
                assert rank_now is not None
            elif on_current_rank_none == "ignore":
                continue
            else:
                assert_never(on_current_rank_none)

        rank_past = p.get_rank_at_date(past_date)
        assert isinstance(rank_past, PlayerRank)

        result.append(_Row(p, rank_past.rank, rank_now))

    return result
