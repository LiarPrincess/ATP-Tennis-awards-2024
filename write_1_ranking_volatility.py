from dataclasses import dataclass
from page import Page, Subtitle, Award, Table, Chart
from atp import Player
from helpers import *


@dataclass
class _Row:
    player: Player
    current_rank: int
    highest_rank: int
    "Highest obtained rank: 1, 2, 3…."
    lowest_rank: int
    "Lowest obtained rank: 99, 98, 97…."
    max_rank_increase: int
    "Maximum number of positions gained in a single ranking change."
    max_rank_drop: int
    "Maximum number of positions dropped in a single ranking change."

    @property
    def rank_spread(self) -> int:
        return self.lowest_rank - self.highest_rank

    def __str__(self) -> str:
        r = self
        p = self.player
        return f"{r.current_rank} {p.name_last} | {r.highest_rank}-{r.lowest_rank} | ⬆️{r.max_rank_increase} ⬇️{r.max_rank_drop}"


def write_ranking_volatility(
    page: Page,
    players: list[Player],
    date_from: str,
    award_count_min_spread: int,
    award_count_max_spread: int,
):
    "Compare rank fluctuation."

    date_from_short = substring_until(date_from, "T")
    page.add(Subtitle(f"Rank spread since {date_from_short}"))

    rows = _get_rows(players, date_from)
    _write_chart(page, rows)
    _write_awards(page, rows, award_count_min_spread, award_count_max_spread)


def _write_chart(page: Page, rows: list[_Row]):

    chart = Chart()
    chart.set_show_grid(True)
    page.add(chart)

    color_map = chart.create_color_map(r.rank_spread for r in rows)

    for r in rows:
        x = r.current_rank
        height = r.lowest_rank - r.highest_rank
        color = color_map[r.rank_spread]
        chart.add_bar(x, height, bottom=r.highest_rank, color=color)
        chart.add_scatter(x, r.current_rank, color="black", marker="D", size=20)

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player rank")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label("Highest/lowest rank (current rank in black)")

    tick_count = 10
    spread = max(r.lowest_rank for r in rows)
    y_axis.set_major_ticks(round_down(spread // tick_count, multiple_of=10))


def _write_awards(
    page: Page,
    rows: list[_Row],
    award_count_min_spread: int,
    award_count_max_spread: int,
):

    def add_award(emoji: str, text: str, rows: list[_Row]):
        table = Table()
        table.headers.append(Table.Header("Player", is_player_column=True))
        table.headers.append(Table.Header("Age"))
        table.headers.append(Table.Header("Highest rank"))
        table.headers.append(Table.Header("Lowest rank"))
        table.headers.append(Table.Header("Spread"))

        for r in rows:
            p = r.player
            assert p.age
            row = Table.Row([p, p.age, r.highest_rank, r.lowest_rank, r.rank_spread])
            table.rows.append(row)

        if rows:
            page.add(Award(emoji, text))
            page.add(table)

    # Smallest spread
    award_rows = filter_award_min(
        rows,
        count=award_count_min_spread,
        key=lambda r: r.rank_spread,
    )
    add_award(
        "🪺",
        "Nest award for the most consistent players.",
        award_rows,
    )

    # Biggest spread
    award_rows = filter_award_max(
        rows,
        count=award_count_max_spread,
        key=lambda r: r.rank_spread,
    )
    add_award(
        "🐇",
        "Bunny award for those who like to hop around.",
        award_rows,
    )


def _get_rows(players: list[Player], date_from: str) -> list[_Row]:
    result = list[_Row]()

    for p in players:
        ranks = [r for r in p.career_rank_history if r.date >= date_from]
        ranks.sort(key=lambda r: r.date)
        assert ranks

        lowest_rank = -9999
        highest_rank = 9999
        max_rank_increase = -9999
        max_rank_drop = 9999
        previous_rank = None

        for r in ranks:
            # Smaller number -> higher rank
            lowest_rank = max(lowest_rank, r.rank)
            highest_rank = min(highest_rank, r.rank)

            if previous_rank is not None:
                diff = previous_rank.rank - r.rank
                max_rank_increase = max(max_rank_increase, diff)
                max_rank_drop = min(max_rank_drop, diff)

            previous_rank = r

        current_rank = p.rank
        assert current_rank is not None

        result.append(
            _Row(
                p,
                current_rank,
                highest_rank,
                lowest_rank,
                max_rank_increase,
                max_rank_drop,
            )
        )

    return result
