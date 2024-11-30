import time
from cache import Cache
from playwright.sync_api import sync_playwright, ViewportSize

# pip install pytest-playwright
# PLAYWRIGHT_BROWSERS_PATH="/mnt/Storage/Programming/DEPRECIATED/tennis_stats/playwright" playwright install chromium


def get_html_browser(
    url: str,
    *,
    cache_path: str | None,
    delay: int | None,
) -> str:
    urls = [url]
    d = get_htmls_browser(urls, cache_path=cache_path, delay=delay)
    return d[url]


def get_htmls_browser(
    urls: list[str],
    *,
    cache_path: str | None,
    delay: int | None,
) -> dict[str, str]:
    cache = Cache(cache_path) if cache_path else None
    not_cached_urls = list[str]()
    result = dict[str, str]()

    for url in urls:
        if cache is not None:
            cached = cache.get(url)

            if cached is not None:
                result[url] = cached
            else:
                not_cached_urls.append(url)

    if not not_cached_urls:
        return result

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport=ViewportSize(width=1920, height=1080))
        url_len = len(urls)

        for index, url in enumerate(not_cached_urls):
            if index != 0 and delay is not None:
                time.sleep(delay)

            print(f"{index+1}/{url_len} {url}")
            page.goto(url)
            html = page.content()
            result[url] = html

            if cache is not None:
                cache.put(url, html)

        browser.close()

    return result
