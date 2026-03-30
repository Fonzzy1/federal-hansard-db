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
RELEASE_TAG = None  # None = latest release (can also be set to specific tag)


def choose_release_type():
    """Choose whether to download stable or prerelease (beta/dev)"""
    print("\nSelect release type:")
    print("  1) stable (main/latest)")
    print("  2) beta/alpha (prerelease)")
    print("  3) specific tag")
    choice = input("Enter choice (1/2/3): ").strip()
    if choice == "1":
        return "stable"
    elif choice == "2":
        return "prerelease"
    elif choice == "3":
        return input("Enter specific tag (e.g., v1.2.3-beta): ").strip()
    else:
        print("Invalid choice.")
        exit(1)

# --- Create local folder ---
os.makedirs(BACKUP_DIR, exist_ok=True)

# -------------------------------------------------------
# GET RELEASE INFO
# -------------------------------------------------------
# Determine which release to fetch
if RELEASE_TAG is not None:
    # Explicit tag set in config
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/tags/{RELEASE_TAG}"
else:
    # Interactive selection
    release_type = choose_release_type()
    if release_type == "stable":
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    elif release_type == "prerelease":
        # Get all releases and find the latest prerelease
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
    else:
        # Specific tag
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/tags/{release_type}"

resp = requests.get(api_url)
resp.raise_for_status()
data = resp.json()

# Handle list of releases (when fetching all for prerelease)
if isinstance(data, list):
    # Find latest prerelease
    prerelease = None
    for r in data:
        if r.get("prerelease", False):
            prerelease = r
            break
    if prerelease is None:
        print("No prerelease (beta/alpha) versions found.")
        exit(1)
    release = prerelease
    print(f"Using latest prerelease: {release['tag_name']}")
else:
    release = data
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
