from atp_api.ranking import get_ranking_top_100, get_ranking_top_100_for_date
from atp_api.player_stats import PlayerStats_Service, PlayerStats_Return
from atp_api.player_activity import PlayerTournament
from atp_api.player_rank_history import PlayerRank
from atp_api.player_activity import (
    PlayerTournament,
    PlayerMatch_Round,
    PlayerMatch_Opponent,
    PlayerMatch_Set,
    PlayerMatch,
    PlayerMatch_Played,
    PlayerMatch_Bye,
    PlayerMatch_NotPlayed,
    PlayerMatch_Walkover,
    PlayerMatch_Retire,
    PlayerMatch_Default,
)

from typing import Literal as _Literal, assert_never as _assert_never
from atp_api.player_data import PlayerData as _PlayerData
from atp_api.json_dict import JSONDict as _JSONDict


class Player(_PlayerData):

    def __init__(
        self,
        id: str,
        json: _JSONDict,
        ytd_stats_service: PlayerStats_Service,
        ytd_stats_return: PlayerStats_Return,
        career_tournaments: list[PlayerTournament],
        career_rank_history: list[PlayerRank],
    ) -> None:
        super().__init__(id, json)
        self.ytd_stats_service = ytd_stats_service
        self.ytd_stats_return = ytd_stats_return
        self.career_tournaments = career_tournaments
        self.career_rank_history = career_rank_history
        self._date_to_rank = {r.date: r for r in career_rank_history}

    def get_rank_at_date(self, date: str) -> "PlayerRank|_Literal['Deceased']":
        if self.active == "Deceased":
            last_rank = self.career_rank_history[-1]
            if date > last_rank.date:
                return "Deceased"

        elif self.active == "Active":
            pass
        else:
            _assert_never(self.active)

        # Fix '2024-01-21' -> '2024-01-21T00:00:00'
        if "T" not in date:
            date += "T00:00:00"

        rank = self._date_to_rank.get(date)

        if rank is not None:
            return rank

        # We do not have an exact entry for a given date.
        # This means that we have to take the rank from the previous week.

        for rank in reversed(self.career_rank_history):
            if rank.date < date:
                self._date_to_rank[date] = rank
                return rank

        assert False, f"{self.name_first} {self.name_last}: No ranking for {date}."


def get_players(player_ids: list[str]) -> list[Player]:
    from atp_api.player_data import get_players_data_json
    from atp_api.player_stats import get_players_stats
    from atp_api.player_activity import get_players_tournaments
    from atp_api.player_rank_history import get_players_rank_history

    id_to_data = get_players_data_json(player_ids)
    id_to_stats = get_players_stats(player_ids)
    id_to_tournaments = get_players_tournaments(player_ids)
    id_to_rank_history = get_players_rank_history(player_ids)

    result = list[Player]()

    for id in player_ids:
        data = id_to_data[id]
        stats_service, stats_return = id_to_stats[id]
        tournaments = id_to_tournaments[id]
        rank_history = id_to_rank_history[id]

        p = Player(id, data, stats_service, stats_return, tournaments, rank_history)
        result.append(p)

    return result
