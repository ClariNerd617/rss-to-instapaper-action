from httpx import AsyncClient, BasicAuth
import feedparser as fp
from os import environ
import logging
from json import load
from datetime import datetime, timedelta
import asyncio

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET",
    format=FORMAT,
    datefmt="[%X]",
)
log = logging.getLogger("rss_to_instapaper_action")

auth = BasicAuth(
    username=environ.get("INSTAPAPER_USERNAME", ""),
    password=environ.get("INSTAPAPER_PASSWORD", ""),
)


async def add_articles(urls: list[str]) -> None:
    async with AsyncClient(
        baseUrl="https://www.instapaper.com/api/add", auth=auth
    ) as client:
        async for url in urls:
            r = await client.post(data={"url": url})
            match r.status_code:
                case 201:
                    log.info(
                        f"Article {url} has been successfully added to Instapaper!"
                    )
                case 400:
                    log.exception(
                        f"Error {r.status_code}: Exceeded the rate limit. Try again later. Otherwise, {url} was not accepted."
                    )
                case 403:
                    log.exception(
                        f"Error {r.status_code}: Invalid username or password"
                    )
                case 500:
                    log.exception(
                        f"Error {r.status_code}: Upstream error. Please try again later."
                    )
                case _:
                    log.exception(
                        f"{r.status_code} returned, not documented in Instapaper, please open a ticket at support@help.instapaper.com"
                    )


def get_articles(feeds: list[dict[str, str]]) -> list[str]:
    # TODO Implement using feedparser
    # Should use GitHub Actions Cached last_checked datetime
    # for each feed item and only add urls if they appear
    # after that cached datetime.
    #
    # Also, update GitHub Actions Cached last_checked datetime
    # for each feed item. Maybe refactor this into three functions?
    # For dev purposes using json file for both feeds list
    # and the last_checked.
    #
    # feeds data object:
    #   [
    #       {
    #           "url": url,
    #           "last_checked: datetime.from_isoformat(datestring),
    #       },
    #   ]
    
    for url, last_checked in feeds.items():
        ...
    return url_list


async def main() -> None:
    with open("./feeds.json") as feedsfile:
        feeds: list[str] = load(feedsfile)
    urls: list[str] = await get_articles(feeds=feeds)
    asyncio.run(add_articles(urls=urls))


if __name__ == "__main__":
    asyncio.run(main())
