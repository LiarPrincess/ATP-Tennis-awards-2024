from atp.json_dict import JSONDict
from atp.helpers import create_urls, get_json

CACHE_PATH = "cache/atp_player_stats"


class PlayerStats_Service:
    def __init__(self, json: JSONDict) -> None:
        self.aces = json.get_int("Aces")
        self.double_faults = json.get_int("DoubleFaults")

        self.games_played = json.get_int("ServiceGamesPlayed")
        self.games_won_percentage = json.get_int("ServiceGamesWonPercentage")

        self.first_serve_percentage = json.get_int("FirstServePercentage")
        self.first_serve_points_won_percentage = json.get_int(
            "FirstServePointsWonPercentage"
        )
        self.second_serve_points_won_percentage = json.get_int(
            "SecondServePointsWonPercentage"
        )

        self.break_points_faced = json.get_int("BreakPointsFaced")
        self.break_points_saved_percentage = json.get_int("BreakPointsSavedPercentage")

        self.points_won_percentage = json.get_int("ServicePointsWonPercentage")


class PlayerStats_Return:
    def __init__(self, json: JSONDict) -> None:
        self.first_serve_return_points_won_percentage = json.get_int(
            "FirstServeReturnPointsWonPercentage"
        )
        self.second_serve_return_points_won_percentage = json.get_int(
            "SecondServeReturnPointsWonPercentage"
        )

        self.break_points_opportunities = json.get_int("BreakPointsOpportunities")
        self.break_points_converted_percentage = json.get_int(
            "BreakPointsConvertedPercentage"
        )

        self.games_played = json.get_int("ReturnGamesPlayed")
        self.games_won_percentage = json.get_int("ReturnGamesWonPercentage")
        self.points_won_percentage = json.get_int("ReturnPointsWonPercentage")
        self.total_points_won_percentage = json.get_int("TotalPointsWonPercentage")


def get_players_stats(
    player_ids: list[str],
) -> dict[str, tuple[PlayerStats_Service, PlayerStats_Return]]:
    """
    Stats - aces/breaks/returns/conversions
    https://www.atptour.com/en/-/www/stats/s0ag/2024/all?v=1
    """

    player_id_urls, urls = create_urls(
        player_ids,
        "https://www.atptour.com/en/-/www/stats/{id}/2024/all?v=1",
    )

    url_to_stats = get_json(urls, CACHE_PATH)
    result = dict[str, tuple[PlayerStats_Service, PlayerStats_Return]]()

    for p in player_id_urls:
        json = url_to_stats[p.url]
        inner = json.get_dict("Stats")

        service_json = inner.get_dict("ServiceRecordStats")
        return_json = inner.get_dict("ReturnRecordStats")

        service = PlayerStats_Service(service_json)
        return_ = PlayerStats_Return(return_json)
        result[p.id] = (service, return_)

    return result
