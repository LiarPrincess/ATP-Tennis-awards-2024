from typing import Literal, assert_never
from dataclasses import dataclass
from atp_api.json_dict import JSONDict
from atp_api.helpers import create_urls, get_json_or_none

CACHE_PATH = "cache/atp_player_activity"


# MARK: Tournament


class PlayerTournament:

    Type = Literal[
        "Grand slam",
        "Challenger",
        "ATP Finals",
        "Next Gen ATP Finals",
        "Olympics",
        "Davis Cup",
        "ATP Cup",
        "Laver Cup",
        "United Cup",
        "1000",
        "500",
        "250",
        "Q",  # Old ATP Masters 1000?
        "CS",  # Total prize < $800 000
        "WS",  # Total prize < $500 000
        "FU",  # Total prize <  $15 000
        "PZ",  # Miscellaneous Prize Money, Profit Share…
    ]

    @dataclass
    class Location:
        city: str | None
        "New York"
        country: str | None
        "United States"
        # location: str
        # "NY, U.S.A."

    def __init__(self, json: "JSONDict") -> None:
        self.id = json.get_str("EventId")
        self.name = json.get_str("EventName")
        "ATP Masters 1000 Monte-Carlo/ATP Masters 1000 Cincinnati"
        self.name_display = json.get_str("EventDisplayName")
        "Rolex Monte-Carlo Masters/Cincinnati Open"
        # self.title = json.get_str_or_none("EventTitle")
        # self.sc_display_name = json.get_str("ScDisplayName")
        self.url = json.get_str("TournamentUrl")

        location = json.get_dict("Location")
        location_city = location.get_str_or_none("EventCity")
        location_country = location.get_str_or_none("EventCountry")
        # location_location = location.get_str("EventLocation")
        self.location = PlayerTournament.Location(location_city, location_country)

        self.date = json.get_str("EventDate")
        self.date_end = json.get_str("PlayEndDate")

        type = json.get_str("EventType")
        self.type = _get_tournament_type(self.name, type)

        surface = json.get_str("Surface")
        surface = surface if surface else None
        assert surface in ("Grass", "Clay", "Hard", "Carpet", None)
        self.surface = surface

        in_out_door = json.get_str_or_none("InOutdoor")
        in_out_door = in_out_door if in_out_door else None
        assert in_out_door in ("I", "O", None)
        self.in_out_door = in_out_door

        self.draw_size = json.get_int("SglDrawSize")
        # self.dbl_draw_size = json.get_int("DblDrawSize")

        self.prize = json.get_int("Prize")
        self.prize_currency_symbol = json.get_str("CurrSymbol")
        self.prize_usd = json.get_int("PrizeUsd")

        self.player_won_count = json.get_int("Won")
        self.player_lost_count = json.get_int("Lost")

        self.matches = list[PlayerMatch]()
        matches_json_list = json.get_list("Matches")

        for m in matches_json_list:
            assert isinstance(m, dict)
            m_json = JSONDict(m)
            match = _get_match(m_json)
            self.matches.append(match)

        # Oldest -> newest
        self.matches.reverse()

        # =====================
        # === Not important ===
        # =====================

        # self.points = json.get_int("Points")
        # self.is_countable_title = json.get_bool("CountableTitle")
        # self.hi_round = json.get_dict("HiRound")
        # self.player_rank = json.get_int("PlayerRank")
        # self.display = json.get_bool("Display")

        # self.tot_fincl_commit = json.get_int("TotFinclCommit")
        # self.tot_prize_money = json.get_int("TotPrizeMoney")

        # self.show_partner_column = json.get_bool("ShowPartnerColumn")
        # self.partner_cms_item_name = json.get_str("PartnerCmsItemName")
        # self.partner_first_name = json.get_NoneType("PartnerFirstName")
        # self.partner_last_name = json.get_NoneType("PartnerLastName")
        # self.partner_natl_id = json.get_NoneType("PartnerNatlId")
        # self.partner_rank = json.get_NoneType("PartnerRank")


# MARK: Match


@dataclass
class PlayerMatch_Round:
    id: str
    name: str


@dataclass
class PlayerMatch_Opponent:
    id: str
    rank: int
    name_first: str | None
    name_first_initial: str
    name_last: str


@dataclass
class PlayerMatch_Set:
    player: int
    opponent: int
    tie_break: int | None


PlayerMatch_PrematureEndReason = Literal["Walkover", "Retire", "Default", "Unplayed"]


@dataclass
class _PlayerMatch_Base:
    id: str
    date: str
    round: PlayerMatch_Round
    win_loss: Literal["W", "L"]
    is_title_countable: bool
    is_win_loss_countable: bool


@dataclass
class PlayerMatch_Played(_PlayerMatch_Base):
    "Match that finished normally."
    opponent: PlayerMatch_Opponent
    sets: list[PlayerMatch_Set]


class PlayerMatch_Bye(_PlayerMatch_Base):
    "Player did not have to play this round."


class PlayerMatch_NotPlayed(_PlayerMatch_Base):
    "Before a match: other reason."


@dataclass
class PlayerMatch_Walkover(_PlayerMatch_Base):
    "Before a match: ill, injured or subjected to penalties of the Code of Conduct."
    opponent: PlayerMatch_Opponent


@dataclass
class PlayerMatch_Retire(_PlayerMatch_Base):
    "During a match: ill or injured."
    opponent: PlayerMatch_Opponent
    sets: list[PlayerMatch_Set]


@dataclass
class PlayerMatch_Default(_PlayerMatch_Base):
    "During a match: Code of Conduct violation."
    opponent: PlayerMatch_Opponent
    sets: list[PlayerMatch_Set]


PlayerMatch = (
    PlayerMatch_Played
    | PlayerMatch_Walkover
    | PlayerMatch_Retire
    | PlayerMatch_Default
    # ---------------
    | PlayerMatch_Bye
    | PlayerMatch_NotPlayed
)


# MARK: Get


def get_players_tournaments(
    player_ids: list[str],
) -> dict[str, list[PlayerTournament]]:
    """
    Activity - all of the tournaments played
    https://www.atptour.com/en/-/www/activity/sgl/s0ag/?v=1
    """

    player_id_urls, urls = create_urls(
        player_ids,
        "https://www.atptour.com/en/-/www/activity/sgl/{id}/?v=1",
    )

    url_to_stats = get_json_or_none(urls, CACHE_PATH)
    result = dict[str, list[PlayerTournament]]()

    for p in player_id_urls:
        json = url_to_stats[p.url]

        tournaments = list[PlayerTournament]()
        result[p.id] = tournaments

        if json is None:
            result[p.id] = []
            continue

        activity_json_list = json.get_list("Activity")

        for a in activity_json_list:
            assert isinstance(a, dict)
            a_json = JSONDict(a)
            tournaments_json_list = a_json.get_list("Tournaments")

            for t in tournaments_json_list:
                assert isinstance(t, dict)
                t_dict = JSONDict(t)
                tournament = PlayerTournament(t_dict)
                tournaments.append(tournament)

        tournaments.sort(key=lambda t: (t.date, t.date_end, t.name))

    return result


# MARK: Get type


def _get_tournament_type(name: str, type: str) -> PlayerTournament.Type:
    if type == "GS":
        assert name in (
            "US Open",
            "Wimbledon",
            "Roland Garros",
            "Australian Open",
        )
        return "Grand slam"

    if type == "CH":
        return "Challenger"

    if type == "WC":
        assert "ATP Finals" in name or name == "Tennis Masters Cup"
        return "ATP Finals"

    if type == "XXI":
        assert "Next Gen ATP Finals" in name
        return "Next Gen ATP Finals"

    if type == "OL":
        assert "Olympics" in name
        return "Olympics"

    if type == "DC":
        # 'name' can me multiple things
        return "Davis Cup"

    if type == "ATPC":
        assert name == "ATP Cup"
        return "ATP Cup"

    if type == "LVR":
        assert name == "Laver Cup"
        return "Laver Cup"

    if type == "UC":
        assert name == "United Cup"
        return "United Cup"

    assert type in (
        "1000",
        "500",
        "250",
        "Q",
        "CS",
        "WS",
        "FU",
        "PZ",
    ), f"Unknown event type: {type}"

    return type


# MARK: Get match


class _PlayerMatchParse:

    def __init__(self, json: "JSONDict") -> None:
        self.id = json.get_str("MatchId")
        self.date = json.get_str("MatchDate")

        # self.has_stats = json.get_bool("HasStats")
        # self.stats_url = json.get_str("MatchStatsUrl")

        win_loss = json.get_str("WinLoss")
        assert win_loss in ("W", "L")
        self.win_loss: Literal["W", "L"] = win_loss

        round = json.get_dict("Round")
        round_short = round.get_str("ShortName")
        round_long = round.get_str("LongName")
        self.round = PlayerMatch_Round(round_short, round_long)

        self.is_bye = json.get_bool("IsBye")
        self.is_title_countable = json.get_bool("IsTitleCountable")
        self.is_win_loss_countable = json.get_bool("IsWinLossCountable")

        opponent_id = json.get_str("OpponentId").lower()
        opponent_rank = json.get_int("OpponentRank")
        opponent_name_first = json.get_str_or_none("OpponentFirstName")
        opponent_name_first_initial = json.get_str("OpponentFirstInitial")
        opponent_name_last = json.get_str("OpponentLastName")
        # self.opponent_cms_item_name = json.get_str("OpponentCmsItemName")
        # self.opponent_natl_id = json.get_str("OpponentNatlId")
        self.opponent = PlayerMatch_Opponent(
            opponent_id,
            opponent_rank,
            opponent_name_first,
            opponent_name_first_initial,
            opponent_name_last,
        )

        self.sets = list[PlayerMatch_Set]()

        # 7 sets just to be sure
        for n in (1, 2, 3, 4, 5, 6, 7):
            set_player = json.get_int_or_none(f"Set{n}Player")
            set_opponent = json.get_int_or_none(f"Set{n}Opponent")

            if set_player is None or set_opponent is None:
                break

            set_tie = json.get_int_or_none(f"Set{n}Tie")
            self.sets.append(PlayerMatch_Set(set_player, set_opponent, set_tie))

        reason = json.get_str_or_none("Reason")
        self.premature_end_reason: PlayerMatch_PrematureEndReason | None = None

        if reason == "W/O":
            self.premature_end_reason = "Walkover"
        elif reason == "RET":
            # Retire
            # https://www.atptour.com/en/scores/match-stats/archive/2024/540/ms009
            # https://www.atptour.com/en/news/medvedev-dimitrov-wimbledon-2024-sunday
            self.premature_end_reason = "Retire"
        elif reason == "DEF":
            # Default -> Win
            # https://www.atptour.com/en/scores/match-stats/archive/2024/418/ms007
            self.premature_end_reason = "Default"
        elif reason == "UNP":
            # Unplayed
            # https://www.atptour.com/en/scores/match-stats/archive/2023/6239/qs027
            # Giovanni Mpetshi Perricard
            # Quimper, France | 23 Jan, 23 | Hard
            # Alternate (0) UNP (UNP)
            self.premature_end_reason = "Unplayed"
        else:
            assert reason is None, f"Unknown reason: {reason}"

        # Singles only
        assert json.get_str_or_none("PartnerId") is None
        assert json.get_str_or_none("PartnerRank") is None
        assert json.get_str_or_none("PartnerFirstName") is None
        assert json.get_str_or_none("PartnerLastName") is None
        assert json.get_str_or_none("PartnerNatlId") is None
        assert json.get_str_or_none("PartnerCmsItemName") in ("-", None)

        assert json.get_int_or_none("OpponentPartnerRank") == 0
        assert json.get_str_or_none("OpponentPartnerFirstInitial") in ("", None)
        assert json.get_str_or_none("OpponentPartnerCmsItemName") in ("-", None)


def _get_match(json: JSONDict) -> PlayerMatch:
    p = _PlayerMatchParse(json)

    if p.is_bye:
        return PlayerMatch_Bye(
            id=p.id,
            date=p.date,
            win_loss=p.win_loss,
            round=p.round,
            is_title_countable=p.is_title_countable,
            is_win_loss_countable=p.is_win_loss_countable,
        )

    if p.premature_end_reason == "Unplayed":
        return PlayerMatch_NotPlayed(
            id=p.id,
            date=p.date,
            win_loss=p.win_loss,
            round=p.round,
            is_title_countable=p.is_title_countable,
            is_win_loss_countable=p.is_win_loss_countable,
        )

    if p.premature_end_reason == "Walkover":
        assert not p.sets
        return PlayerMatch_Walkover(
            id=p.id,
            date=p.date,
            win_loss=p.win_loss,
            round=p.round,
            is_title_countable=p.is_title_countable,
            is_win_loss_countable=p.is_win_loss_countable,
            opponent=p.opponent,
        )

    if p.premature_end_reason == "Retire":
        return PlayerMatch_Retire(
            id=p.id,
            date=p.date,
            win_loss=p.win_loss,
            round=p.round,
            is_title_countable=p.is_title_countable,
            is_win_loss_countable=p.is_win_loss_countable,
            opponent=p.opponent,
            sets=p.sets,
        )

    if p.premature_end_reason == "Default":
        return PlayerMatch_Default(
            id=p.id,
            date=p.date,
            win_loss=p.win_loss,
            round=p.round,
            is_title_countable=p.is_title_countable,
            is_win_loss_countable=p.is_win_loss_countable,
            opponent=p.opponent,
            sets=p.sets,
        )

    if p.premature_end_reason is None:
        return PlayerMatch_Played(
            id=p.id,
            date=p.date,
            win_loss=p.win_loss,
            round=p.round,
            is_title_countable=p.is_title_countable,
            is_win_loss_countable=p.is_win_loss_countable,
            opponent=p.opponent,
            sets=p.sets,
        )

    assert_never(p.premature_end_reason)
