import os
import csv
import json
from typing import Any
from dataclasses import dataclass


@dataclass
class Continent:
    id: str
    name: str


@dataclass
class Country:
    name: str
    alpha2: str
    alpha3: str
    ioc_code: str
    continent: Continent
    flag_emoji: str


@dataclass
class _Cache:
    countries: list[Country]
    continents: list[Continent]
    alpha2_to_country: dict[str, Country]
    alpha3_to_country: dict[str, Country]
    ioc_code_to_country: dict[str, Country]


def get_all_countries() -> list[Country]:
    data = _read_data()
    return data.countries


def get_all_continents() -> list[Continent]:
    data = _read_data()
    return data.continents


def get_country_by_ioc_code(code: str) -> Country:
    "Get country by International Olympic Committee code."
    data = _read_data()
    return data.ioc_code_to_country[code]


# MARK: Cache

_DATA_CACHE: _Cache | None = None


def _read_data() -> _Cache:
    global _DATA_CACHE

    if _DATA_CACHE is not None:
        return _DATA_CACHE

    continents = _read_continents()
    alpha2_to_alpha3 = _read_alpha2_to_alpha3()
    alpha2_to_ioc_code = _read_alpha2_to_ioc_code()
    alpha2_to_emoji_flag = _read_alpha2_to_emoji_flag()
    countries = _read_countries(
        continents,
        alpha2_to_alpha3,
        alpha2_to_ioc_code,
        alpha2_to_emoji_flag,
    )

    _DATA_CACHE = _Cache(countries, continents, {}, {}, {})

    for c in countries:
        _DATA_CACHE.alpha2_to_country[c.alpha2] = c
        _DATA_CACHE.alpha3_to_country[c.alpha3] = c
        _DATA_CACHE.ioc_code_to_country[c.ioc_code] = c

    return _DATA_CACHE


# MARK: Read


def _read_continents() -> list[Continent]:
    result = list[Continent]()
    json = _read_json("continents.min.json")
    assert isinstance(json, dict)

    for id, name in json.items():
        result.append(Continent(id, name))

    return result


def _read_alpha2_to_alpha3() -> dict[str, str]:
    result = dict[str, str]()
    json = _read_json("countries.2to3.min.json")
    assert isinstance(json, dict)

    for alpha2, flag in json.items():
        result[alpha2] = flag

    return result


def _read_alpha2_to_emoji_flag() -> dict[str, str]:
    result = dict[str, str]()
    json = _read_json("countries.emoji.min.json")
    assert isinstance(json, dict)

    for alpha2, flag in json.items():
        result[alpha2] = flag

    # Remove Russia flag
    result["RU"] = "⬜"
    return result


def _read_alpha2_to_ioc_code():
    "https://www.worlddata.info/countrycodes.php"
    result = dict[str, str]()
    path = _get_file_path("ioc.csv")

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            # Country
            # alpha2 - ISO 3166-1
            # alpha3 - ISO 3166-1
            # numeric - ISO 3166-1
            # IOC
            # Fips 10
            # License Plate
            # Domain
            alpha2 = row[1]
            ioc_code = row[4]
            result[alpha2] = ioc_code

    return result


def _read_countries(
    continents: list[Continent],
    alpha2_to_alpha3: dict[str, str],
    alpha2_to_ioc_code: dict[str, str],
    alpha2_to_emoji_flag: dict[str, str],
) -> list[Country]:
    result = list[Country]()
    id_to_continent = {c.id: c for c in continents}
    json = _read_json("countries.min.json")
    assert isinstance(json, dict)

    for alpha2, data in json.items():
        assert isinstance(data, dict)

        name = data["name"]
        alpha3 = alpha2_to_alpha3[alpha2]
        ioc_code = alpha2_to_ioc_code[alpha2]
        continent_id = data["continent"]
        continent = id_to_continent[continent_id]
        flag = alpha2_to_emoji_flag[alpha2]
        result.append(Country(name, alpha2, alpha3, ioc_code, continent, flag))

    return result


def _read_json(name: str) -> Any:
    path = _get_file_path(name)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_file_path(name: str) -> str:
    dir_path = os.path.dirname(__file__)
    return os.path.join(dir_path, name)
