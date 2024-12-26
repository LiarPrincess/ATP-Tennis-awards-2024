from typing import Literal
from datetime import datetime, timedelta
from dataclasses import dataclass
from atp import Player
from chart import Chart
from helpers import *


@dataclass
class Page:

    @dataclass
    class Row:
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
        def birthday(self) -> str:
            return substring_until(self.player.birth_date, "T")

        @property
        def years_since_pro(self) -> int:
            return self.age_years - self.age_pro

        @property
        def age_decimal(self) -> float:
            return self.age_years + self.age_days / 366.0

    age_chart: Chart
    age_awards_min: list[Row]
    age_awards_max: list[Row]

    height_chart: Chart
    height_awards_min: list[Row]
    height_awards_max: list[Row]

    weight_chart: Chart
    weight_awards_min: list[Row]
    weight_awards_max: list[Row]

    hand_right_backhand_1: list[Row]
    hand_right_backhand_2: list[Row]
    hand_left_backhand_1: list[Row]
    hand_left_backhand_2: list[Row]


def page5_body(
    players: list[Player],
    award_count_age: int,
    award_count_height: int,
    award_count_weight: int,
) -> Page:
    rows = _get_rows(players)

    age_chart = _create_age_chart(rows)
    age_awards_min = filter_award_min(rows, award_count_age, lambda r: r.age_decimal)
    age_awards_max = filter_award_max(rows, award_count_age, lambda r: r.age_decimal)

    height_chart, height_awards_min, height_awards_max = _height_weight(
        rows,
        key=lambda r: r.height_cm,
        y_axis_label="Height [cm]",
        legend_average_template="Average {0:.1f} cm",
        award_count=award_count_height,
    )

    weight_chart, weight_awards_min, weight_awards_max = _height_weight(
        rows,
        key=lambda r: r.weight_kg,
        y_axis_label="Weight [kg]",
        legend_average_template="Average {0:.1f} kg",
        award_count=award_count_weight,
    )

    hand_right_backhand_1 = list[Page.Row]()
    hand_right_backhand_2 = list[Page.Row]()
    hand_left_backhand_1 = list[Page.Row]()
    hand_left_backhand_2 = list[Page.Row]()

    for r in rows:
        play_back = r.hand_play, r.hand_back

        if play_back == ("R", "1"):
            hand_right_backhand_1.append(r)
        elif play_back == ("R", "2"):
            hand_right_backhand_2.append(r)
        elif play_back == ("L", "1"):
            hand_left_backhand_1.append(r)
        elif play_back == ("L", "2"):
            hand_left_backhand_2.append(r)
        else:
            assert False, play_back

    return Page(
        age_chart=age_chart,
        age_awards_min=age_awards_min,
        age_awards_max=age_awards_max,
        height_chart=height_chart,
        height_awards_min=height_awards_min,
        height_awards_max=height_awards_max,
        weight_chart=weight_chart,
        weight_awards_min=weight_awards_min,
        weight_awards_max=weight_awards_max,
        hand_right_backhand_1=hand_right_backhand_1,
        hand_right_backhand_2=hand_right_backhand_2,
        hand_left_backhand_1=hand_left_backhand_1,
        hand_left_backhand_2=hand_left_backhand_2,
    )


def _create_age_chart(rows: list[Page.Row]) -> Chart:
    chart = Chart()
    chart.set_show_grid(True)
    chart.set_aspect_rato(100, 50)

    ranks = [r.rank for r in rows]

    ages_pro = [r.age_pro for r in rows]
    ages_pro_color_map = chart.create_color_map(
        ages_pro,
        ["purple"],
    )
    ages_pro_color = [ages_pro_color_map[r.age_pro] for r in rows]
    chart.add_bar(ranks, ages_pro, color=ages_pro_color)

    ages = [r.age_decimal for r in rows]
    ages_from_pro = [r.age_decimal - r.age_pro for r in rows]
    ages_color_map = chart.create_color_map(
        ages,
        ["cyan"],
    )
    ages_color = [ages_color_map[a] for a in ages]
    chart.add_bar(ranks, ages_from_pro, bottom=ages_pro, color=ages_color)

    # Average
    rank_min = min(ranks)
    rank_max = max(ranks)
    age_avg = average(ages)
    age_pro_avg = average(a for a in ages_pro if a != 0)
    chart.add_horizontal_line(
        age_avg,
        rank_min - 0.4,
        rank_max + 0.4,
        color="yellow",
    )
    chart.add_horizontal_line(
        age_pro_avg,
        rank_min - 0.4,
        rank_max + 0.4,
        color="red",
    )

    chart.add_legend(
        [
            f"Average {age_avg:.1f} years",
            f"Average age when pro {age_pro_avg:.1f} years",
            "Age when pro",
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
    y_axis.set_major_tick_interval(2)
    y_axis.set_range(12, max_age)

    return chart


def _height_weight(
    rows: list[Page.Row],
    key: Callable[[Page.Row], int],
    y_axis_label: str,
    legend_average_template: str,
    award_count: int,
) -> tuple[Chart, list[Page.Row], list[Page.Row]]:
    chart = Chart()
    chart.set_show_grid(True)
    chart.set_aspect_rato(100, 50)

    ranks = [r.rank for r in rows]

    values = [key(r) for r in rows]
    color_map = chart.create_color_map(
        values,
        ["pink", "purple", "cyan"],
    )
    colors = [color_map[r] for r in values]
    chart.add_bar(ranks, values, color=colors)

    values_min = min(values)
    values_max = max(values)
    values_avg = average(values)

    # Average
    rank_min = min(ranks)
    rank_max = max(ranks)
    chart.add_horizontal_line(
        values_avg,
        rank_min - 0.4,
        rank_max + 0.4,
        color="green",
    )

    # Legend
    legend_average = legend_average_template.format(values_avg)
    chart.add_legend([legend_average])

    # X axis
    x_axis = chart.x_axis
    x_axis.set_label("Player rank")

    # Y axis
    y_axis = chart.y_axis
    y_axis.set_label(y_axis_label.format(values_avg))
    y_axis.set_major_tick_interval(5)

    values_min_10 = round_down(values_min, multiple_of=5)
    values_max_10 = round_down(values_max, multiple_of=5)
    y_axis.set_range(values_min_10 - 5, values_max_10 + 5)

    # Awards
    awards_min = filter_award_min(rows, award_count, key)
    awards_max = filter_award_max(rows, award_count, key)
    return chart, awards_min, awards_max


# MARK: Rows


def _get_rows(players: list[Player]) -> list[Page.Row]:
    result = list[Page.Row]()
    now = datetime.now()

    for p in players:
        assert p.rank

        birth_date_str = p.birth_date
        birth_date = datetime.fromisoformat(birth_date_str)
        age_years, age_days = _date_diff_years_days(birth_date, now)

        if p.pro_year is None:
            age_pro = 0
        else:
            age_pro = p.pro_year - birth_date.year

        # p_str = to_str_player(p)
        # print(f"{p_str} | {p.birth_date} | {age_years}y {age_days}d | {age_pro} y")

        result.append(
            Page.Row(
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


def _date_diff_years_days(past: datetime, now: datetime) -> tuple[int, int]:
    now = datetime(year=now.year, month=now.month, day=now.day)
    year_count = now.year - past.year
    last_birthday = datetime(year=now.year, month=past.month, day=past.day)
    had_birthday = now >= last_birthday

    if not had_birthday:
        year_count -= 1
        last_birthday = datetime(year=now.year - 1, month=past.month, day=past.day)

    day_count = 0
    day_count_day = last_birthday
    day = timedelta(days=1)

    while day_count_day != now:
        day_count_day += day
        day_count += 1

    # print(f"{past} | {year_count} years {day_count} days")
    return year_count, day_count
