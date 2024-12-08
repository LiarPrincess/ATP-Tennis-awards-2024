from typing import Literal, assert_never
from dataclasses import dataclass
from atp import Player
from chart import Chart
from helpers import *


_CHART_ASPECT_RATIO = {"width": 100, "height": 50}


@dataclass
class Page:

    @dataclass
    class Row:
        player: Player
        rank_now: int
        "Current rank."
        rank_past: int
        "Rank at the start of the period."
        rank_highest: int
        "Highest obtained rank: 1, 2, 3…."
        rank_lowest: int
        "Lowest obtained rank: 99, 98, 97…."

        @property
        def rank_change(self) -> int:
            return self.rank_past - self.rank_now

        @property
        def rank_spread(self) -> int:
            "rank_lowest - rank_highest"
            return self.rank_lowest - self.rank_highest

    date_now: str
    date_past: str
    player_no_1: Player

    rank_change_chart: Chart
    rank_change_max_gain: int
    rank_change_awards_max_gain: list[Row]
    rank_change_awards_max_drop: list[Row]
    rank_change_awards_no_change: list[Row]

    rank_spread_chart: Chart
    rank_spread_awards_min: list[Row]
    rank_spread_awards_max: list[Row]


def page1_ranking(
    date_past: str,
    ranking_past: list[Player],
    date_now: str,
    ranking_now: list[Player],
    award_count_rank_gain_lose: int,
    award_count_spread: int,
) -> Page:
    rows = _get_rows(
        ranking_now,
        date_past=date_past,
        on_current_rank_none="throw",
    )

    rows_past = _get_rows(
        ranking_past,
        date_past=date_past,
        on_current_rank_none="ignore",
    )

    date_now_short = substring_until(date_now, "T")
    date_past_short = substring_until(date_past, "T")
    player_no_1 = find(rows, lambda r: r.rank_now == 1)

    # Rank change
    rank_change_max_gain = max(r.rank_change for r in rows)
    rank_change_chart = _create_rank_change_chart(rows)

    rank_change_awards_max_gain = filter_award_max(
        rows,
        award_count_rank_gain_lose,
        key=lambda r: r.rank_change,
    )

    rank_change_awards_max_drop = filter_award_min(
        rows_past,  # We need to use the previous TOP 100!
        award_count_rank_gain_lose,
        key=lambda r: r.rank_change,
    )

    rank_change_awards_no_change = filter_award_equal(
        rows,
        key=lambda r: r.rank_change == 0,
    )

    # Rank spread
    rank_spread_chart = _create_rank_spread_chart(rows)

    rank_spread_awards_min = filter_award_min(
        rows,
        award_count_spread,
        key=lambda r: r.rank_spread,
    )

    rank_spread_awards_max = filter_award_max(
        rows,
        award_count_spread,
        key=lambda r: r.rank_spread,
    )

    return Page(
        date_now=date_now_short,
        date_past=date_past_short,
        player_no_1=player_no_1.player,
        rank_change_chart=rank_change_chart,
        rank_change_max_gain=rank_change_max_gain,
        rank_change_awards_max_gain=rank_change_awards_max_gain,
        rank_change_awards_max_drop=rank_change_awards_max_drop,
        rank_change_awards_no_change=rank_change_awards_no_change,
        rank_spread_chart=rank_spread_chart,
        rank_spread_awards_min=rank_spread_awards_min,
        rank_spread_awards_max=rank_spread_awards_max,
    )


# MARK: Charts


def _create_rank_change_chart(rows: list[Page.Row]) -> Chart:
    chart = Chart()
    chart.set_show_grid(True)
    chart.set_aspect_rato(**_CHART_ASPECT_RATIO)

    # Bars
    rank = [r.rank_now for r in rows]
    rank_change = [r.rank_change for r in rows]

    # Separate color map for gain and loss
    color_map_gain = chart.create_color_map(
        (r for r in rank_change if r >= 0), "purple_cyan"
    )
    color_map_loss = chart.create_color_map(
        (r for r in rank_change if r <= 0), "red_pink"
    )

    color = [color_map_gain[c] if c >= 0 else color_map_loss[c] for c in rank_change]
    chart.add_bar(rank, rank_change, color=color)

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player rank")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label("Positions gained/lost")
    y_axis.set_major_tick_count(rank_change, 20, multiple_of=10)

    return chart


def _create_rank_spread_chart(rows: list[Page.Row]) -> Chart:
    chart = Chart()
    chart.set_show_grid(True)
    chart.set_aspect_rato(**_CHART_ASPECT_RATIO)

    # Bars
    rank = [r.rank_now for r in rows]
    spread = [r.rank_spread for r in rows]
    highest = [r.rank_highest for r in rows]

    color_map = chart.create_color_map(
        spread,
        ["pink", "purple", "cyan"],
    )

    color = [color_map[c] for c in spread]
    chart.add_bar(rank, spread, bottom=highest, color=color)

    # Scatter
    rank_now = [r.rank_now for r in rows]
    chart.add_scatter(rank, rank_now, marker="D", color="foreground", size=20)

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player rank")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label("Highest/lowest rank (◆ = current)")
    lowest = [r.rank_lowest for r in rows]
    y_axis.set_major_tick_count(lowest, 10, multiple_of=10)

    return chart


# MARK: Rows


def _get_rows(
    players: list[Player],
    date_past: str,
    on_current_rank_none: Literal["throw", "ignore"],
) -> list[Page.Row]:
    result = list[Page.Row]()

    for p in players:
        rank_now = p.rank

        if rank_now is None:
            if on_current_rank_none == "throw":
                assert rank_now is not None
            elif on_current_rank_none == "ignore":
                continue
            else:
                assert_never(on_current_rank_none)

        rank_history = sorted(p.career_rank_history, key=lambda r: r.date)
        rank_past: int | None = None
        rank_lowest: int | None = None
        rank_highest: int | None = None

        for r in rank_history:
            # It may happen that we do not have a ranking at the exact 'past_date'.
            # In such case just take the ranking from the date before.
            if r.date <= date_past:
                rank_past = r.rank

            # Smaller number -> higher rank
            if r.date >= date_past:
                rank_lowest = max2(rank_lowest, r.rank)
                rank_highest = min2(rank_highest, r.rank)

        assert rank_past is not None
        assert rank_lowest is not None
        assert rank_highest is not None

        r = Page.Row(
            player=p,
            rank_now=rank_now,
            rank_past=rank_past,
            rank_highest=rank_highest,
            rank_lowest=rank_lowest,
        )
        result.append(r)

    return result
