import pytest
from aioresponses import aioresponses
from main import (
    build_search_url,
    get_working_proxy,
    get_html_content,
    parse_search_results,
    parse_repo_details,
)
from aiohttp import ClientSession


@pytest.fixture
def source_data():
    return {
        "keywords": ["python", "asyncio"],
        "type": "repositories",
        "proxies": ["127.0.0.1:8080", "127.0.0.2:8080"],
    }


def test_build_search_url(source_data):
    url = build_search_url(
        keywords=source_data["keywords"], type_source=source_data["type"]
    )
    assert url.startswith("https://github.com/search?")
    assert "python+asyncio" in url
    assert "type=repositories" in url


@pytest.mark.asyncio
async def test_get_working_proxy_success(source_data):
    with aioresponses() as m:
        m.get(
            "https://api.ipify.org?format=json", status=200, payload={"ip": "1.2.3.4"}
        )
        proxy = await get_working_proxy(proxy_list=source_data["proxies"])
        assert proxy.startswith("http://")


@pytest.mark.asyncio
async def test_get_html_content(source_data):
    with aioresponses() as m:
        m.get("https://example.com", status=200, body="OK")
        async with ClientSession() as session:
            result = await get_html_content(
                session, "https://example.com", ua="TestAgent", proxy="127.0.0.1:1111"
            )
            assert result == "OK"


@pytest.mark.asyncio
async def test_parse_search_results(source_data):
    dummy_html = """
    <div>
      <div>
         <div data-testid="results-list">
           <div>
            <div><h3><div><div><a href="/user1/repo1">Repo 1</a></div></div></h3></div>
            <div><h3><span><div><a href="/user2/repo2">Repo 2</a></div></span></h3></div>
          </div>
        </div>
      </div>
    </div>
    """

    with aioresponses() as m:
        m.get(
            "https://github.com/search?q=python+asyncio&type=repositories",
            status=200,
            body=dummy_html,
        )
        async with ClientSession() as session:
            result = await parse_search_results(
                session,
                proxy="127.0.0.1:1111",
                ua="TestUA",
                url="https://github.com/search?q=python+asyncio&type=repositories",
            )
            assert len(result) == 2
            assert result[0]["url"] == "https://github.com/user1/repo1"


@pytest.mark.asyncio
async def test_parse_repo_details(source_data):
    dummy_html = """
    <span class="author flex-self-stretch"><a>JohnDoe</a></span>
    <div class="BorderGrid-cell">
        <h2>Languages</h2>
        <ul>
            <li><a><span>Python</span><span>75%</span></a></li>
            <li><a><span>HTML</span><span>25%</span></a></li>
        </ul>
    </div>
    """
    with aioresponses() as m:
        m.get("https://github.com/user1/repo1", status=200, body=dummy_html)
        async with ClientSession() as session:
            result = await parse_repo_details(
                session,
                proxy="127.0.0.1:1111",
                ua="TestAgent",
                url="https://github.com/user1/repo1",
            )
            assert result["extra"]["owner"] == "JohnDoe"
            assert result["extra"]["language_stats"] == {"Python": 75.0, "HTML": 25.0}
