import os
import json
import subprocess
from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth
from oauth2client.service_account import ServiceAccountCredentials
import io
import tempfile


# --- Config ---
DB_CONTAINER = "postgres"
DB_NAME = "prisma_db"
DB_USER = "prisma_user"
BACKUP_DIR = ".temporary_backup"
BACKUP_FILE = f"{DB_NAME}.backup"  # fixed name
BACKUP_PATH = os.path.join(BACKUP_DIR, BACKUP_FILE)

# --- Ensure backup dir exists ---
os.makedirs(BACKUP_DIR, exist_ok=True)

# --- Get database size (for pv progress) ---
size_bytes = int(
    subprocess.check_output(
        f"docker exec -t {DB_CONTAINER} du -sb /var/lib/postgresql/data | awk '{{print $1}}'",
        shell=True,
    )
)

# --- Dump database with progress ---
dump_cmd = (
    f"docker exec -t {DB_CONTAINER} pg_dump -U {DB_USER} -d {DB_NAME} -F c"
)
pv_cmd = f"pv -s {size_bytes} > {BACKUP_PATH}"
os.system(f"{dump_cmd} | {pv_cmd}")

print(f"Local backup complete: {BACKUP_PATH}")

# Define the OAuth scope for Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = '/root/mount/hansard_db_client_secret.json'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    SERVICE_ACCOUNT_FILE,
    SCOPES
)

gauth = GoogleAuth()
gauth.credentials = credentials
drive = GoogleDrive(gauth)

folder_id = '1splKDhcBuy1p_OAJTCTuIbx6t5o6yURi'

# Search for an existing file with the same name in the folder
file_list = drive.ListFile({
    'q': f"'{folder_id}' in parents and title='{BACKUP_FILE}' and trashed=false"
}).GetList()

if file_list:
    # File exists, update it
    gfile = file_list[0]
    gfile.SetContentFile(BACKUP_PATH)
    gfile.Upload(param={'supportsAllDrives': True})
    print(f"Updated existing file: {BACKUP_FILE}")
else:
    # File does not exist, create new
    file_metadata = {
        'title': BACKUP_FILE,  # PyDrive uses 'title' not 'name'
        'parents': [{'id': folder_id}]
    }
    gfile = drive.CreateFile(file_metadata)
    gfile.SetContentFile(BACKUP_PATH)
    gfile.Upload(param={'supportsAllDrives': True})
    print(f"Created new file: {BACKUP_FILE}")

# --- Remove local temporary file ---
os.remove(BACKUP_PATH)
print("Temporary backup removed.")

