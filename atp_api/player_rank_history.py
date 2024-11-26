from atp_api.json_dict import JSONDict
from atp_api.helpers import create_urls, get_json

CACHE_PATH = "cache/atp_player_rank_history"


class PlayerRank:
    def __init__(self, json: JSONDict) -> None:
        # There are entries for 'race' and 'roll':
        # - roll is the correct one.
        # - race is race to Turin
        #
        # Example for Sinner at 2024-05-27T00:00:00:
        #      | rank | points
        # race |    1 | 4500
        # roll |    2 | 8770
        #
        # If you go to the website https://www.atptour.com/en/rankings/singles?dateWeek=2024-05-27:
        # Rank | Player   | Age | Points | +/-  | Played | Dropping | Next Best
        # 1    | Djokovic | 37  | 9,960  | +100 |     18 |    2,000 | -
        # 2    | Sinner   | 22  | 8,770  | -    |     19 |       45 | -

        self.date = json.get_str("RankDate")

        self.rank = json.get_int("SglRollRank")
        self.points = json.get_int("SglRollPoints")
        self.is_tie = json.get_bool("SglRollTie")
        # self.sgl_race_rank = json.get_int("SglRaceRank")
        # self.sgl_race_tie = json.get_bool("SglRaceTie")
        # self.sgl_race_points = json.get_int("SglRacePoints")

        # self.dbl_rank = json.get_int("DblRollRank")
        # self.dbl_tie = json.get_bool("DblRollTie")
        # self.dbl_points = json.get_int("DblRollPoints")


def get_players_rank_history(player_ids: list[str]) -> dict[str, list[PlayerRank]]:
    """
    Rank - rank history
    https://www.atptour.com/en/-/www/rank/history/s0ag?v=1
    """

    player_id_urls, urls = create_urls(
        player_ids,
        "https://www.atptour.com/en/-/www/rank/history/{id}?v=1",
    )

    url_to_stats = get_json(urls, CACHE_PATH)
    result = dict[str, list[PlayerRank]]()

    for p in player_id_urls:
        json = url_to_stats[p.url]
        json_list = json.get_list("History")

        history = list[PlayerRank]()
        result[p.id] = history

        for r in json_list:
            assert isinstance(r, dict)
            r_json = JSONDict(r)
            history.append(PlayerRank(r_json))

        history.sort(key=lambda r: r.date)

    return result
