#! /bin/env/python3
import os
import subprocess
from tqdm import tqdm
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.http import MediaIoBaseDownload
from pathlib import Path

# --- Config ---
DB_CONTAINER = "db"
DB_NAME = "prisma_db"
DB_USER = "prisma_user"
DB_PASSWORD = "prisma_password"
BACKUP_DIR = ".temporary_backup"
BACKUP_FILE = f"{DB_NAME}.backup"
BACKUP_PATH = os.path.join(BACKUP_DIR, BACKUP_FILE)

# --- Ensure backup dir exists ---
os.makedirs(BACKUP_DIR, exist_ok=True)

# --- Google Drive Auth ---
SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "/app/client.json"

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    SERVICE_ACCOUNT_FILE, SCOPES
)

gauth = GoogleAuth()
gauth.credentials = credentials
drive = GoogleDrive(gauth)

folder_id = "1splKDhcBuy1p_OAJTCTuIbx6t5o6yURi"

# --- Search for the backup file ---
file_list = drive.ListFile(
    {
        "q": f"'{folder_id}' in parents and title='{BACKUP_FILE}' and trashed=false"
    }
).GetList()

if not file_list:
    raise FileNotFoundError(
        f"No backup file '{BACKUP_FILE}' found in Drive folder."
    )

gfile = file_list[0]
file_size = int(gfile["fileSize"])

# --- Download with progress bar ---
print("Downloading backup from Drive...")
request = gfile.auth.service.files().get_media(fileId=gfile["id"])
with open(BACKUP_PATH, "wb") as f:
    downloader = MediaIoBaseDownload(
        f, request, chunksize=1024 * 1024 * 10
    )  # 10MB chunks
    done = False
    with tqdm(
        total=file_size, unit="B", unit_scale=True, desc="Download"
    ) as pbar:
        while not done:
            status, done = downloader.next_chunk()
            if status:
                pbar.update(status.resumable_progress - pbar.n)

print(f"Downloaded: {BACKUP_PATH}")


# --- Restore into Postgres with verbose output ---
print("Restoring database...")
restore_cmd = f"PGPASSWORD={DB_PASSWORD} pg_restore -h {DB_CONTAINER} -p 5432 -U {DB_USER} -d {DB_NAME} --clean --verbose {BACKUP_PATH}"
subprocess.run(restore_cmd, shell=True, check=True)
print("Database restore complete.")
