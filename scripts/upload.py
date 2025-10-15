#! /bin/env/python3
import os
from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth
from oauth2client.service_account import ServiceAccountCredentials
from tqdm import tqdm
from pathlib import Path

# --- Config ---
DB_CONTAINER = "postgres"
DB_NAME = "prisma_db"
DB_USER = "prisma_user"
DB_PASSWORD = "prisma_password"
BACKUP_DIR = ".temporary_backup"
BACKUP_FILE = f"{DB_NAME}.backup"  # fixed name
BACKUP_PATH = os.path.join(BACKUP_DIR, BACKUP_FILE)

# --- Google Drive Auth ---
SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "/root/client.json"

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    SERVICE_ACCOUNT_FILE, SCOPES
)

gauth = GoogleAuth()
gauth.credentials = credentials
drive = GoogleDrive(gauth)

folder_id = "1splKDhcBuy1p_OAJTCTuIbx6t5o6yURi"
filename = os.path.basename(BACKUP_PATH)

# --- Search for existing file ---
file_list = drive.ListFile(
    {"q": f"'{folder_id}' in parents and title='{filename}' and trashed=false"}
).GetList()


# --- Ensure backup dir exists ---
os.makedirs(BACKUP_DIR, exist_ok=True)

# --- Dump database without compression ---
print(f"Backing up to complete: {BACKUP_PATH}")
dump_cmd = f"PGPASSWORD={DB_PASSWORD} pg_dump -h {DB_CONTAINER} -p 5432 -U {DB_USER} -d {DB_NAME} -F c -f  {BACKUP_PATH}"
os.system(dump_cmd)

print(f"Local backup complete: {BACKUP_PATH}")

backup_path = Path(BACKUP_PATH)
file_size = backup_path.stat().st_size

if file_list:
    # File exists, update it
    gfile = file_list[0]

    with backup_path.open("rb") as fobj:
        with tqdm.wrapattr(
            fobj,
            "read",
            desc=f"Updating {filename}",
            total=file_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as wrapped:
            if file_size:  # PyDrive bug with empty files
                gfile.content = wrapped
            gfile["title"] = filename
            gfile.Upload(param={"supportsAllDrives": True})

    print(f"Updated existing file: {filename}")

else:
    # File does not exist, create new
    file_metadata = {
        "title": filename,
        "parents": [{"id": folder_id}],
    }
    gfile = drive.CreateFile(file_metadata)

    with backup_path.open("rb") as fobj:
        with tqdm.wrapattr(
            fobj,
            "read",
            desc=f"Creating {filename}",
            total=file_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as wrapped:
            if file_size:
                gfile.content = wrapped
            gfile["title"] = filename
            gfile.Upload(param={"supportsAllDrives": True})

    print(f"Created new file: {filename}")
