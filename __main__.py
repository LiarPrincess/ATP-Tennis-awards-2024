import os
from typing import Any
from atp import Player, get_ranking_top_100_for_date, get_players
from chart import Chart, Map
from page1_ranking import page1_ranking
from page2_game_set_match import page2_game_set_match
from page3_game_set_match_2 import page3_game_set_match_2
from page4_map import page4_map
from page5_body import page5_body
from page6_income import page6_income
from page7_fin import page7_fin

_PLAYER_COUNT = 50
# Day has to be one of the days the ranking is published.
# Go https://www.atptour.com/en/rankings/singles and use the date combo box.
_RANKING_NOW_DAY = "2024-12-30"
_RANKING_PAST_DAY = "2024-01-01"
_RANKING_NOW_DATE = f"{_RANKING_NOW_DAY}T00:00:00"
_RANKING_PAST_DATE = f"{_RANKING_PAST_DAY}T00:00:00"
_IMAGE_WIDTH = 1200
_OUTPUT_DIR_PATH = "output"
_ASSETS_DIR_PATH = "assets"


def main():
    players = _get_ranking(_RANKING_NOW_DAY)
    players_past = _get_ranking(_RANKING_PAST_DAY)

    print("1 Ranking")
    data = page1_ranking(
        date_past=_RANKING_PAST_DATE,
        ranking_past=players_past,
        date_now=_RANKING_NOW_DATE,
        ranking_now=players,
        award_count_rank_gain_lose=5,
        award_count_spread=5,
    )
    render_template("page1_ranking.html", data, "1_ranking.png")

    print("2 Game, set, match")
    data = page2_game_set_match(
        players,
        date_from=_RANKING_PAST_DATE,
        top_N=10,
        award_count_unlucky=5,
    )
    render_template("page2_game_set_match.html", data, "2_game_set_match.png")

    print("3 Game, set, match 2")
    data = page3_game_set_match_2(
        players,
        date_from=_RANKING_PAST_DATE,
        award_count_highest_defeated=5,
        award_count_game_count=6,
    )
    render_template("page3_game_set_match_2.html", data, "3_game_set_match_2.png")

    print("4 Map")
    data = page4_map(
        players,
        award_count_best_countries=3,
        award_count_best_player_per_continent=6,
    )
    render_template("page4_map.html", data, "4_map.png")

    print("5 Body")
    data = page5_body(
        players,
        award_count_age=5,
        award_count_height=3,
        award_count_weight=4,
    )
    render_template("page5_body.html", data, "5_body.png")

    print("6 Income")
    data = page6_income(players)
    render_template("page6_income.html", data, "6_income.png")

    print("7 Fin")
    data = page7_fin(players, date_from=_RANKING_PAST_DATE)
    render_template("page7_fin.html", data, "7_fin.png")


def render_template(template_name: str, context: Any, image_name: str):
    tmp_dir_path = _ASSETS_DIR_PATH
    os.makedirs(_OUTPUT_DIR_PATH, exist_ok=True)
    os.makedirs(tmp_dir_path, exist_ok=True)

    # Change chart to its path
    padding_x = 10
    context_dict: dict[str, Any] = {"width": _IMAGE_WIDTH, "padding_x": padding_x}
    image_name_without_extension, _ = os.path.splitext(image_name)
    chart_index = 1
    chart_width = _IMAGE_WIDTH - 2 * padding_x

    for name, o in vars(context).items():
        if isinstance(o, Chart | Map):
            chart_img_name = f"{image_name_without_extension}_chart_{chart_index}.png"
            chart_img_path = os.path.join(tmp_dir_path, chart_img_name)
            o.write_img(chart_img_path, width=chart_width)

            o = os.path.realpath(chart_img_path)
            chart_index += 1

        context_dict[name] = o

    # Write html
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    env = Environment(
        loader=FileSystemLoader("."),
        autoescape=select_autoescape(),
    )
    template = env.get_template(template_name)
    html = template.render(context_dict)

    html_name = image_name_without_extension + ".html"
    html_path = os.path.join(tmp_dir_path, html_name)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Render image
    from browser import save_png

    html_url = "file:" + os.path.realpath(html_path)
    image_path = os.path.realpath(os.path.join(_OUTPUT_DIR_PATH, image_name))
    save_png(html_url, image_path, width=_IMAGE_WIDTH)


def _get_ranking(day: str) -> list[Player]:
    print(f"Reading TOP {_PLAYER_COUNT} for {day}")

    rows_all = get_ranking_top_100_for_date(day)
    assert len(rows_all) == 100

    rows_all.sort(key=lambda r: r.rank)
    rows = rows_all[:_PLAYER_COUNT]

    player_ids = [r.id for r in rows]
    players = get_players(player_ids)

    result = list[Player]()
    id_to_player = {p.id: p for p in players}

    for r in rows:
        p = id_to_player[r.id]
        result.append(p)

    return result


if __name__ == "__main__":
    main()
