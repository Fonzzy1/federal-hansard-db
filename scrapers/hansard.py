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
        if a['href'].endswith(".xml"):
            files.append(requests.compat.urljoin(url, a['href']))
    return files

# ---- Async download ----

async def download_file(session, url, outpath, retries=3):
    """Download a single file, skipping if it already exists, with retries."""
    if os.path.exists(outpath):
        return "skipped"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
    }

    for attempt in range(1, retries+1):
        try:
            async with session.get(url, headers=headers, timeout=60) as resp:
                resp.raise_for_status()
                content = await resp.read()
                with open(outpath, 'wb') as f:
                    f.write(content)
            return "downloaded"
        except Exception as e:
            if attempt < retries:
                await asyncio.sleep(2 ** attempt)  # exponential backoff
            else:
                return f"failed: {e}"

async def main(download_list, max_concurrent=20):
    if not download_list:
        print("No files to download.")
        return

    ensure_dir(os.path.dirname(download_list[0][1]))
    connector = aiohttp.TCPConnector(limit_per_host=max_concurrent)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [download_file(session, url, path) for url, path in download_list]
        # Use tqdm to track progress
        for f in tqdm_asyncio.as_completed(tasks, total=len(tasks), desc="Downloading"):
            result = await f
            # Optionally, you can log result somewhere if needed
            # print(result)

# ---- Main ----

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Async Hansard Scraper")
    parser.add_argument("--is-senate", action="store_true")
    parser.add_argument("outfile", help="Output folder for downloaded XMLs")
    args = parser.parse_args()

    house = "senate" if args.is_senate else "hofreps"
    ensure_dir(args.outfile)

    # 1. Load historical CSV
    df = pd.read_csv("https://raw.githubusercontent.com/wragge/hansard-xml/refs/heads/master/all-sitting-days.csv")
    df = df[df['house'] == house]
    base_url = "http://parlinfo.aph.gov.au"

    download_list = []

    # Add Hansard XMLs from CSV
    for _, row in df.iterrows():
        outpath = os.path.join(args.outfile, f'{row.date}.xml')
        download_list.append((f'{base_url}{row.url}', outpath))

    # Add OpenAustralia XMLs
    open_url = ("http://data.openaustralia.org.au/origxml/senate_debates/"
                if house == "senate"
                else "http://data.openaustralia.org.au/origxml/representatives_debates/")
    open_urls = list_xml_files_from_html(open_url)
    for url in open_urls:
        filename = os.path.basename(url)
        outpath = os.path.join(args.outfile, filename)
        download_list.append((url, outpath))

    # Run async downloader
    asyncio.run(main(download_list, max_concurrent=20))
