from typing import Literal
from dataclasses import dataclass
from page import Page, Subtitle, Award, Table, Chart, Paragraph
from atp_api import Player
from helpers import *

_YEAR_DAY_COUNT = 365


@dataclass
class _Row:
    player: Player
    rank: int
    age_years: int
    age_days: int
    age_pro: int
    height_cm: int
    weight_kg: int
    hand_play: Literal["R", "L"]
    hand_back: Literal["1", "2"]

    @property
    def age_decimal(self) -> float:
        return self.age_years + self.age_days / _YEAR_DAY_COUNT


def write_body_stats(
    page: Page,
    players: list[Player],
    award_count_age: int,
    award_count_height: int,
    award_count_weight: int,
):
    "Compare physical attributes."

    rows = _get_rows(players)

    page.add(Subtitle(f"Age"))
    _write_age(page, rows, award_count_age)

    page.add(Subtitle(f"Height"))
    _write_height_weight(
        page,
        rows,
        key=lambda r: r.height_cm,
        y_axis_label="Height [cm]",
        legend_average_template="Average {0:.1f} cm",
        award_min_emoji="🐞",
        award_min_text="Ladybug award for the shortest.",
        award_max_emoji="🦒",
        award_max_text="Giraffe award for the tallest.",
        award_count=award_count_height,
    )

    page.add(Subtitle(f"Weight"))
    _write_height_weight(
        page,
        rows,
        key=lambda r: r.weight_kg,
        y_axis_label="Weight [kg]",
        legend_average_template="Average {0:.1f} kg",
        award_min_emoji="🪶",
        award_min_text="Feather award for the lightest.",
        award_max_emoji="🐘",
        award_max_text="Elephant award for the heaviest.",
        award_count=award_count_weight,
    )

    page.add(Subtitle(f"Hand"))
    _write_hand(page, rows)


# MARK: Age


def _write_age(page: Page, rows: list[_Row], award_count: int):
    chart = Chart()
    chart.set_show_grid(True)
    page.add(chart)

    ranks = [r.rank for r in rows]

    ages_pro = [r.age_pro for r in rows]
    ages_pro_color_map = chart.create_color_map(ages_pro)
    ages_pro_color = [ages_pro_color_map[r.age_pro] for r in rows]
    chart.add_bars(ranks, ages_pro, color=ages_pro_color)

    ages = [r.age_decimal for r in rows]
    ages_from_pro = [r.age_decimal - r.age_pro for r in rows]
    chart.add_bars(ranks, ages_from_pro, bottom=ages_pro, color="black")

    # Average
    rank_min = min(ranks)
    rank_max = max(ranks)
    age_avg = average(ages)
    age_pro_avg = average(a for a in ages_pro if a != 0)
    chart.add_horizontal_line(age_avg, rank_min - 0.4, rank_max + 0.4)
    chart.add_horizontal_line(age_pro_avg, rank_min - 0.4, rank_max + 0.4, color="red")

    chart.add_legend(
        [
            f"Average {age_avg:.1f} years",
            f"Average when becoming pro {age_pro_avg:.1f} years",
            "Age when becoming pro",
            "Age",
        ]
    )

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player rank")

    # Y axis
    max_age = max(r.age_years for r in rows) + 1
    y_axis = chart.y_axis
    y_axis.set_label("Age")
    y_axis.set_major_ticks(2)
    y_axis.set_range(10, max_age)

    def add_award(emoji: str, text: str, rows: list[_Row]):
        table = Table()
        table.headers.append(Table.Header("Player", is_player_column=True))
        table.headers.append(Table.Header("Birth date"))
        table.headers.append(Table.Header("Age"))
        table.headers.append(Table.Header("Became pro at"))
        table.headers.append(Table.Header("Years since becoming pro"))

        for r in rows:
            p = r.player
            birth_day = substring_until(p.birth_date, "T")
            age = f"{r.age_years} years {r.age_days} days"
            pro = f"{r.age_pro} years"
            since_pro = f"{r.age_years-r.age_pro} years"
            row = Table.Row([p, birth_day, age, pro, since_pro])
            table.rows.append(row)

        if rows:
            page.add(Award(emoji, text))
            page.add(table)

    award_rows = filter_award_min(rows, award_count, lambda r: r.age_decimal)
    add_award("🐣", "Chick award for the youngest.", award_rows)

    award_rows = filter_award_max(rows, award_count, lambda r: r.age_decimal)
    add_award("🐦‍🔥", "Phoenix award for the oldest.", award_rows)


# MARK: Height/weight


def _write_height_weight(
    page: Page,
    rows: list[_Row],
    key: Callable[[_Row], int],
    y_axis_label: str,
    legend_average_template: str,
    award_min_emoji: str,
    award_min_text: str,
    award_max_emoji: str,
    award_max_text: str,
    award_count: int,
):
    chart = Chart()
    chart.set_show_grid(True)
    page.add(chart)

    ranks = [r.rank for r in rows]

    values = [key(r) for r in rows]
    color_map = chart.create_color_map(values)
    colors = [color_map[key(r)] for r in rows]
    chart.add_bars(ranks, values, color=colors)

    values_min = min(values)
    values_max = max(values)
    values_avg = average(values)

    # Average
    rank_min = min(ranks)
    rank_max = max(ranks)
    chart.add_horizontal_line(values_avg, rank_min - 0.4, rank_max + 0.4)

    # Legend
    legend_average = legend_average_template.format(values_avg)
    chart.add_legend([legend_average])

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player rank")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label(y_axis_label.format(values_avg))
    y_axis.set_major_ticks(5)

    values_min_10 = round_down(values_min, multiple_of=5)
    values_max_10 = round_down(values_max, multiple_of=5)
    y_axis.set_range(values_min_10 - 5, values_max_10 + 5)

    def add_award(page: Page, emoji: str, text: str, rows: list[_Row]):
        table = Table()
        table.headers.append(Table.Header("Player", is_player_column=True))
        table.headers.append(Table.Header("Age"))
        table.headers.append(Table.Header("Height"))
        table.headers.append(Table.Header("Weight"))

        for r in rows:
            p = r.player
            height = f"{r.height_cm} cm"
            weight = f"{r.weight_kg} kg"
            row = Table.Row([p, p.age, height, weight])
            table.rows.append(row)

        if rows:
            page.add(Award(emoji, text))
            page.add(table)

    award_rows = filter_award_min(rows, award_count, lambda r: key(r))
    add_award(page, award_min_emoji, award_min_text, award_rows)

    award_rows = filter_award_max(rows, award_count, lambda r: key(r))
    add_award(page, award_max_emoji, award_max_text, award_rows)


# MARK: Hand


def _write_hand(page: Page, rows: list[_Row]):
    right_1 = list[_Row]()
    right_2 = list[_Row]()
    left_1 = list[_Row]()
    left_2 = list[_Row]()

    for r in rows:
        play_back = r.hand_play, r.hand_back

        if play_back == ("R", "1"):
            right_1.append(r)
        elif play_back == ("R", "2"):
            right_2.append(r)
        elif play_back == ("L", "1"):
            left_1.append(r)
        elif play_back == ("L", "2"):
            left_2.append(r)
        else:
            assert False, play_back

    chart = Chart()
    ax = chart.ax
    ax.set_axis_off()
    page.add(chart)

    max_x = 0
    min_x = 0
    max_y = 0
    min_y = 0

    from typing import TypeVar

    T = TypeVar("T")
    font_size = 15

    def group_to_count(os: list[T], count: int) -> list[list[T]]:
        result = list[list[T]]()
        current = list[T]()

        for o in os:
            current.append(o)

            if len(current) == count:
                result.append(current)
                current = list()

        # Last non-full list
        if current:
            result.append(current)

        return result

    def add_players(
        rows: list[_Row],
        hand_play: Literal["left", "right"],
        hand_back: Literal["1", "2"],
    ):
        nonlocal max_x, min_x, max_y, min_y
        margin_x = 0.002
        margin_y = 0.0002
        column_width = 0.1
        column_height = 0.003
        count_per_column = 10

        columns = group_to_count(rows, count=count_per_column)
        previous_x = 0

        for rs in columns:
            lines = list[str]()

            for r in rs:
                s = to_str_player(r.player)
                lines.append(s)

            s = "\n".join(lines)
            t = chart.ax.text(0, 0, s, fontsize=font_size)

            clip_box = t.get_clip_box()
            tight_box = t.get_tightbbox()
            assert clip_box is not None
            assert tight_box is not None
            width = column_width * (tight_box.width / clip_box.width)
            height = column_height * (tight_box.height / clip_box.height)

            if hand_play == "left":
                x = previous_x - width - margin_x
                previous_x = x
                min_x = min(previous_x, min_x)
            elif hand_play == "right":
                x = previous_x + margin_x
                previous_x = x + width
                max_x = max(previous_x, max_x)

            if hand_back == "1":
                y = margin_y
                t.set_verticalalignment("bottom")
                max_y = max(margin_y + height, max_y)
            elif hand_back == "2":
                y = -margin_y
                t.set_verticalalignment("top")
                min_y = min(-margin_y - height, min_y)

            t.set_position((x, y))

    add_players(right_1, "right", "1")
    add_players(right_2, "right", "2")
    add_players(left_1, "left", "1")
    add_players(left_2, "left", "2")

    # Legend
    def add_legend(s: str, x: float, y: float, rotation: int = 0):
        ax.text(
            x,
            y,
            s,
            ha="center",
            va="center",
            fontsize=font_size + 2,
            weight="bold",
            rotation=rotation,
        )

    # X axis
    margin = 0.004
    add_legend("Left handed", min_x - margin, 0, rotation=90)
    add_legend("Right handed", max_x + margin, 0, rotation=270)
    margin = 0
    chart.add_horizontal_line(0, min_x + margin, max_x - margin)
    margin = 0.003
    x_axis = chart.x_axis
    x_axis.set_range(min_x - margin, max_x + margin)

    # Y axis
    margin = 0
    add_legend("1 handed backhand", 0, max_y + margin)
    add_legend("2 handed backhand", 0, min_y - margin)
    margin = 0
    chart.add_vertical_line(0, min_y + margin, max_y - margin)
    margin = 0
    y_axis = chart.y_axis
    y_axis.set_range(min_y - margin, max_y + margin)

    # Wikipedia - population
    page.add(
        Award(
            "🍆",
            "No awards for handedness. Waiting for the players to grow the 3rd hand.",
        )
    )

    page.add(
        Paragraph(
            "Or maybe we should give it to Anthony Ammirati? You know… the French pole vaulter from the Olympics."
        )
    )

    left_count = len(left_1) + len(left_2)
    left_pct = 100.0 * left_count / len(rows)
    page.add(
        Paragraph(
            f"Anyway, according to Wikipedia 10% of the people are left handed. Tennis players fairly close to that at {left_pct:.1f}%. For comparison: 30% of the TOP 50 fencers are left handed."
        )
    )

    table = Table()
    table.headers.append(Table.Header("🤺"))
    table.headers.append(Table.Header("Female"))
    table.headers.append(Table.Header("Male"))
    table.rows.append(Table.Row(["Épée", 18, 14]))
    table.rows.append(Table.Row(["Foil", 18, 19]))
    table.rows.append(Table.Row(["Saber", 12, 6]))
    page.add(table)

    # Back hand
    page.add(Award("🐙", "Octopus award for 1 handed backhand. (See table above.)"))


# MARK: Rows


def _get_rows(players: list[Player]) -> list[_Row]:

    from datetime import datetime

    result = list[_Row]()
    now = datetime.now()

    for p in players:
        assert p.rank

        birth_date_str = p.birth_date
        birth_date = datetime.fromisoformat(birth_date_str)
        age_delta = now - birth_date
        age_years, age_days = divmod(age_delta.days, _YEAR_DAY_COUNT)

        if p.pro_year is None:
            age_pro = 0
        else:
            age_pro = p.pro_year - birth_date.year

        # p_str = to_str_player(p)
        # print(f"{p_str} | {p.birth_date} | {age_years}y {age_days}d | {age_pro} y")

        result.append(
            _Row(
                p,
                p.rank,
                age_years,
                age_days,
                age_pro,
                p.height_cm,
                p.weight_kg,
                p.hand_play,
                p.hand_back,
            )
        )

    return result
