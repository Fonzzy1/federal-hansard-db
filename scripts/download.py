#! /bin/env python3
import os
import requests
from pathlib import Path
import subprocess
from tqdm import tqdm

# --- Config ---
DB_CONTAINER = "db"
DB_NAME = os.environ["PGDB"]
DB_USER = os.environ["PGUSER"]
BACKUP_DIR = "split_backup_download"
RESTORED_FILE = f"{DB_NAME}.backup"

# --- GitHub release info ---
# Replace these with your repo and release
REPO_OWNER = "fonzzy1"
REPO_NAME = "federal-hansard-db"
RELEASE_TAG = None  # None = latest release

# --- Create local folder ---
os.makedirs(BACKUP_DIR, exist_ok=True)

# -------------------------------------------------------
# GET RELEASE INFO
# -------------------------------------------------------
# If latest release
if RELEASE_TAG is None:
    api_url = (
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    )
else:
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/tags/{RELEASE_TAG}"

resp = requests.get(api_url)
resp.raise_for_status()
release = resp.json()
print(f"Downloading release: {release['tag_name']}")

# -------------------------------------------------------
# DOWNLOAD ASSETS
# -------------------------------------------------------
for asset in tqdm(release["assets"], desc="Downloading DB Backup"):
    asset_name = asset["name"]
    download_url = asset["browser_download_url"]
    asset_path = os.path.join(BACKUP_DIR, asset_name)
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(asset_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                _ = f.write(chunk)

# -------------------------------------------------------
# REASSEMBLE SPLIT FILES
# -------------------------------------------------------
split_files = sorted(Path(BACKUP_DIR).glob("*"))  # ensure correct order
with open(RESTORED_FILE, "wb") as outfile:
    for part in split_files:
        print(f"Adding {part} ...")
        with open(part, "rb") as infile:
            _ = outfile.write(infile.read())

print(f"Backup reassembled as {RESTORED_FILE}")

# -------------------------------------------------------
# RESTORE DATABASE
# -------------------------------------------------------
print(f"Restoring database {DB_NAME} ...")
restore_cmd = (
    f"pg_restore -h {DB_CONTAINER} -p 5432 -U {DB_USER} "
    f"-d {DB_NAME} --verbose --clean {RESTORED_FILE} || true"
)
subprocess.run(restore_cmd, shell=True, check=True)
print(f"Database {DB_NAME} restored successfully.")
