import numpy as np
import datetime
from dataclasses import dataclass
from page import Page, Subtitle, Award, Chart, Paragraph
from atp_api import Player
from helpers import *

_THOUSAND = 1000
_MILLION = _THOUSAND * _THOUSAND
_YEAR = datetime.datetime.now().year


@dataclass
class _Row:
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


def write_income(page: Page, players: list[Player]):
    rows = _get_rows(players)

    # Income since {date}
    page.add(Subtitle("Income ytd"))

    ranks = [r.rank for r in rows]
    income_ytd = [r.income_ytd for r in rows]
    income_ytd_avg = average(income_ytd)

    _write_income_chart(
        page,
        ranks,
        income_ytd,
        y_axis_label="Income [$1M]",
        y_axis_scale=_MILLION,
        y_axis_tick_interval=_MILLION,
        has_polynomial=True,
        average=income_ytd_avg,
    )

    above_million = [x for x in income_ytd if x >= _MILLION]
    above_million_len = len(above_million)

    page.add(
        Award(
            "🐋",
            f"There are no awards in this category. {above_million_len} of them made more than $1M this year. Remember this chart next time you see somebody complaining about the cost of… well anything (🔧🚗).",
        )
    )

    page.add(
        Paragraph(
            "We could compare that to other sports, but most of them would not be noticeable. In fencing only 🇭🇰 Vivian Kong Man Wai (🥇 women épée) and 🇭🇰 Edgar Cheung Ka-long (🥇 men foil) would be visible, as Hong Kong awarded them $768,172 for their Olympic golds. On the other hand 🇺🇸 Lee Kiefer (🥇 women foil) got $37,500 for their medal."
        )
    )

    # Income since {date} per game
    page.add(Subtitle(f"Income ytd per game"))
    income_ytd_per_game = [r.income_ytd / r.games_count for r in rows]
    income_ytd_per_game_avg = average(income_ytd_per_game)
    _write_income_chart(
        page,
        ranks,
        income_ytd_per_game,
        y_axis_label="Income [$1k]",
        y_axis_scale=_THOUSAND,
        y_axis_tick_interval=500,
        has_polynomial=True,
        average=income_ytd_per_game_avg,
    )

    # page.add(
    #     Award(
    #         "🎾",
    #         f"Next time you see somebody smashing the racket you have to remind yourself that they just made ${income_ytd_per_game_avg:.0f} anyway (on average).",
    #     )
    # )

    # Career income
    page.add(Subtitle(f"Total career income"))
    income_career = [r.income_career for r in rows]
    income_career_avg = average(income_career)
    _write_income_chart(
        page,
        ranks,
        income_career,
        y_axis_label="Income [$1M]",
        y_axis_scale=_MILLION,
        y_axis_tick_interval=10 * _MILLION,
        average=income_career_avg,
    )

    page.add(Award("🔍", "Try to find Nole."))
    page.add(Paragraph(f"Hint: it is not that hard!"))

    # Income per year
    page.add(Subtitle(f"Average income per year as a pro"))
    income_per_year = [r.avg_income_per_year for r in rows]
    income_per_year_avg = average(i for i in income_per_year if i != 0)
    _write_income_chart(
        page,
        ranks,
        income_per_year,
        y_axis_label="Income [$1k or 0 if no data available]",
        y_axis_scale=_MILLION,
        y_axis_tick_interval=500 * _THOUSAND,
        average=income_per_year_avg,
    )

    page.add(
        Paragraph(
            "Note that players tend to earn less at the beginning of their career. It may be better to do separate charts for 1st, 2nd etc. year.",
        )
    )


def _write_income_chart(
    page: Page,
    ranks: list[int],
    values: list[int] | list[float],
    y_axis_label: str,
    y_axis_scale: int,
    y_axis_tick_interval: int,
    average: float | None = None,
    has_polynomial: bool = False,
):
    chart = Chart()
    chart.set_show_grid(True)
    chart.set_aspect_rato(100, 60)
    page.add(chart)

    # Bars
    color_map = chart.create_color_map(values)
    colors = [color_map[v] for v in values]
    chart.add_bars(ranks, values, color=colors)

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
        )
        chart.add_legend()

    if has_polynomial:
        poly_fn = np.polynomial.Chebyshev.fit(ranks, values, deg=10)

        poly_x = np.arange(rank_min, rank_max, step=0.1)
        poly_y = poly_fn(poly_x)

        chart.add_plot(poly_x, poly_y, label="Trend", color="black", line_width=2)
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
    y_axis.set_major_ticks(y_axis_tick_interval)

    def format_y_tick(value: float, pos) -> str:
        x = value / y_axis_scale
        s = str(x)

        if s.endswith(".0"):
            s = s[:-2]

        return s

    y_axis.set_major_formatter_fn(format_y_tick)


def _format_money_as_int(n: float) -> str:
    s = f"{n:.0f}"
    result = ""

    for index, c in enumerate(reversed(s)):
        # 9 876 543 210
        if index != 0 and index % 3 == 0:
            result = "," + result
        result = c + result

    return result


def _get_rows(players: list[Player]) -> list[_Row]:

    def parse_money(s: str) -> tuple[int, str]:
        assert s.startswith("$")
        i = s.strip("$")
        i = i.replace(",", "")
        return int(i), s

    result = list[_Row]()

    for p in players:
        assert p.rank

        income_ytd, income_ytd_str = parse_money(p.ytd_prize_formatted)
        income_career, income_career_str = parse_money(p.career_prize_formatted)

        games_count_service = p.ytd_stats_service.games_played
        games_count_return = p.ytd_stats_return.games_played
        games_count = games_count_service + games_count_return

        r = _Row(
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
