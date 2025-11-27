#! /bin/env python3
import os
from pathlib import Path
from github import Github, Auth
import re
from tqdm import tqdm

# --- Config ---
DB_CONTAINER = "db"
DB_NAME = os.environ["PGDB"]
DB_USER = os.environ["PGUSER"]
BACKUP_DIR = "split_backup"
BACKUP_FILE = f"{DB_NAME}.backup"
GH_TOKEN = os.environ["GITHUB_TOKEN"]

# --- Github setup ---
auth = Auth.Token(GH_TOKEN)
github = Github(auth=auth)
repo = github.get_repo("fonzzy1/federal-hansard-db")

# --- Backup folder ---
os.makedirs(BACKUP_DIR, exist_ok=True)


# -------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------
def run(cmd):
    """Run a shell command"""
    import subprocess

    subprocess.run(cmd, shell=True, check=True)


def parse_semver(tag):
    """Parse a tag like v1.2.3"""
    if tag is None:
        return [0, 0, 0]
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", tag)
    if not m:
        raise ValueError(f"Invalid tag format: {tag}")
    return list(map(int, m.groups()))


def bump_version(version, bump_type):
    major, minor, patch = version
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    return f"v{major}.{minor}.{patch}"


def choose_bump():
    print("Select version bump:")
    print("  1) major")
    print("  2) minor")
    print("  3) patch")
    choice = input("Enter choice (1/2/3): ").strip()
    if choice == "1":
        return "major"
    elif choice == "2":
        return "minor"
    elif choice == "3":
        return "patch"
    else:
        print("Invalid choice.")
        exit(1)


# -------------------------------------------------------
# DETERMINE TAG
# -------------------------------------------------------
latest_release = None
try:
    latest_release = repo.get_latest_release()
    latest_tag = latest_release.tag_name
except:
    latest_tag = None

current_version = parse_semver(latest_tag)
bump_type = choose_bump()
TAG = bump_version(current_version, bump_type)
RELEASE_NAME = f"Federal Hansard DB {TAG}"

print("Previous tag:", latest_tag)
print("New tag:", TAG)

# -------------------------------------------------------
# DATABASE BACKUP
# -------------------------------------------------------
print(f"Backing up to complete: {BACKUP_FILE}")
dump_cmd = (
    f"pg_dump -h {DB_CONTAINER} -p 5432 -U {DB_USER} "
    f"-d {DB_NAME} --verbose -F c -f {BACKUP_FILE}"
)
run(dump_cmd)
print(f"Local backup complete: {BACKUP_FILE}")

# Split backup file
split_cmd = f"split --verbose -b 50M {BACKUP_FILE} {BACKUP_DIR}/"
run(split_cmd)

# -------------------------------------------------------
# CREATE GITHUB RELEASE
# -------------------------------------------------------
release = repo.create_git_release(
    tag=TAG, name=RELEASE_NAME, message="", draft=False, prerelease=False
)
print("Created new release:", release.html_url)

# -------------------------------------------------------
# UPLOAD ASSETS
# -------------------------------------------------------
for fname in tqdm(os.listdir(BACKUP_DIR), desc="Uploading Assets"):
    fpath = os.path.join(BACKUP_DIR, fname)
    if os.path.isfile(fpath):
        release.upload_asset(fpath)


print("All assets uploaded successfully.")
