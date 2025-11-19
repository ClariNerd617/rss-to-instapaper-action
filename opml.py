import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, IO
from pathlib import Path

def parse_opml(source: str|Path|IO[str]) -> List[Dict[str, Optional[str]]]:
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
                feeds.append({
                    "title": outline.attrib.get("title") or outline.attrib.get("text"),
                    "text": outline.attrib.get("text"),
                    "xml_url": outline.attrib.get("xmlUrl"),
                    "html_url": outline.attrib.get("htmlUrl"),
                })
            walk(outline)

    walk(root.find("body"))
    return feeds

if __name__ == "__main__":
    from pprint import pprint
    with open("feeds.opml") as feedfile:
        pprint(parse_opml(feedfile))
