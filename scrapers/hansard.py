import os
import asyncio
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
import argparse
from tqdm.asyncio import tqdm_asyncio

# ---- Helper functions ----


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


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


async def download_file(session, url, outpath, retries=3):
    """Download a single file, skipping if it already exists, with retries."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }

    for attempt in range(1, retries + 1):
        try:
            async with session.get(url, headers=headers, timeout=60) as resp:
                resp.raise_for_status()
                content = await resp.read()
                with open(outpath, "wb") as f:
                    f.write(content)
            return "downloaded"
        except Exception as e:
            if attempt < retries:
                await asyncio.sleep(2**attempt)  # exponential backoff
            else:
                return f"failed: {e}"


async def download(download_list, max_concurrent=20):
    if not download_list:
        print("No files to download.")
        return

    ensure_dir(os.path.dirname(download_list[0][1]))
    connector = aiohttp.TCPConnector(limit_per_host=max_concurrent)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            download_file(session, url, path) for url, path in download_list
        ]
        # Use tqdm to track progress
        for f in tqdm_asyncio.as_completed(
            tasks, total=len(tasks), desc="Downloading"
        ):
            result = await f
            # Optionally, you can log result somewhere if needed
            # print(result)


# ---- Main ----


def scraper(db, is_senate=False, source_id=None):
    house = "senate" if is_senate else "hofreps"

    # Add OpenAustralia XMLs
    open_url = (
        "http://data.openaustralia.org.au/origxml/senate_debates/"
        if house == "senate"
        else "http://data.openaustralia.org.au/origxml/representatives_debates/"
    )
    urls = list_xml_files_from_html(open_url)

    for file in urls:
        file_name = parse_filename(file)
        existing_file = await db.rawDocument.find_unique(
            where={"name": file_name, "sourceId": source_id}
        )
        if existing_file:
            pass
        else:
            file_string = download_file(urls)
            await upload_file(source_id, file_name, file_string)
