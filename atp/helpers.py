import json
from typing import Iterable
from dataclasses import dataclass
from browser import get_htmls_browser
from atp.json_dict import JSONDict

REQUEST_INTERVAL_SECONDS = 5


@dataclass
class PlayerIdURL:
    id: str
    url: str


def create_urls(
    player_ids: list[str],
    url_template: str,
) -> tuple[list[PlayerIdURL], list[str]]:
    player_id_urls = [PlayerIdURL(id, url_template.format(id=id)) for id in player_ids]
    urls = [p.url for p in player_id_urls]
    return (player_id_urls, urls)


def get_json(urls: Iterable[str], cache_path: str | None) -> dict[str, JSONDict]:
    urls = list(urls)
    result = dict[str, JSONDict]()
    raw = get_json_or_none(urls, cache_path)

    for url in urls:
        data = raw[url]
        assert data is not None, f"Missing {url}"
        result[url] = data

    return result


def get_json_or_none(
    urls: Iterable[str],
    cache_path: str | None,
) -> dict[str, JSONDict | None]:
    # Simple requests would be blocked by Cloudflare.
    # But they can't block the whole browser.
    urls = list(urls)

    url_to_html = get_htmls_browser(
        urls,
        cache_path=cache_path,
        delay=REQUEST_INTERVAL_SECONDS,
    )

    result = dict[str, JSONDict | None]()

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
