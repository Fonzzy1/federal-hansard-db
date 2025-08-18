import requests
from tqdm import tqdm
import zipfile
import tempfile
import os
import shutil
import re
from datetime import datetime
import argparse
from tqdm import tqdm
import os
import shutil


# ---- Helper functions ----
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Async Hansard Scraper")
    parser.add_argument("--is-senate", action="store_true")
    parser.add_argument("outfile", help="Output folder for downloaded XMLs")
    args = parser.parse_args()

    house = "senate" if args.is_senate else "hofreps"
    ensure_dir(args.outfile)
    # --- Settings ---
    url = "https://github.com/wragge/hansard-xml/archive/refs/heads/master.zip"
    house = "commons"  # or "lords"
    args_outfile = "output_folder"  # replace with your actual output folder

    # --- Download to a temp directory ---
    with tempfile.TemporaryDirectory() as tmpdir:
        local_zip_path = os.path.join(tmpdir, "master.zip")
        
        # Download with progress bar
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024
        
        with open(local_zip_path, 'wb') as f, tqdm(
            desc="Downloading",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024
        ) as bar:
            for data in response.iter_content(block_size):
                f.write(data)
                bar.update(len(data))
        
        # --- Unzip in temp dir ---
        with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
        
        extracted_folder = os.path.join(tmpdir, "hansard-xml-master", house)
        

        # --- Process files ---
        all_files = []
        for root, dirs, files in os.walk(extracted_folder):
            for filename in files:
                all_files.append((root, filename))

        for root, filename in tqdm(all_files):
            file_path = os.path.join(root, filename)
            
            # Replace with your function
            yyyymmdd = grab_and_format_yyyymmdd(filename)
            
            # Prepare output path
            os.makedirs(args.outfile, exist_ok=True)
            output_file = os.path.join(args.outfile, f"{yyyymmdd}.xml")
            
            # Move the file
            shutil.move(file_path, output_file)
        
        print("All files processed.")
