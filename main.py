import json
import asyncio
import aiohttp
import random
from lxml import html
from loguru import logger
from typing import List, Dict
from fake_useragent import UserAgent

SOURCE_DATA = json.load(open("source.json", "r", encoding="utf-8"))


def get_url():
    """
    Method for getting url by keywords from source.json
    :return: url with keywords
    """
    keywords = "+".join(SOURCE_DATA.get("keywords"))
    return f'https://github.com/search?q={keywords}&type={SOURCE_DATA.get("type")}'


async def get_working_proxy() -> str | None:
    """
    Method for checking working proxies
    make requests to https://api.ipify.org
    :return: str http://{proxy} or None
    """

    proxy_list = SOURCE_DATA.get("proxies")
    random.shuffle(proxy_list)

    async with aiohttp.ClientSession() as session:
        for proxy in proxy_list:
            try:
                proxy = f"http://{proxy}"
                async with session.get(
                    "https://api.ipify.org?format=json",
                    proxy=proxy,
                    timeout=2,
                ) as response:
                    if response.status == 200:
                        logger.info(f"Working proxy: {proxy}")
                        return proxy
            except Exception:
                logger.error(f"{proxy} - not working")
    logger.warning("There is no working proxy!")
    return None


async def fetch(
    session: aiohttp.ClientSession, url: str, ua: str, proxy: str
) -> str | None:
    """
    Method async fetch using aiohttp for async requests
    :param session: aiohttp.ClientSession
    :param url: str by keywords or find repositories url
    :param ua: random user agent
    :param proxy: random proxy from source.json
    :return: html content
    """
    try:
        async with session.get(
            url, headers={"User-Agent": ua}, proxy=proxy, timeout=2
        ) as response:
            return await response.text()
    except Exception as e:
        logger.error(f"{url} - {e.__str__()}")
        return None


async def parse_search_results(
    session: aiohttp.ClientSession, proxy: str, ua: str, url: str
) -> List[Dict]:
    """
    Method for parsing search results
    :param session: aiohttp.ClientSession
    :param url: str by keywords
    :param ua: random user agent
    :param proxy: random proxy from source.json
    :return: list of urls of repositories
    """

    html_content = await fetch(session=session, proxy=proxy, ua=ua, url=url)
    if not html_content:
        return []

    tree = html.fromstring(html_content)
    links = tree.xpath('.//div[@data-testid="results-list"]//h3//div/a')

    logger.info("Repositories links successfully parsed!")
    return [{"url": f'https://github.com{link.get("href")}'} for link in links]


async def parse_repo_details(
    session: aiohttp.ClientSession, proxy: str, ua: str, url: str
) -> Dict:
    """
    Methof for parsing repository details
    :param session: aiohttp.ClientSession
    :param url: repositories url
    :param ua: random user agent
    :param proxy: random proxy from source.json
    :return: dict with parsed data
    """

    html_content = await fetch(session=session, proxy=proxy, ua=ua, url=url)
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


async def main():
    # Main function with base logic

    user_agent = UserAgent(platforms="desktop").random
    proxy = await get_working_proxy()
    search_url = get_url()

    if not proxy:
        return

    async with aiohttp.ClientSession() as session:
        page_data = await parse_search_results(
            session=session, proxy=proxy, ua=user_agent, url=search_url
        )

        tasks = [
            parse_repo_details(
                session=session, proxy=proxy, ua=user_agent, url=item.get("url")
            )
            for item in page_data
        ]
        results = await asyncio.gather(*tasks)

        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
            logger.info("Results successfully saved in results.json!")


if __name__ == "__main__":
    asyncio.run(main())
