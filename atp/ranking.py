from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass
from browser import get_html_browser
from atp.helpers import REQUEST_INTERVAL_SECONDS

CACHE_PATH = "atp_cache/atp_ranking"


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
        cache_path=CACHE_PATH,
        delay=REQUEST_INTERVAL_SECONDS,
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
        id: str = link_no_overview[id_start_index:].lstrip("/").lower()

        p = PlayerRow(id, rank, name, link)
        result.append(p)

    return result
