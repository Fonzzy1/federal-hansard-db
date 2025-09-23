import os
import json
import subprocess
from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth
from oauth2client.service_account import ServiceAccountCredentials
import tempfile
import sys
from tqdm import tqdm
from pathlib import Path

# --- Config ---
DB_CONTAINER = "postgres"
DB_NAME = "prisma_db"
DB_USER = "prisma_user"
BACKUP_DIR = ".temporary_backup"
BACKUP_FILE = f"{DB_NAME}.backup"  # fixed name
BACKUP_PATH = os.path.join(BACKUP_DIR, BACKUP_FILE)
COMPRESSED_BACKUP_PATH = BACKUP_PATH + ".gz"

# --- Ensure backup dir exists ---
os.makedirs(BACKUP_DIR, exist_ok=True)

# --- Get database size (for pv progress) ---

# --- Dump database with progress ---
dump_cmd = (
    f"docker exec -t {DB_CONTAINER} pg_dump -U {DB_USER} -d {DB_NAME} -F c"
)
pv_cmd = f"pv | gzip > {COMPRESSED_BACKUP_PATH}"
os.system(f"{dump_cmd} | {pv_cmd}")

print(f"Local backup complete and compressed: {COMPRESSED_BACKUP_PATH}")

# --- Google Drive Auth ---
SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "/root/mount/hansard_db_client_secret.json"

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    SERVICE_ACCOUNT_FILE, SCOPES
)

gauth = GoogleAuth()
gauth.credentials = credentials
drive = GoogleDrive(gauth)

folder_id = "1splKDhcBuy1p_OAJTCTuIbx6t5o6yURi"
compressed_filename = os.path.basename(COMPRESSED_BACKUP_PATH)

# --- Search for existing file ---
file_list = drive.ListFile(
    {
        "q": f"'{folder_id}' in parents and title='{compressed_filename}' and trashed=false"
    }
).GetList()

backup_path = Path(COMPRESSED_BACKUP_PATH)
file_size = backup_path.stat().st_size

if file_list:
    # File exists, update it
    gfile = file_list[0]

    with backup_path.open("rb") as fobj:
        with tqdm.wrapattr(
            fobj,
            "read",
            desc=f"Updating {compressed_filename}",
            total=file_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as wrapped:
            if file_size:  # PyDrive bug with empty files
                gfile.content = wrapped
            gfile["title"] = compressed_filename
            gfile.Upload(param={"supportsAllDrives": True})

    print(f"Updated existing file: {compressed_filename}")

else:
    # File does not exist, create new
    file_metadata = {
        "title": compressed_filename,  # PyDrive uses 'title' not 'name'
        "parents": [{"id": folder_id}],
    }
    gfile = drive.CreateFile(file_metadata)

    with backup_path.open("rb") as fobj:
        with tqdm.wrapattr(
            fobj,
            "read",
            desc=f"Creating {compressed_filename}",
            total=file_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as wrapped:
            if file_size:
                gfile.content = wrapped
            gfile["title"] = compressed_filename
            gfile.Upload(param={"supportsAllDrives": True})

    print(f"Created new file: {compressed_filename}")

# --- Cleanup ---
os.remove(COMPRESSED_BACKUP_PATH)
print("Temporary compressed backup removed.")
