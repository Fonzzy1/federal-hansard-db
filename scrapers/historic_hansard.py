import requests
from tqdm import tqdm
import zipfile
import re
from datetime import datetime
from tqdm import tqdm
import shutil
import os


# ---- Helper functions ----
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def grab_and_format_yyyymmdd(s):
    # Grab all digits in order
    digits = re.findall(r"\d", s)
    if len(digits) < 8:
        return s  # Not enough digits
    # Take the first 8 digits and join them
    yyyymmdd = "".join(digits[:8])
    try:
        date_obj = datetime.strptime(yyyymmdd, "%Y%m%d")
        return date_obj.strftime("%Y-%m-%d")
    except:
        return s


def download_from_github():
    tmpdir = "/cache/hansard_xml"  # set your fixed temp folder path
    os.makedirs(tmpdir, exist_ok=True)
    local_zip_path = os.path.join(tmpdir, "master.zip")

    if not os.path.exists(local_zip_path):
        response = requests.get(
            "https://github.com/fonzzy1/hansard-xml/archive/refs/heads/master.zip",
            stream=True,
        )
        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024

        with open(local_zip_path, "wb") as f, tqdm(
            desc="Downloading",
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(block_size):
                f.write(data)
                bar.update(len(data))

    extracted_folder = os.path.join(
        tmpdir,
        "hansard-xml-master",
    )
    if not os.path.exists(extracted_folder):
        print("Extracting Zips")
        with zipfile.ZipFile(local_zip_path, "r") as zip_ref:
            zip_ref.extractall(tmpdir)
    return extracted_folder


def file_list_extractor(senate=False):
    house = "senate" if senate else "hofreps"

    path = download_from_github()
    file_dict = {}
    for year in os.listdir(os.path.join(path, house)):
        for file in os.listdir(os.path.join(path, house, year)):
            file_dict[grab_and_format_yyyymmdd(file)] = os.path.join(
                path, house, year, file
            )
    return file_dict


def scraper(file):
    with open(file, "r") as f:
        return f.read()
