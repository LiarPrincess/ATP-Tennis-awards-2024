from typing import Literal
from dataclasses import dataclass
from atp_api.json_dict import JSONDict
from atp_api.helpers import create_urls, get_json

CACHE_PATH = "cache/atp_player_data"


# MARK: Player


class PlayerData:

    @property
    def can_receive_award(self) -> bool:
        # That could be awkward or downright hurtful.
        if self.active == "Deceased":
            return False

        return True

    def __init__(self, id: str, json: JSONDict) -> None:
        self.id = id.lower()

        self.name_first = json.get_str("FirstName")
        self.name_last = json.get_str("LastName")
        self.name_mid = json.get_str_or_none("MidInitial")
        # self.name_pronunciation = json.get_str_or_none("Pronunciation")

        self.age = json.get_int_or_none("Age")
        self.birth_date = json.get_str("BirthDate")

        nationality_id = json.get_str("NatlId")
        self.nationality = _NATIONALITY_ID_TO_NATIONALITY[nationality_id]
        # self.nationality = json.get_str("Nationality")
        # self.nationality_birth_city = json.get_str_or_none("BirthCity")
        self.nationality_residence = json.get_str_or_none("Residence")

        # self.height_ft = json.get_str("HeightFt")
        # self.height_in = json.get_int("HeightIn")
        self.height_cm = json.get_int("HeightCm")

        # self.weight_lb = json.get_int("WeightLb")
        self.weight_kg = json.get_int("WeightKg")

        play_hand = json.get_dict("PlayHand")
        play_hand_id = play_hand.get_str("Id")
        assert play_hand_id in ("L", "R")
        self.hand_play: Literal["L", "R"] = play_hand_id

        back_hand = json.get_dict("BackHand")
        back_hand_id = back_hand.get_str("Id")
        assert back_hand_id in ("1", "2")
        self.hand_back: Literal["1", "2"] = back_hand_id

        active = json.get_dict("Active")
        active_description = active.get_str("Description")
        assert active_description in ("Active", "Deceased")
        self.active: Literal["Active", "Deceased"] = active_description

        self.pro_year = json.get_int_or_none("ProYear")
        # self.coach = json.get_str_or_none("Coach")

        self.rank = json.get_int_or_none("SglRank")
        # self.rank_highest = json.get_int("SglHiRank")
        # self.rank_highest_date = json.get_str("SglHiRankDate")
        self.rank_is_tie = json.get_bool("SglRankTie")
        # self.rank_move = json.get_int("SglRankMove")

        self.ytd_won = json.get_int("SglYtdWon")
        self.ytd_lost = json.get_int("SglYtdLost")
        self.ytd_titles = json.get_int("SglYtdTitles")
        self.ytd_prize_formatted = json.get_str("SglYtdPrizeFormatted")

        self.career_won = json.get_int("SglCareerWon")
        self.career_lost = json.get_int("SglCareerLost")
        self.career_titles = json.get_int("SglCareerTitles")
        self.career_prize_formatted = json.get_str("CareerPrizeFormatted")

        # self.dbl_is_specialist = json.get_bool("DblSpecialist")
        # self.dbl_rank = json.get_int_or_none("DblRank")
        # self.dbl_rank_highest = json.get_int_or_none("DblHiRank")
        # self.dbl_rank_highest_date = json.get_str("DblHiRankDate")
        # self.dbl_rank_move = json.get_int("DblRankMove")
        # self.dbl_rank_is_tie = json.get_bool("DblRankTie")
        # self.dbl_ytd_won = json.get_int("DblYtdWon")
        # self.dbl_ytd_lost = json.get_int("DblYtdLost")
        # self.dbl_ytd_titles = json.get_int("DblYtdTitles")
        # self.dbl_ytd_prize_formatted = json.get_str("DblYtdPrizeFormatted")
        # self.dbl_career_lost = json.get_int("DblCareerLost")
        # self.dbl_career_won = json.get_int("DblCareerWon")
        # self.dbl_career_titles = json.get_int("DblCareerTitles")

        # self.scRelativeUrlPlayerProfile = json.get_str("ScRelativeUrlPlayerProfile")
        # self.scRelativeUrlPlayerCountryFlag = json.get_str("ScRelativeUrlPlayerCountryFlag")
        # self.gladiatorImageUrl = json.get_NoneType("GladiatorImageUrl")
        # self.isCarbonTrackerEnabled = json.get_bool("IsCarbonTrackerEnabled")
        # self.socialLinks = json.get_list("SocialLinks")
        # self.cacheTags = json.get_NoneType("CacheTags")
        # self.topCourtLink = json.get_str("TopCourtLink")


# MARK: Get


def get_players_data_json(player_ids: list[str]) -> dict[str, JSONDict]:
    """
    Main data
    https://www.atptour.com/en/-/www/players/hero/s0ag?v=1
    """

    player_id_urls, urls = create_urls(
        player_ids,
        "https://www.atptour.com/en/-/www/players/hero/{id}?v=1",
    )

    url_to_stats = get_json(urls, CACHE_PATH)
    result = dict[str, JSONDict]()

    for p in player_id_urls:
        json = url_to_stats[p.url]
        result[p.id] = json

    return result


# MARK: Nationality


@dataclass
class PlayerNationality:
    id: str
    name: str
    emoji: str


_NATIONALITY_ID_TO_NATIONALITY: dict[str, PlayerNationality] = {
    "ARG": PlayerNationality("ARG", "Argentina", "🇦🇷"),
    "AUS": PlayerNationality("AUS", "Australia", "🇦🇺"),
    "AUT": PlayerNationality("AUT", "Austria", "🇦🇹"),
    "BEL": PlayerNationality("BEL", "Belgium", "🇧🇪"),
    "BRA": PlayerNationality("BRA", "Brazil", "🇧🇷"),
    "BUL": PlayerNationality("BUL", "Bulgaria", "🇧🇬"),
    "CAN": PlayerNationality("CAN", "Canada", "🇨🇦"),
    "CHI": PlayerNationality("CHI", "Chile", "🇨🇱"),
    "CHN": PlayerNationality("CHN", "China", "🇨🇳"),
    "COL": PlayerNationality("COL", "Colombia", "🇨🇴"),
    "CRO": PlayerNationality("CRO", "Croatia", "🇭🇷"),
    "CZE": PlayerNationality("CZE", "Czechia", "🇨🇿"),
    "DEN": PlayerNationality("DEN", "Denmark", "🇩🇰"),
    "ESP": PlayerNationality("ESP", "Spain", "🇪🇸"),
    "FIN": PlayerNationality("FIN", "Finland", "🇫🇮"),
    "FRA": PlayerNationality("FRA", "France", "🇫🇷"),
    "GBR": PlayerNationality("GBR", "Great Britain", "🇬🇧"),  # ?
    "GER": PlayerNationality("GER", "Germany", "🇩🇪"),
    "GRE": PlayerNationality("GRE", "Greece", "🇬🇷"),
    "HUN": PlayerNationality("HUN", "Hungary", "🇭🇺"),
    "IND": PlayerNationality("IND", "India", "🇮🇳"),
    "ITA": PlayerNationality("ITA", "Italy", "🇮🇹"),
    "JPN": PlayerNationality("JPN", "Japan", "🇯🇵"),
    "KAZ": PlayerNationality("KAZ", "Kazakhstan", "🇰🇿"),
    "NED": PlayerNationality("NED", "Netherlands", "🇳🇱"),
    "NOR": PlayerNationality("NOR", "Norway", "🇳🇴"),
    "PER": PlayerNationality("PER", "Peru", "🇵🇪"),
    "POL": PlayerNationality("POL", "Poland", "🇵🇱"),
    "POR": PlayerNationality("POR", "Portugal", "🇵🇹"),
    "RUS": PlayerNationality("RUS", "Russia", "⬜"),
    "SRB": PlayerNationality("SRB", "Serbia", "🇷🇸"),
    "SUI": PlayerNationality("SRB", "Switzerland", "🇨🇭"),
    "USA": PlayerNationality("USA", "United States", "🇺🇸"),
}
