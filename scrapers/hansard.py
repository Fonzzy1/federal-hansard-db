import os
import asyncio
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
import requests
import argparse
from tqdm.asyncio import tqdm_asyncio
import time

# ---- Helper functions ----


def list_xml_files_from_html(url):
    """Return list of XML URLs from an OpenAustralia page."""
    import requests

    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    files = []
    for a in soup.find_all("a", href=True):
        if a["href"].endswith(".xml"):
            files.append(requests.compat.urljoin(url, a["href"]))
    return files


def parse_filename(url):
    return url.rstrip(".xml").split("/")[-1]


def file_list_extractor(senate=False):
    house = "senate" if senate else "hofreps"

    # Add OpenAustralia XMLs
    open_url = (
        "http://data.openaustralia.org.au/origxml/senate_debates/"
        if house == "senate"
        else "http://data.openaustralia.org.au/origxml/representatives_debates/"
    )
    urls = list_xml_files_from_html(open_url)
    return {parse_filename(file): file for file in urls}


def scraper(file):
    """Download a single file, skipping if it already exists, with retries."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }

    for attempt in range(1, 4):
        try:
            with requests.get(file, headers=headers, timeout=60) as resp:
                resp.raise_for_status()
                content = resp.text
                return content
        except Exception as e:
            if attempt < 4:
                time.sleep(2**attempt)  # exponential backoff
            else:
                return f"failed: {e}"
