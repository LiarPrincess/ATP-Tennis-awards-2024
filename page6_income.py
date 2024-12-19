import numpy as np
from datetime import datetime
from dataclasses import dataclass
from atp import Player
from chart import Chart
from helpers import *

_THOUSAND = 1000
_MILLION = _THOUSAND * _THOUSAND
_YEAR = datetime.now().year


@dataclass
class Page:

    @dataclass
    class Row:
        player: Player
        rank: int
        year_became_pro: int | None
        games_count: int
        income_ytd: int
        income_ytd_str: str
        income_career: int
        income_career_str: str

        @property
        def avg_income_per_year(self) -> float:
            if self.year_became_pro is None:
                return 0

            year_count = _YEAR - self.year_became_pro + 1
            return self.income_career / year_count

    ytd_chart: Chart
    ytd_above_million_count: int
    ytd_per_game_chart: Chart
    total_chart: Chart
    total_average_per_year_chart: Chart


def page6_income(players: list[Player]) -> Page:
    rows = _get_rows(players)

    ranks = [r.rank for r in rows]

    ytd = [r.income_ytd for r in rows]
    ytd_avg = average(ytd)
    ytd_chart = _create_income_chart(
        ranks,
        ytd,
        y_axis_label="Income [$1M]",
        y_axis_scale=_MILLION,
        y_axis_tick_interval=_MILLION,
        has_polynomial=True,
        average=ytd_avg,
    )

    ytd_above_million = [x for x in ytd if x >= _MILLION]
    ytd_above_million_count = len(ytd_above_million)

    ytd_per_game = [r.income_ytd / r.games_count for r in rows]
    ytd_per_game_avg = average(ytd_per_game)
    ytd_per_game_chart = _create_income_chart(
        ranks,
        ytd_per_game,
        y_axis_label="Income [$1k]",
        y_axis_scale=_THOUSAND,
        y_axis_tick_interval=500,
        has_polynomial=True,
        average=ytd_per_game_avg,
    )

    total = [r.income_career for r in rows]
    total_avg = average(total)
    total_chart = _create_income_chart(
        ranks,
        total,
        y_axis_label="Income [$1M]",
        y_axis_scale=_MILLION,
        y_axis_tick_interval=10 * _MILLION,
        average=total_avg,
    )

    total_per_year = [r.avg_income_per_year for r in rows]
    total_per_year_avg = average(i for i in total_per_year if i != 0)
    total_average_per_year_chart = _create_income_chart(
        ranks,
        total_per_year,
        y_axis_label="Income [$1M or 0 if no data available]",
        y_axis_scale=_MILLION,
        y_axis_tick_interval=500 * _THOUSAND,
        average=total_per_year_avg,
    )

    return Page(
        ytd_chart=ytd_chart,
        ytd_above_million_count=ytd_above_million_count,
        ytd_per_game_chart=ytd_per_game_chart,
        total_chart=total_chart,
        total_average_per_year_chart=total_average_per_year_chart,
    )


def _create_income_chart(
    ranks: list[int],
    values: list[int] | list[float],
    y_axis_label: str,
    y_axis_scale: int,
    y_axis_tick_interval: int,
    average: float | None = None,
    has_polynomial: bool = False,
) -> Chart:
    chart = Chart()
    chart.set_show_grid(True)
    chart.set_aspect_rato(100, 60)

    # Bars
    color_map = chart.create_color_map(
        values,
        ["pink", "purple", "cyan"],
    )
    colors = [color_map[v] for v in values]
    chart.add_bar(ranks, values, color=colors)

    rank_min = min(ranks)
    rank_max = max(ranks)

    if average is not None:
        average_str = _format_money_as_int(average)
        chart.add_horizontal_line(
            average,
            rank_min - 0.4,
            rank_max + 0.4,
            label=f"Average ${average_str}",
            color="red",
            line_width=4,
        )
        chart.add_legend()

    if has_polynomial:
        poly_fn = np.polynomial.Chebyshev.fit(ranks, values, deg=10)

        poly_x = np.arange(rank_min, rank_max, step=0.1)
        poly_y = poly_fn(poly_x)

        chart.add_plot(
            poly_x,
            poly_y,
            label="Trend",
            color="green",
            line_width=4,
        )
        chart.add_legend()

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player rank")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label(y_axis_label)

    # tick_count = 20
    # values_max = max(values)
    # spread = round_down(values_max // tick_count, multiple_of=y_axis_scale)
    # spread = max(spread, y_axis_scale)
    # y_axis.set_major_ticks(spread)
    y_axis.set_major_tick_interval(y_axis_tick_interval)

    def format_y_tick(value: float, pos) -> str:
        x = value / y_axis_scale
        s = str(x)

        if s.endswith(".0"):
            s = s[:-2]

        return s

    y_axis.set_major_formatter_fn(format_y_tick)

    return chart


def _format_money_as_int(n: float) -> str:
    s = f"{n:.0f}"
    result = ""

    for index, c in enumerate(reversed(s)):
        # 9 876 543 210
        if index != 0 and index % 3 == 0:
            result = "," + result
        result = c + result

    return result


def _get_rows(players: list[Player]) -> list[Page.Row]:

    def parse_money(s: str) -> tuple[int, str]:
        assert s.startswith("$")
        i = s.strip("$")
        i = i.replace(",", "")
        return int(i), s

    result = list[Page.Row]()

    for p in players:
        assert p.rank

        income_ytd, income_ytd_str = parse_money(p.ytd_prize_formatted)
        income_career, income_career_str = parse_money(p.career_prize_formatted)

        games_count_service = p.ytd_stats_service.games_played
        games_count_return = p.ytd_stats_return.games_played
        games_count = games_count_service + games_count_return

        r = Page.Row(
            player=p,
            rank=p.rank,
            year_became_pro=p.pro_year,
            games_count=games_count,
            income_ytd=income_ytd,
            income_ytd_str=income_ytd_str,
            income_career=income_career,
            income_career_str=income_career_str,
        )

        result.append(r)

    return result
