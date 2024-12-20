from dataclasses import dataclass
from atp import (
    Player,
    Country,
    Continent,
    get_all_countries,
    get_all_continents,
)
from chart import Map, MapData
from helpers import *


@dataclass
class Page:

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

    map_chart: Map
    country_awards_rows: list[CountryPlayers]
    continent_count_rows: list[ContinentPlayers]
    continent_awards_europe: list[Player]
    continent_awards_north_america: list[Player]
    continent_awards_asia: list[Player]
    continent_awards_south_america: list[Player]
    continent_awards_oceania: list[Player]


def page4_map(
    players: list[Player],
    award_count_best_countries: int,
    award_count_best_player_per_continent: int,
) -> Page:
    # Data
    countries_pairs = group_by_key_id(players, lambda p: p.nationality)
    countries = list(Page.CountryPlayers(c, ps) for c, ps in countries_pairs)
    countries.sort(key=lambda c: c.players_len, reverse=True)

    continents_pairs = group_by_key_id(players, lambda p: p.nationality.continent)
    continents = list(Page.ContinentPlayers(c, ps) for c, ps in continents_pairs)
    continents.sort(key=lambda c: c.players_len, reverse=True)

    # Map
    map_chart = _create_map(countries)

    # Country
    country_awards_rows = filter_award_max_NO_can_receive_award_check(
        countries,
        count=award_count_best_countries,
        key=lambda c: c.players_len,
    )

    # Continent awards
    def continent_best(filter: Callable[[Continent], bool]):
        return filter_award_min_NO_can_receive_award_check(
            (
                p
                for p in players
                if p.can_receive_award and filter(p.nationality.continent)
            ),
            award_count_best_player_per_continent,
            key=lambda p: p.rank,
        )

    continent_awards_europe = continent_best(lambda c: c.id == "EU")
    continent_awards_north_america = continent_best(lambda c: c.id == "NA")
    continent_awards_asia = continent_best(lambda c: c.id == "AS")
    continent_awards_south_america = continent_best(lambda c: c.id == "SA")
    continent_awards_oceania = continent_best(lambda c: c.id == "OC")

    for p in players:
        c = p.nationality.continent
        assert c.id in ("EU", "NA", "AS", "SA", "OC")

    return Page(
        map_chart=map_chart,
        country_awards_rows=country_awards_rows,
        continent_count_rows=continents,
        continent_awards_europe=continent_awards_europe,
        continent_awards_north_america=continent_awards_north_america,
        continent_awards_asia=continent_awards_asia,
        continent_awards_south_america=continent_awards_south_america,
        continent_awards_oceania=continent_awards_oceania,
    )


def _create_map(countries: list[Page.CountryPlayers]) -> Map:
    map = Map()
    map.set_aspect_rato(1400, 550)
    map.set_latitude_range(-60, 90)  # Cut Antarctica

    data = MapData("assets/ne_110m_admin_0_countries.shp")
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
            x += dx
            y += dy
            map.annotate(x, y, str(players_len))

    assert not alpha3_to_country, f"Unable to map country to shape: {alpha3_to_country}"

    map.add_data(data, column_name="VALUE")
    return map
