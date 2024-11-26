import os
from api import Player, get_ranking_top_100_for_date, get_players
from page import Page, Title
from write_1_ranking_change import write_ranking_change
from write_1_ranking_volatility import write_ranking_volatility

_PLAYER_COUNT = 50
# Day has to be one of the days the ranking is published.
# Go https://www.atptour.com/en/rankings/singles and use the date combo box.
_RANKING_NOW_DAY = "2024-11-25"
_RANKING_PAST_DAY = "2024-01-01"
_RANKING_NOW_DATE = f"{_RANKING_NOW_DAY}T00:00:00"
_RANKING_PAST_DATE = f"{_RANKING_PAST_DAY}T00:00:00"


def main():
    players = _get_ranking(_RANKING_NOW_DAY)
    players_past = _get_ranking(_RANKING_PAST_DAY)

    output_dir_path = "output"
    os.makedirs(output_dir_path, exist_ok=True)

    # MARK: 1. Ranking

    print("Writing: Ranking")

    page = Page()
    page.add(Title("Ranking"))

    write_ranking_change(
        page,
        past_date=_RANKING_PAST_DATE,
        past_ranking=players_past,
        now_date=_RANKING_NOW_DATE,
        now_ranking=players,
        award_count_raise=5,
        award_count_drop=3,
    )

    write_ranking_volatility(
        page,
        ranking=players,
        date_from=_RANKING_PAST_DATE,
        award_count_min_spread=5,
        award_count_max_spread=5,
    )

    path = os.path.join(output_dir_path, "1_ranking.md")
    page.write_html(path, width=1400)
    print("Before publishing please DELETE CACHE and generate again.")


# MARK: Helpers


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
