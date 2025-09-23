import os
import subprocess
import gzip
import shutil
from tqdm import tqdm
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.http import MediaIoBaseDownload

# --- Config ---
DB_CONTAINER = "postgres"
DB_NAME = "prisma_db"
DB_USER = "prisma_user"
BACKUP_DIR = ".temporary_backup"
BACKUP_FILE = f"{DB_NAME}.backup"
BACKUP_PATH = os.path.join(BACKUP_DIR, BACKUP_FILE)
COMPRESSED_BACKUP_PATH = BACKUP_PATH + ".gz"

# --- Ensure backup dir exists ---
os.makedirs(BACKUP_DIR, exist_ok=True)

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

# --- Search for the backup file ---
file_list = drive.ListFile(
    {
        "q": f"'{folder_id}' in parents and title='{compressed_filename}' and trashed=false"
    }
).GetList()

if not file_list:
    raise FileNotFoundError(f"No backup file '{compressed_filename}' found in Drive folder.")

gfile = file_list[0]
file_size = int(gfile["fileSize"])

# --- Download with progress bar ---
print("Downloading backup from Drive...")
request = gfile.auth.service.files().get_media(fileId=gfile["id"])
with open(COMPRESSED_BACKUP_PATH, "wb") as f:
    downloader = MediaIoBaseDownload(f, request, chunksize=1024 * 1024 * 10)  # 10MB chunks
    done = False
    with tqdm(total=file_size, unit="B", unit_scale=True, desc="Download") as pbar:
        while not done:
            status, done = downloader.next_chunk()
            if status:
                pbar.update(status.resumable_progress - pbar.n)

print(f"Downloaded: {COMPRESSED_BACKUP_PATH}")

# --- Decompress with progress ---
print("Decompressing backup...")
with gzip.open(COMPRESSED_BACKUP_PATH, "rb") as f_in, open(BACKUP_PATH, "wb") as f_out:
    chunk_size = 1024 * 1024
    with tqdm(total=os.path.getsize(COMPRESSED_BACKUP_PATH),
              unit="B", unit_scale=True, desc="Decompress") as pbar:
        while True:
            chunk = f_in.read(chunk_size)
            if not chunk:
                break
            f_out.write(chunk)
            pbar.update(len(chunk))

print(f"Decompressed backup ready: {BACKUP_PATH}")

# --- Restore into Postgres with progress ---
print("Restoring database...")
file_size = os.path.getsize(BACKUP_PATH)
restore_cmd = (
    f"docker exec -i {DB_CONTAINER} pg_restore -U {DB_USER} -d {DB_NAME} --clean"
)

with open(BACKUP_PATH, "rb") as f:
    with tqdm(total=file_size, unit="B", unit_scale=True, desc="Restore") as pbar:
        process = subprocess.Popen(restore_cmd, shell=True, stdin=subprocess.PIPE)
        chunk_size = 1024 * 1024
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            process.stdin.write(chunk)
            pbar.update(len(chunk))
        process.stdin.close()
        process.wait()

if process.returncode != 0:
    raise RuntimeError("Database restore failed!")
else:
    print("Database restore complete.")

# --- Cleanup ---
os.remove(COMPRESSED_BACKUP_PATH)
os.remove(BACKUP_PATH)
print("Temporary backup files removed.")
