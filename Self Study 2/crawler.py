"""
Web Crawler
"""
import logging
from random import random
from typing import Dict, Set, List
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
from datetime import datetime
from bs4 import BeautifulSoup
import requests

__logger = logging.getLogger(__name__)


def __get_host(url: str) -> str:
    """
    Gets host from any URL.
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def __get_page(url: str, timeout=1000) -> BeautifulSoup:
    """
    Get parsed page.
    """
    res = requests.get(url, timeout=timeout)
    __visited_host(__get_host(url))

    return BeautifulSoup(res.text, "html.parser")


def __format_relative_url(href: str, host: str) -> str:
    """
    Turns a href from anchor tag into full url.
    """
    if href[0] == "/":
        return urljoin(host, href)

    return urlparse(href).geturl()


def __filter_urls(urls: List[str]) -> List[str]:
    """
    Filter any URL that isn't using the HTTPS protocol.
    E.g. removing ssh:// and mailto://
    """
    return [url for url in urls if "https://" in url]


def __extract_urls(parsed: BeautifulSoup, url: str) -> Set[str]:
    """
    Extract all URLs from anchor tags, ensure they are in the correct format, and filter.
    """
    all_anchor_tags = parsed.find_all("a")
    urls = [tag["href"] for tag in all_anchor_tags if tag.get("href", False)]
    formatted = [__format_relative_url(href, url) for href in urls]

    logging.info(
        f"<a>: {len(all_anchor_tags)} | URLs: {len(urls)} | Formatted: {len(formatted)}"
    )

    return __filter_urls(formatted)


def __visited_host(host: str):
    """
    Mark host as visited.
    """
    __hosts[host] = datetime.now()


def __get_can_visit_host_fn(timeout=1, blacklist: List[str] = []):
    """
    Returns function that determines whether host should be accessed.
    Timeout is given in seconds.
    """

    def check_fn(host: str, priority_queue: dict[str, int]) -> bool:
        if host in blacklist:
            return False
        
        if host not in priority_queue:
            return True

        return (datetime.now() - priority_queue.get(host)).seconds >= timeout

    return check_fn


def __get_can_visit_url_fn():
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

__hosts: Dict[str, datetime] = {}
# list of urls to explore
__frontier: List[str] = []
# url -> title
__visited: Dict[str, str] = {}


def crawl(seed_urls: List[str], host_blacklist: List[str], timeout=1) -> tuple[Dict[str, str], List[str], Dict[str, datetime]]:
    """Returns tuple of dict over visited URLs, list of frontier URLs, and dict over visited hosts."""
    logging.info("Starting")
    # host -> time visited

    __frontier.extend(seed_urls)
    blacklist = host_blacklist if host_blacklist else []
    can_visit_host = __get_can_visit_host_fn(timeout=timeout, blacklist=blacklist)
    can_visit_url = __get_can_visit_url_fn()

    while len(__frontier) != 0:
        rnd_indx = round(random() * len(__frontier)) - 1
        target_url = __frontier[rnd_indx]
        host_url = __get_host(target_url)

        # Don't want to encounter it again, no matter if we can visit it now or not.
        # Either it's already visited or robots.txt disallow it.
        if target_url in __visited or not can_visit_url(target_url, host_url):
            __frontier.pop(rnd_indx)
            continue

        if not can_visit_host(host_url, __hosts):
            continue

        logging.info(f"Visiting {target_url}")
        page = __get_page(target_url)
        if page is None:
            continue

        extracted_urls = __extract_urls(page, target_url)
        __frontier.extend(extracted_urls)
        page_title = page.find("title")
        if page_title is None:
            continue

        logging.info(f"Visit #{len(__visited)}: {page_title.string} at {target_url}")
        __visited[target_url] = page_title.string

        if len(__visited) == 100:
            logging.info("Visited 100 pages. Ending.")
            break

    return [__visited, __frontier, __hosts]


# if __name__ == "__main__":
#     seeds = [
#         "https://bagerbach.com",
#         # "https://aau.dk",
#         # "https://stackoverflow.com",
#         # "https://youtube.com",
#         # "https://hckrnews.com",
#     ]
#     [visited, frontier, hosts] = crawl(seeds, timeout=1, host_blacklist=[
#         "https://hckrnews.com",
#         "https://www.youtube.com",
#         "https://facebook.com",
#         "https://google.com",
#         "https://twitter.com",
#         "https://github.com",
#         ])

#     print("=== Frontier ===")
#     print([x for i, x in enumerate(frontier) if i < 5])
#     print("=== Hosts ===")
#     print([x for i, x in enumerate(hosts.items()) if i < 5])
#     print("=== Visited ===")
#     print([x for i, x in enumerate(visited.items()) if i < 5])
#     print(
#         f"Visited {len(visited)} pages. Frontier has {len(frontier)} pages. Met {len(hosts.values())} hosts."
#     )
