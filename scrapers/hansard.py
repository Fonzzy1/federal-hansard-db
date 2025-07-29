import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
import wget
import zipfile
from datetime import datetime
import shutil
import argparse


def grab_and_format_yyyymmdd(s):
    # Grab all digits in order
    digits = re.findall(r"\d", s)
    if len(digits) < 8:
        return None  # Not enough digits
    # Take the first 8 digits and join them
    yyyymmdd = "".join(digits[:8])
    try:
        date_obj = datetime.strptime(yyyymmdd, "%Y%m%d")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        print(f"failed for {s}")


def ensure_dir(dir_path):
    os.makedirs(dir_path, exist_ok=True)


def list_xml_files_from_html(url):
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    files = []
    for l in soup.find_all("a", href=True):
        href = l.get("href")
        if href.endswith(".xml"):
            file_url = requests.compat.urljoin(url, href)
            files.append(file_url)
    return files


def download_files(file_urls, dest_dir, rename_map=None):
    ensure_dir(dest_dir)
    for url in tqdm(file_urls, desc=f"Downloading to {dest_dir}"):
        file_name = os.path.basename(url)
        if rename_map and file_name in rename_map:
            dest_file = rename_map[file_name]
        else:
            dest_file = file_name
        dest = os.path.join(dest_dir, dest_file)
        # Avoid redownloading
        if os.path.exists(dest):
            continue
        try:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
        except Exception as e:
            print(f"Error downloading {url}: {e}")


def my_bar(current, total, width=80):
    progress_message = f"\rDownloading: {current / 1024 / 1024:.2f}/{total / 1024 / 1024:.2f} MB"
    print(progress_message, end="")


### MAIN
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Hansard Scraper",
        description="Fetches the hansard from various sources",
    )
    parser.add_argument("--historical", action="store_true")
    args = parser.parse_args()

    if args.historical:
        # Set download and extraction path
        download_path = "/tmp/master.zip"
        extract_path = "/tmp"

        # Download the zip
        filename = wget.download(
            "https://github.com/wragge/hansard-xml/archive/refs/heads/master.zip",
            out=download_path,
            bar=my_bar,
        )

        # Unzip
        with zipfile.ZipFile(filename, "r") as zip_ref:
            zip_ref.extractall(extract_path)
        # Move the files

        for house in ["hofreps", "senate"]:
            for year in os.listdir(
                f"{extract_path}/hansard-xml-master/{house}"
            ):
                for file in os.listdir(
                    f"{extract_path}/hansard-xml-master/{house}/{year}"
                ):
                    shutil.move(
                        f"{extract_path}/hansard-xml-master/{house}/{year}/{file}",
                        f"./scrapers/raw_sources/hansard/{house}/{grab_and_format_yyyymmdd(file)}.xml",
                    )
            # Clean
            if os.path.exists(
                f"./scrapers/raw_sources/hansard/{house}/None.xml"
            ):
                os.remove(f"./scrapers/raw_sources/hansard/{house}/None.xml")

    # OpenAustralia URLs (these are already in YYYY-mm-dd.xml)
    reps_urls = list_xml_files_from_html(
        "http://data.openaustralia.org.au/origxml/representatives_debates/"
    )
    senate_urls = list_xml_files_from_html(
        "http://data.openaustralia.org.au/origxml/senate_debates/"
    )

    # Download OpenAustralia files (names unchanged)
    download_files(reps_urls, "scrapers/raw_sources/hansard/hofreps")
    download_files(senate_urls, "scrapers/raw_sources/hansard/senate")
