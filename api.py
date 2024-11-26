import sys
import json
from bs4 import BeautifulSoup, Tag
from typing import Any, Literal, Iterable, assert_never
from dataclasses import dataclass
from browser import get_html_browser, get_htmls_browser


_REQUEST_INTERVAL_SECONDS = 5
_CACHE_PATH_ATP_RANKING = "cache/atp_ranking"
_CACHE_PATH_ATP_PLAYER = "cache/atp_player"
_CACHE_PATH_ATP_PLAYER_STATS = "cache/atp_player_stats"
_CACHE_PATH_ATP_PLAYER_ACTIVITY = "cache/atp_player_activity"
_CACHE_PATH_ATP_PLAYER_RANK_HISTORY = "cache/atp_player_rank_history"

# MARK: Ranking


@dataclass
class PlayerRow:
    id: str
    rank: int
    name: str
    url: str


def get_ranking_top_100() -> list[PlayerRow]:
    url = "https://www.atptour.com/en/rankings/singles"
    return _get_ranking(url)


def get_ranking_top_100_for_date(date: str):
    "Take date from ATP website, for example: 2024-01-01."
    url = f"https://www.atptour.com/en/rankings/singles?dateWeek={date}"
    return _get_ranking(url)


def _get_ranking(url: str) -> list[PlayerRow]:
    html = get_html_browser(
        url,
        cache_path=_CACHE_PATH_ATP_RANKING,
        delay=_REQUEST_INTERVAL_SECONDS,
    )
    soup = BeautifulSoup(html, "html.parser")

    # <table class="mega-table desktop-table non-live">
    table_tag = soup.find("table", class_=f"mega-table")
    assert isinstance(table_tag, Tag)

    # <tr class="">
    #     <td class="rank bold heavy tiny-cell" colspan="1">1</td>
    #     <td class="player bold heavy large-cell" colspan="7">
    #         <ul class="player-stats">
    #             <li class="rank">
    #             </li>
    #             <li class="avatar">
    #                 <img class="headShot " src="/-/media/alias/player-headshot/s0ag" alt="headshot-1" title="Headshot">
    #                 <svg class="atp-flag atp-flag--tiny flag ">
    #                     <use href="/assets/atptour/assets/flags.svg#flag-ita"></use>
    #                 </svg>
    #             </li>
    #             <li class="name center">
    #                 <a href="/en/players/jannik-sinner/s0ag/overview">
    #                     <span>Jannik Sinner</span>
    #                 </a>
    #             </li>
    #         </ul>
    #     </td>
    #     <td class="age small-cell" colspan="2">23</td>
    #     <td class="points center bold extrabold small-cell" colspan="2">
    #         <a href="/en/players/jannik-sinner/s0ag/rankings-breakdown?team=singles">
    #             11,830
    #         </a>
    #     </td>
    #     <td class="small-cell pointsMove center positive" colspan="2">
    #         +1500 </td>
    #     <td class="tourns center small-cell" colspan="2">17</td>
    #     <td class="drop center small-cell" colspan="2">-</td>
    #     <td class="best center small-cell" colspan="2">-</td>
    # </tr>
    result = list[PlayerRow]()

    for row_tag in table_tag.find_all("tr"):
        assert isinstance(row_tag, Tag)

        name_tag = row_tag.find("li", class_="name")
        rank_tag = row_tag.find("td", class_="rank")

        # Not a player row
        if name_tag is None or rank_tag is None:
            continue

        assert isinstance(rank_tag, Tag)
        assert isinstance(name_tag, Tag)

        link_tag = name_tag.find("a")
        assert isinstance(link_tag, Tag)

        rank_str = rank_tag.get_text().strip()
        rank = int(rank_str)

        name = link_tag.get_text().strip()

        href = link_tag.attrs["href"]
        assert isinstance(href, str)

        # https://www.atptour.com/en/players/jannik-sinner/s0ag/overview
        link = "https://www.atptour.com" + href
        assert link.startswith("https://www.atptour.com/en/players/")
        assert link.endswith("/overview")

        # Extract 'id'
        overview_start_index = link.rindex("/")
        assert overview_start_index != -1
        link_no_overview = link[:overview_start_index]
        id_start_index = link_no_overview.rindex("/")
        assert id_start_index != -1
        id: str = link_no_overview[id_start_index:].lstrip("/")

        p = PlayerRow(id, rank, name, link)
        result.append(p)

    return result


# MARK: Player data

PlayerId = str


class Player:

    @property
    def can_receive_award(self) -> bool:
        # That could be awkward or downright hurtful.
        if self.active == "Deceased":
            return False

        return True

    def __init__(
        self,
        id: PlayerId,
        json: "JSONDict",
        stats_json: "JSONDict",
        activity_json: "JSONDict|None",
        rank_history_json: "JSONDict",
    ) -> None:
        self.id = id

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

        stats_json_inner = stats_json.get_dict("Stats")
        stats_json_service = stats_json_inner.get_dict("ServiceRecordStats")
        stats_json_return = stats_json_inner.get_dict("ReturnRecordStats")
        self.ytd_stats_service = PlayerService(stats_json_service)
        self.ytd_stats_return = PlayerReturn(stats_json_return)

        self.career_rank_history = list[PlayerRank]()
        self._date_to_rank = dict[str, PlayerRank]()
        rank_history_json_list = rank_history_json.get_list("History")

        for r in rank_history_json_list:
            assert isinstance(r, dict)
            r_json = JSONDict(r)
            e = PlayerRank(r_json)
            self.career_rank_history.append(e)
            self._date_to_rank[e.date] = e

        self.career_rank_history.sort(key=lambda r: r.date)

    def get_rank_at_date(self, date: str) -> "PlayerRank|Literal['Deceased']":
        if self.active == "Deceased":
            last_rank = self.career_rank_history[-1]
            if date > last_rank.date:
                return "Deceased"

        elif self.active == "Active":
            pass
        else:
            assert_never(self.active)

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


@dataclass
class PlayerNationality:
    id: str
    name: str
    emoji: str


class PlayerRank:
    def __init__(self, json: "JSONDict") -> None:
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


class PlayerService:
    def __init__(self, json: "JSONDict") -> None:
        self.aces = json.get_int("Aces")
        self.double_faults = json.get_int("DoubleFaults")

        self.first_serve_percentage = json.get_int("FirstServePercentage")
        self.first_serve_points_won_percentage = json.get_int(
            "FirstServePointsWonPercentage"
        )
        self.second_serve_points_won_percentage = json.get_int(
            "SecondServePointsWonPercentage"
        )

        self.break_points_faced = json.get_int("BreakPointsFaced")
        self.break_points_saved_percentage = json.get_int("BreakPointsSavedPercentage")

        self.service_games_played = json.get_int("ServiceGamesPlayed")
        self.service_games_won_percentage = json.get_int("ServiceGamesWonPercentage")
        self.service_points_won_percentage = json.get_int("ServicePointsWonPercentage")


class PlayerReturn:
    def __init__(self, json: "JSONDict") -> None:
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

        self.return_games_played = json.get_int("ReturnGamesPlayed")
        self.return_games_won_percentage = json.get_int("ReturnGamesWonPercentage")
        self.return_points_won_percentage = json.get_int("ReturnPointsWonPercentage")
        self.total_points_won_percentage = json.get_int("TotalPointsWonPercentage")


# MARK: Get player


def get_player(player_id: str) -> Player:
    player_ids = [player_id]
    players = get_players(player_ids)
    assert len(players) == 1
    return players[0]


def get_players(player_ids: list[PlayerId]) -> list[Player]:

    @dataclass
    class PlayerUrls:
        def __init__(self, id: PlayerId) -> None:
            self.id = id
            # Main data
            # https://www.atptour.com/en/-/www/players/hero/s0ag?v=1
            self.main_url = f"https://www.atptour.com/en/-/www/players/hero/{id}?v=1"
            # Stats - aces/breaks/returns/conversions
            # https://www.atptour.com/en/-/www/stats/s0ag/2024/all?v=1
            self.stats_url = f"https://www.atptour.com/en/-/www/stats/{id}/2024/all?v=1"
            # Activity - all of the tournaments played
            self.activity_url = (
                f"https://www.atptour.com/en/-/www/activity/sgl/{id}/?v=1"
            )
            # Rank - rank history
            # https://www.atptour.com/en/-/www/rank/history/s0ag?v=1
            self.rank_history_url = (
                f"https://www.atptour.com/en/-/www/rank/history/{id}?v=1"
            )

    urls = [PlayerUrls(id) for id in player_ids]
    url_to_main = _get_json(
        (u.main_url for u in urls),
        _CACHE_PATH_ATP_PLAYER,
    )
    url_to_stats = _get_json(
        (u.stats_url for u in urls),
        _CACHE_PATH_ATP_PLAYER_STATS,
    )
    url_to_activity = _get_json_or_none(
        (u.activity_url for u in urls),
        _CACHE_PATH_ATP_PLAYER_ACTIVITY,
    )
    url_to_rank_history = _get_json(
        (u.rank_history_url for u in urls),
        _CACHE_PATH_ATP_PLAYER_RANK_HISTORY,
    )

    result = list[Player]()

    for u in urls:
        id = u.id
        main = url_to_main[u.main_url]
        stats = url_to_stats[u.stats_url]
        activity = url_to_activity[u.activity_url]
        rank_history = url_to_rank_history[u.rank_history_url]

        # Generate Python code:
        # _dump_type("PlayerService", stats_service_json)

        p = Player(
            id=id,
            json=main,
            stats_json=stats,
            activity_json=activity,
            rank_history_json=rank_history,
        )
        result.append(p)

    return result


def _dump_type(name: str, d: "JSONDict|dict"):
    if isinstance(d, JSONDict):
        d = d.data

    print(f"class {name}:")
    print(f'    def __init__(self, json: "JSONDict") -> None:')

    for k, v in d.items():
        prop = _to_camel_case(k)
        v_type = type(v).__name__
        print(f'        self.{prop} = json.get_{v_type}("{k}")')

    sys.exit(0)


def _to_camel_case(s: str) -> str:
    result = ""

    for c in s:
        if result and c.isupper():
            result += "_"

        result += c

    return result.lower()


# MARK: Nationality


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

# MARK: JSON


class JSONDict:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    def get_str(self, key: str) -> str:
        v = self.data[key]
        assert isinstance(v, str), key
        return v

    def get_str_or_none(self, key: str) -> str | None:
        v = self.data[key]
        assert isinstance(v, str | None), key
        return v

    def get_int(self, key: str) -> int:
        v = self.data[key]
        assert isinstance(v, int), key
        return v

    def get_int_or_none(self, key: str) -> int | None:
        v = self.data[key]
        assert isinstance(v, int | None), key
        return v

    def get_bool(self, key: str) -> bool:
        v = self.data[key]
        assert isinstance(v, bool), key
        return v

    def get_list(self, key: str) -> list:
        v = self.data[key]
        assert isinstance(v, list), key
        return v

    def get_dict(self, key: str) -> "JSONDict":
        v = self.data[key]
        assert isinstance(v, dict), key
        return JSONDict(v)

    def get_dict_or_none(self, key: str) -> "JSONDict|None":
        v = self.data[key]
        assert isinstance(v, dict | None), key
        return JSONDict(v) if v is not None else None


URL = str


def _get_json(urls: Iterable[str], cache_path: str | None) -> dict[URL, JSONDict]:
    urls = list(urls)
    result = dict[URL, JSONDict]()
    raw = _get_json_or_none(urls, cache_path)

    for url in urls:
        data = raw[url]
        assert data is not None, f"Missing {url}"
        result[url] = data

    return result


def _get_json_or_none(
    urls: Iterable[str],
    cache_path: str | None,
) -> dict[URL, JSONDict | None]:
    # Simple requests would be blocked by Cloudflare.
    # But they can't block the whole browser.
    urls = list(urls)

    url_to_html = get_htmls_browser(
        urls,
        cache_path=cache_path,
        delay=_REQUEST_INTERVAL_SECONDS,
    )

    result = dict[URL, JSONDict | None]()

    for url in urls:
        html = url_to_html[url]

        # Extract JSON
        html_prefix = '<html><head><meta name="color-scheme" content="light dark"><meta charset="utf-8"></head><body><pre>'
        html_suffix = '</pre><div class="json-formatter-container"></div></body></html>'
        assert html.startswith(html_prefix)
        assert html.endswith(html_suffix)

        json_str = html[len(html_prefix) : -len(html_suffix)]

        if json_str == "null":
            result[url] = None
        else:
            json_dict: dict = json.loads(json_str)
            assert isinstance(json_dict, dict)
            result[url] = JSONDict(json_dict)

    return result
