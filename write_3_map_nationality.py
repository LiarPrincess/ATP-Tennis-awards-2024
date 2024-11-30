from typing import Iterable
from dataclasses import dataclass
from page import Page, Award, Table
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


def write_map_nationality(
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


    _write_award_for_best_tally(
        page,
        countries,
        award_count_best_countries,
    )

    _write_awards_for_best_in_continent(
        page,
        players,
        award_count_best_player_per_continent,
    )


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
