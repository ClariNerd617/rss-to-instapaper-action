# /// script
# dependencies = [
#   "httpx",
#   "feedparser",
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
import feedparser


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
            log.info(f"Adding url {url}.")
            r = await client.post(data={"url": url})
            r.raise_for_status()


def get_articles(feeds: list[dict[str, str]]) -> list[str]:
    url_list = []
    for feed in feeds:
        feed_url = feed["url"]
        last_checked = datetime.fromisoformat(feed["last_checked"])
        """NOTE: at an unspecified date in the future:
        feedparse will stop handling the http part of parsing feeds
        (source: https://github.com/kurtmckee/feedparser/issues/199#issuecomment-570113456)
        so I will need to add a get_feeds() function and parse the data here
        On the plus side, that means I can async that part too.
        On the minus side, this makes the async main() more complicated for now."""
        feed_parsed = feedparser.parse(feed_url) # unofficially deprecated
        for entry in feed_parsed.entries:
            entry_date = datetime.fromisoformat(entry.published)
            if entry_date - last_checked >= timedelta():
                url_list.append(entry.link)
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

    with open("feeds.opml") as feedsfile:
        feeds = parse_opml(feedsfile)
    feedslist: list[str] = [feed[0]["xml_url"] for feed in feeds]
    """TODO Using SQLite, figure out a workflow for:
      - on first run:
        - create sqlite db in repo, populate with feed urls and current timestamp in isoformat
        - only get the five most-recent urls in this case
      - on subsequent runs:
        - check sqlite db for feed urls and timestamps
        - update db with current timestamps
    """
    # rwc mode is read-write-create. If the file doesn't exist, this'll create it.
    con = sqlite3.connect("file:feeds.db?mode=rwc", uri=True)
    # TODO last_checked set from db for each feed_url
    feeds = [
        {
            "url": url,
            "last_checked": "", 
        }
        for url in feedslist
    ]
    urls: list[str] = await get_articles(feeds=feeds)
    # TODO DB UPDATE last_checked -> datetime.now(datetime.UTC).isoformat()
    await add_articles(urls=urls, auth=auth, log=log)


if __name__ == "__main__":
    asyncio.run(main())
