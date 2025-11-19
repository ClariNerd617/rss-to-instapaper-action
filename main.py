# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "httpx",
# ]
# ///
from httpx import AsyncClient, BasicAuth
from os import environ
import logging
import sqlite3
from datetime import datetime, timedelta
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, IO
from pathlib import Path


def parse_opml(source: str | Path | IO[str]) -> List[Dict[str, Optional[str]]]:
    """
    Parse an OPML file (path or file-like object) and return a list of feed info dicts.
    Each dict includes: title, text, xml_url, and html_url (if present).
    """
    tree = ET.parse(source)
    root = tree.getroot()
    feeds = []

    def walk(node):
        for outline in node.findall("outline"):
            if "xmlUrl" in outline.attrib:
                feeds.append(
                    {
                        "title": outline.attrib.get("title")
                        or outline.attrib.get("text"),
                        "text": outline.attrib.get("text"),
                        "xml_url": outline.attrib.get("xmlUrl"),
                        "html_url": outline.attrib.get("htmlUrl"),
                    }
                )
            walk(outline)

    walk(root.find("body"))
    return feeds


async def add_articles(urls: list[str], auth: BasicAuth, log: logging.Logger) -> None:
    async with AsyncClient(
        base_url="https://www.instapaper.com/api/add", auth=auth
    ) as client:
        for url in urls:
            r = await client.post(data={"url": url})
            r.raise_for_status()


def get_articles(feeds: list[dict[str, str]]) -> list[str]:
    """
    TODO Implement using feedparser\n
    Will use GitHub Actions to update SQLite DB in repo as detailed in main() below.

    feeds data object as follows
    [
        {
            "url": url,
            "last_checked: datetime.from_isoformat(datestring),
        },
    ]

    ---
    """

    for feed in feeds:
        url = feed["url"]
        last_checked = feed["last_checked"]
        ...
    return url_list


async def main() -> None:
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

    with open("./feeds.opml") as feedsfile:
        result = parse_opml(feedsfile)
    feedslist: list[str] = [feed[0].url for feed in result.feeds]
    """ TODO Using SQLite, figure out a workflow for:
      - on first run:
        - create sqlite db in repo, populate with feed urls and current timestamp in isoformat
      - on subsequent runs:
        - check sqlite db for feed urls and timestamps
        - update db with current timestamps
      - determine whether first run based on existence checks
      - feed resulting data structure of the form detailed in the docstring for get_articles() above
    """
    feeds = [
        {
            "url": url,
            "last_checked": datetime.now(datetime.UTC).isoformat(),
        }
        for url in feedslist
    ]
    urls: list[str] = await get_articles(feeds=feeds)
    await add_articles(urls=urls, auth=auth, log=log)


if __name__ == "__main__":
    asyncio.run(main())
