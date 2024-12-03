from typing import Iterable
from dataclasses import dataclass
from page import Page, Subtitle, Award, Table, Map, MapData
from atp_api import (
    Country,
    Continent,
    Player,
    get_all_countries,
    get_all_continents,
)
from helpers import *


@dataclass
class CountryPlayers:
    country: Country
    players: list[Player]

    @property
    def players_len(self) -> int:
        return len(self.players)


@dataclass
class ContinentPlayers:
    continent: Continent
    players: list[Player]

    @property
    def players_len(self) -> int:
        return len(self.players)


def write_map(
    page: Page,
    players: list[Player],
    award_count_best_countries: int,
    award_count_best_player_per_continent: int,
):
    # MARK: Data

    countries = list[CountryPlayers]()
    continents = list[ContinentPlayers]()

    id_to_country = {id(c): c for c in get_all_countries()}
    id_to_continent = {id(c): c for c in get_all_continents()}

    for c_id, group in groupby(players, key=lambda p: id(p.nationality)):
        c = id_to_country[c_id]
        countries.append(CountryPlayers(c, group))

    for c_id, group in groupby(players, key=lambda p: id(p.nationality.continent)):
        c = id_to_continent[c_id]
        continents.append(ContinentPlayers(c, group))

    countries.sort(key=lambda c: c.players_len, reverse=True)
    continents.sort(key=lambda c: c.players_len, reverse=True)

    page.add(Subtitle(f"Number of players per country"))
    _write_map(page, countries)

    _write_award_for_best_tally(
        page,
        countries,
        award_count_best_countries,
    )

    page.add(Subtitle(f"Number of players per continent"))

    _write_continent_count_table(page, continents)

    _write_awards_for_best_in_continent(
        page,
        players,
        award_count_best_player_per_continent,
    )


# MARK: Map


def _write_map(page: Page, countries: list[CountryPlayers]):
    map = Map()
    map.set_aspect_rato(1400, 550)
    map.set_latitude_range(-60, 90)  # Cut Antarctica
    page.add(map)

    data = MapData("map/ne_110m_admin_0_countries.shp")
    data.calculate_centroid("CENTROID")

    alpha3_to_country = {c.country.alpha3.lower(): c for c in countries}
    alpha3_to_label_adjustment = {
        "fra": (10, 4),
        "nor": (-5, -5),
        "usa": (0, -5),
        "can": (-10, -3),
        "chl": (-5, 0),
        "chn": (-2, -3),
        "aus": (3, -2),
    }

    for row in data.iter_rows():
        alpha3: str = row["ADM0_A3"].lower()
        country = alpha3_to_country.pop(alpha3, None)

        players_len = country.players_len if country else 0
        row["VALUE"] = players_len

        if players_len != 0:
            centroid = row["CENTROID"]
            x, y = centroid.coords[0]
            dx, dy = alpha3_to_label_adjustment.get(alpha3, (0, 0))
            x = x + dx
            y = y + dy
            map.annotate(x, y, str(players_len))

    assert not alpha3_to_country, f"Unable to map country to shape: {alpha3_to_country}"

    players_len_max = max(c.players_len for c in countries)
    map.add_data(data, value_min=0, value_max=players_len_max)


# MARK: Table


def _write_continent_count_table(page: Page, continents: list[ContinentPlayers]):
    table = Table()
    table.headers.append(Table.Header("Name"))
    table.headers.append(Table.Header("Count"))
    page.add(table)

    continents = sorted(continents, key=lambda c: (-c.players_len, c.continent.name))

    for c in continents:
        continent = c.continent
        name = continent.name
        row = Table.Row([name, c.players_len])
        table.rows.append(row)


# MARK: Awards


def _write_award_for_best_tally(
    page: Page,
    countries: list[CountryPlayers],
    award_count: int,
):
    #  🇮🇹 Italy award for the best tally.
    award_rows = filter_award_max_NO_can_receive_award_check(
        countries,
        count=award_count,
        key=lambda c: c.players_len,
    )

    page.add(Award("🇮🇹", "Italy award for the best tally."))

    table = Table()
    table.headers.append(Table.Header("Country"))
    table.headers.append(Table.Header("Count"))
    table.headers.append(Table.Header("Players", is_player_column=True))
    page.add(table)

    for c in award_rows:
        country = c.country
        name = f"{country.flag_emoji} {country.name}"
        ps = "\\n".join(to_str_player(p) for p in c.players)
        row = Table.Row([name, c.players_len, ps])
        table.rows.append(row)


def _write_awards_for_best_in_continent(
    page: Page,
    players: list[Player],
    award_count: int,
):
    #  🐦 Unladen swallow award for the best player from Europe
    #  🦅 Turkey award for the best player from North America
    #  🐲 Dragon award for the best player from Asia
    #  🦤 Dodo award for the best player not from the above

    def add_award(emoji: str, text: str, players: Iterable[Player]):
        table = Table()
        table.headers.append(Table.Header("Player", is_player_column=True))
        table.headers.append(Table.Header("Age"))
        table.headers.append(Table.Header("Country"))
        table.headers.append(Table.Header("Birthplace"))
        table.headers.append(Table.Header("Residence"))

        award_players = filter_award_min_NO_can_receive_award_check(
            (p for p in players if p.can_receive_award),
            award_count,
            key=lambda p: p.rank,
        )

        for p in award_players:
            assert p.age
            country = p.nationality.name
            city = p.nationality_birth_city
            residence = p.nationality_residence
            row = Table.Row([p, p.age, country, city, residence])
            table.rows.append(row)

        if award_players:
            page.add(Award(emoji, text))
            page.add(table)

    add_award(
        "🐦",
        "Unladen swallow award for the best player from Europe.",
        (p for p in players if p.nationality.continent.id == "EU"),
    )
    add_award(
        "🦅",
        "Eagle award for the best player from North America.",
        (p for p in players if p.nationality.continent.id == "NA"),
    )
    add_award(
        "🐲",
        "Dragon award for the best player from Asia.",
        (p for p in players if p.nationality.continent.id == "AS"),
    )
    add_award(
        "🦤",
        "Dodo award for the best player not from the above.",
        (p for p in players if p.nationality.continent.id not in ("EU", "NA", "AS")),
    )
