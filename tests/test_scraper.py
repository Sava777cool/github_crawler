import pytest
from aioresponses import aioresponses
from main import (
    get_url,
    get_working_proxy,
    fetch,
    parse_search_results,
    parse_repo_details,
)
from aiohttp import ClientSession

SOURCE_DATA = {
    "keywords": ["python", "asyncio"],
    "type": "repositories",
    "proxies": ["127.0.0.1:8080", "127.0.0.2:8080"],
}


@pytest.fixture
def mock_source(monkeypatch):
    monkeypatch.setattr("main.SOURCE_DATA", SOURCE_DATA)


def test_get_url(mock_source):
    url = get_url()
    assert "python+asyncio" in url
    assert "type=repositories" in url


@pytest.mark.asyncio
async def test_get_working_proxy_success(mock_source):
    with aioresponses() as m:
        m.get(
            "https://api.ipify.org?format=json", status=200, payload={"ip": "1.2.3.4"}
        )
        proxy = await get_working_proxy()
        assert proxy.startswith("http://")


@pytest.mark.asyncio
async def test_fetch(mock_source):
    with aioresponses() as m:
        m.get("https://example.com", status=200, body="OK")
        async with ClientSession() as session:
            result = await fetch(
                session, "https://example.com", ua="TestAgent", proxy="127.0.0.1:1111"
            )
            assert result == "OK"


@pytest.mark.asyncio
async def test_parse_search_results(mock_source):
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
async def test_parse_repo_details(mock_source):
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
            assert result["extra"]["language_stats"] == {"Python": "75", "HTML": "25"}
