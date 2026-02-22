import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from tqdm import tqdm
from rich.progress import Progress


def request_with_rate_limit_exception(url, retries=5, delay=20):
    import time
    import requests
    import random

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    for _ in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response
            elif response.status_code == 403:
                time.sleep(delay + random.uniform(0, delay))
            else:
                time.sleep(delay)
        except requests.RequestException:
            time.sleep(delay)
    return None


def file_list_extractor(start_year=2000):
    base_url = "https://www.aph.gov.au"
    hansard_url = f"{base_url}/Parliamentary_Business/Hansard"
    xml_links = {}
    visited_urls = set()
    current_url = hansard_url

    # Set 'now' as the start date for tracking progress
    last_date = datetime.now()
    target_date = datetime(start_year, 1, 1)
    approx_total_weeks = int((last_date - target_date).days / 7) + 1

    with Progress(transient=False) as progress:
        task = progress.add_task("Scraping Parli-Info", total=approx_total_weeks)
        while True:
            if current_url in visited_urls:
                break  # Prevent infinite loop on abnormal pages
            visited_urls.add(current_url)

            html_content = request_with_rate_limit_exception(current_url).text
            soup = BeautifulSoup(html_content, "html.parser")

            # --- Collect data from the page ---
            rows = soup.find_all("tr")
            min_date_obj = None  # Track earliest date found on this page
            for row in rows:
                date_td = row.find("td", class_="date")
                title_td = (
                    row.find_all("td")[1]
                    if len(row.find_all("td")) > 1
                    else None
                )
                xml_link = row.find("a", title="XML format")
                if date_td and title_td and xml_link:
                    date_str = date_td.get_text(strip=True)
                    date_obj = datetime.strptime(date_str, "%d %b %Y")

                    # Functions for updating the tqdm
                    if min_date_obj is None or date_obj < min_date_obj:
                        min_date_obj = date_obj
                    if date_obj.year < start_year:
                        # Update progress bar for the last chunk and exit
                        weeks_covered = int((last_date - date_obj).days / 7)
                        if weeks_covered > 0:
                            progress.update(task, advance=weeks_covered)
                        return xml_links

                    title = title_td.get_text(strip=True)
                    house = (
                        "hofreps"
                        if "House of Representatives" in title
                        else "senate" if "Senate" in title else None
                    )
                    is_proof = "Proof" in title

                    xml_links[f'{house}-{date_obj.strftime("%Y-%m-%d")}'] = {
                        "path": base_url + xml_link["href"],
                        "is_proof": is_proof,
                    }

            # Update the progress bar based on the actual number of weeks
            # covered
            if min_date_obj is not None:
                weeks_covered = int((last_date - min_date_obj).days / 7)
                if weeks_covered > 0:
                    progress.update(task, advance=weeks_covered)
                last_date = min_date_obj

            # --- Find "previous sitting week" link ---
            link_tag = soup.find(
                "a", string=re.compile(r"previous\s+sitting\s+week", re.I)
            )
            if link_tag and "href" in link_tag.attrs:
                # The link might be relative; join it with base_url if necessary
                next_url = link_tag["href"]
                if next_url.startswith("http"):
                    current_url = next_url
                else:
                    current_url = base_url + next_url
            else:
                break  # No more previous sitting weeks

    return xml_links


def scraper(path):
    response = request_with_rate_limit_exception(path)
    if not response:
        raise Exception(f"Error:  Could Not Fetch")
    text = response.text
    return text
