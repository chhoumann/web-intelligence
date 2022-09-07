from random import random
from typing import Dict, Set, List
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
from datetime import datetime
from bs4 import BeautifulSoup
from time import sleep
import requests


def get_host(url: str) -> str:
    """
    Gets host from any URL.
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def get_page(url: str, timeout=1000) -> BeautifulSoup:
    """
    Get parsed page.
    """
    res = requests.get(url, timeout=timeout)
    visited_host(get_host(url))

    return BeautifulSoup(res.text, "html.parser")


def format_relative_url(href: str, host: str) -> str:
    """
    Turns a href from anchor tag into full url.
    """
    if href[0] == "/":
        return urljoin(host, href)

    return urlparse(href).geturl()


def filter_urls(urls: List[str]) -> List[str]:
    """
    Filter any URL that isn't using the HTTPS protocol.
    E.g. removing ssh:// and mailto://
    """
    return [url for url in urls if "https://" in url]


def extract_urls(parsed: BeautifulSoup, url: str) -> Set[str]:
    """
    Extract all URLs from anchor tags, ensure they are in the correct format, and filter.
    """
    all_anchor_tags = parsed.find_all("a")
    urls = [tag["href"] for tag in all_anchor_tags if tag.get("href", False)]
    formatted = [format_relative_url(href, url) for href in urls]

    print(
        f"<a>: {len(all_anchor_tags)} | URLs: {len(urls)} | Formatted: {len(formatted)}"
    )

    return filter_urls(formatted)


def visited_host(host: str):
    """
    Mark host as visited.
    """
    hosts[host] = datetime.now()


def get_can_visit_fn(timeout=1):
    """
    Returns function that determines whether host should be accessed.
    Timeout is given in seconds.
    """

    def check_fn(host: str, priority_queue: dict[str, int]) -> bool:
        if host not in priority_queue:
            return True

        return (datetime.now() - priority_queue.get(host)).seconds >= timeout

    return check_fn


def get_can_visit_url_fn():
    """
    Checks whether robots.txt allows visit to url.
    """
    # Host -> Robots parser that has read robots.txt
    robots_cache: Dict[str, RobotFileParser] = {}

    def robots_policy_allow_fetching(url: str, host: str) -> bool:
        """
        Check if host allows visiting this URL.
        """
        if host in robots_cache:
            return robots_cache.get(host).can_fetch("*", url)

        robots_parser = RobotFileParser(url=url)

        try:
            robots_parser.read()
            robots_cache[host] = robots_parser

            can_visit = robots_parser.can_fetch("*", url)

            return can_visit
        except:
            return True

    return robots_policy_allow_fetching


seed_urls = [
    "https://bagerbach.com",
    # "https://aau.dk",
    # "https://stackoverflow.com",
    # "https://youtube.com",
    # "https://hckrnews.com",
]

# host -> time visited
hosts: Dict[str, datetime] = {}
# list of urls to explore
frontier: List[str] = []
# url -> title
visited: Dict[str, str] = {}

if __name__ == "__main__":
    print("Starting")

    frontier.extend(seed_urls)
    can_visit_host = get_can_visit_fn(timeout=2)
    can_visit_url = get_can_visit_url_fn()

    while len(frontier) != 0:
        rnd_indx = round(random() * len(frontier)) - 1
        target_url = frontier[rnd_indx]
        host_url = get_host(target_url)

        # Don't want to encounter it again, no matter if we can visit it now or not.
        # Either it's already visited or robots.txt disallow it.
        if target_url in visited or not can_visit_url(target_url, host_url):
            frontier.pop(rnd_indx)
            continue

        if not can_visit_host(host_url, hosts):
            continue

        page = get_page(target_url)
        if page is None:
            continue

        extracted_urls = extract_urls(page, target_url)
        frontier.extend(extracted_urls)
        page_title = page.find("title")
        if page_title is None:
            continue

        print(f"Visit #{len(visited)}: {page_title.string} at {target_url}")
        visited[target_url] = page_title.string

        if len(visited) == 100:
            print("Visited 100 pages. Ending.")
            break

    print("=== Frontier ===")
    print([x for i, x in enumerate(frontier) if i < 5])
    print("=== Hosts ===")
    print([x for i, x in enumerate(hosts.items()) if i < 5])
    print("=== Visited ===")
    print([x for i, x in enumerate(visited.items()) if i < 5])
    print(
        f"Visited {len(visited)} pages. Frontier has {len(frontier)} pages. Met {len(hosts.values())} hosts."
    )
