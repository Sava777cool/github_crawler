from lxml import html
from pathlib import Path
from loguru import logger
from random import shuffle
from json import load, dump
from typing import List, Dict
from asyncio import gather, run
from aiohttp import ClientSession
from urllib.parse import urlencode
from argparse import ArgumentParser
from fake_useragent import UserAgent


def build_search_url(keywords: list, type_source: str) -> str:
    """
    Method for getting url by keywords from source.json
    :return: url with keywords
    """
    base_url = "https://github.com/search"
    query = {
        "q": " ".join(keywords),
        "type": type_source,
    }
    return f"{base_url}?{urlencode(query)}"


async def get_working_proxy(proxy_list: list, request_timeout: int = 2) -> str | None:
    """
    Method for checking working proxies
    make requests to https://api.ipify.org
    :return: str http://{proxy} or None
    """

    shuffle(proxy_list)

    async with ClientSession() as session:
        for proxy in proxy_list:
            try:
                proxy = f"http://{proxy}"
                async with session.get(
                    "https://api.ipify.org?format=json",
                    proxy=proxy,
                    timeout=request_timeout,
                ) as response:
                    if response.status == 200:
                        logger.info(f"Working proxy: {proxy}")
                        return proxy
            except Exception:
                logger.error(f"{proxy} - not working")
    logger.warning("There is no working proxy!")
    return None


async def get_html_content(
    session: ClientSession, url: str, ua: str, proxy: str, request_timeout: int = 2
) -> str | None:
    """
    Method async get_html_content using aiohttp for async requests
    :param session: ClientSession
    :param url: str by keywords or find repositories url
    :param ua: random user agent
    :param proxy: random proxy from source.json
    :param request_timeout: amount of seconds for request
    :return: html content
    """
    try:
        async with session.get(
            url, headers={"User-Agent": ua}, proxy=proxy, timeout=request_timeout
        ) as response:
            return await response.text()
    except Exception as e:
        logger.error(f"{url} - {e.__str__()}")
        return None


async def parse_search_results(
    session: ClientSession, proxy: str, ua: str, url: str
) -> List[Dict]:
    """
    Method for parsing search results
    :param session: ClientSession
    :param url: str by keywords
    :param ua: random user agent
    :param proxy: random proxy from source.json
    :return: list of urls of repositories
    """

    html_content = await get_html_content(session=session, proxy=proxy, ua=ua, url=url)
    if not html_content:
        return []

    tree = html.fromstring(html_content)
    links = tree.xpath('.//div[@data-testid="results-list"]//h3//div/a')

    logger.info("Repositories links successfully parsed!")
    return [{"url": f'https://github.com{link.get("href")}'} for link in links]


async def parse_repo_details(
    session: ClientSession, proxy: str, ua: str, url: str
) -> Dict:
    """
    Methof for parsing repository details
    :param session: ClientSession
    :param url: repositories url
    :param ua: random user agent
    :param proxy: random proxy from source.json
    :return: dict with parsed data
    """

    html_content = await get_html_content(session=session, proxy=proxy, ua=ua, url=url)
    tree = html.fromstring(html_content)

    try:
        owner = tree.xpath('.//span[@class="author flex-self-stretch"]/a')[
            0
        ].text.strip()
    except IndexError:
        owner = "Unknown"

    lang_data = {}
    languages_block = tree.xpath(
        '//div[@class="BorderGrid-cell"][.//h2[contains(text(), "Languages")]]'
    )

    for block in languages_block:
        links = block.xpath(".//ul/li/a")

        for a in links:
            try:
                lang = (
                    a.xpath(".//span[1]/text()")[0].strip().replace("%", "")
                )  # remove %
                perc = float(a.xpath(".//span[2]/text()")[0].strip().replace("%", ""))
                lang_data[lang] = perc
            except:
                continue
    logger.info("Repository data successfully parsed!")
    return {"url": url, "extra": {"owner": owner, "language_stats": lang_data}}


async def main(file_name: str):
    # Main function with base logic

    base_path = Path(__file__).parent
    source_data = load(open(base_path / file_name, "r", encoding="utf-8"))
    type_source = source_data.get("type").lower()

    user_agent = UserAgent(platforms="desktop").random
    proxy = await get_working_proxy(proxy_list=source_data.get("proxies"))
    search_url = build_search_url(
        keywords=source_data.get("keywords"), type_source=type_source
    )

    if not proxy:
        return

    async with ClientSession() as session:
        page_data = await parse_search_results(
            session=session, proxy=proxy, ua=user_agent, url=search_url
        )

        if type_source == "repositories":
            tasks = [
                parse_repo_details(
                    session=session, proxy=proxy, ua=user_agent, url=item.get("url")
                )
                for item in page_data
            ]
            page_data = await gather(*tasks)

        with open("results.json", "w", encoding="utf-8") as f:
            dump(page_data, f, indent=4, ensure_ascii=False)
            logger.info("Results successfully saved in results.json!")


if __name__ == "__main__":
    parser = ArgumentParser(description="GitHub Crawler")
    parser.add_argument(
        "-f", "--file", help="path to source.json file", default="source.json"
    )
    args = parser.parse_args()
    run(main(file_name=args.file))
