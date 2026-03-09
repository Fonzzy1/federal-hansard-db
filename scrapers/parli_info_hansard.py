from bs4 import BeautifulSoup
import re
from datetime import datetime
from tqdm import tqdm
from typing import Dict, Any
from rich.progress import Progress
import time
import requests
import random


def request_with_rate_limit_exception(url, retries=5, delay=20):

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


def fetch_html(url: str) -> str:
    """Fetch HTML content from the given URL with rate-limiting handling."""
    response = request_with_rate_limit_exception(url)
    if not response:
        raise Exception(f"Error: Could not fetch {url}")
    return response.text


def parse_hansard_rows(
    soup: BeautifulSoup, base_url: str, date_from: datetime, date_to: datetime
) -> Dict[str, Dict[str, Any]]:
    """
        Extract document metadata from Hansard page rows if the date is within
    bounds.
    """
    xml_links = {}
    rows = soup.find_all("tr")
    for row in rows:
        date_td = row.find("td", class_="date")
        tds = row.find_all("td")
        title_td = tds[1] if len(tds) > 1 else None
        xml_link = row.find("a", title="XML format")

        if date_td and title_td and xml_link:
            date_str = date_td.get_text(strip=True)
            try:
                date_obj = datetime.strptime(date_str, "%d %b %Y")
            except Exception:
                continue

            # Only keep links within range
            if date_from <= date_obj <= date_to:
                title = title_td.get_text(strip=True)
                house = (
                    "hofreps"
                    if "House of Representatives" in title
                    else "senate" if "Senate" in title else None
                )
                is_proof = "Proof" in title
                key = f'{house}-{date_obj.strftime("%Y-%m-%d")}'
                xml_links[key] = {
                    "path": base_url + xml_link["href"],
                    "is_proof": is_proof,
                }
    return xml_links


def get_min_date_on_page(soup: BeautifulSoup) -> datetime:
    """Find the earliest date (as datetime) in the table rows."""
    min_date = None
    for row in soup.find_all("tr"):
        date_td = row.find("td", class_="date")
        if date_td:
            try:
                date_obj = datetime.strptime(
                    date_td.get_text(strip=True), "%d %b %Y"
                )
                if min_date is None or date_obj < min_date:
                    min_date = date_obj
            except Exception:
                continue
    return min_date


def find_previous_week_url(soup: BeautifulSoup, base_url: str) -> str:
    """Find the URL for 'previous sitting week'."""
    link_tag = soup.find(
        "a", string=re.compile(r"previous\s+sitting\s+week", re.I)
    )
    if link_tag and "href" in link_tag.attrs:
        href = link_tag["href"]
        return href if href.startswith("http") else base_url + href
    return None


def file_list_extractor(
    from_day: str, to_day: str
) -> Dict[str, Dict[str, Any]]:
    """
    Extract Hansard XML doc links between from_day and to_day (inclusive).
    Returns dict keyed by 'hofreps-yyyy-mm-dd' or 'senate-yyyy-mm-dd'.
    """
    base_url = "https://www.aph.gov.au"
    hansard_url = f"{base_url}/Parliamentary_Business/Hansard"
    xml_links = {}
    visited_urls = set()

    date_from = datetime.strptime(from_day, "%Y-%m-%d")
    date_to = datetime.strptime(to_day, "%Y-%m-%d")
    approx_total_weeks = max(1, int((date_to - date_from).days / 7) + 1)
    current_url = f"{hansard_url}?wc={date_to.strftime('%y/%m/%Y')}"

    with Progress(transient=False) as progress:
        task = progress.add_task(
            "Scraping Parli-Info", total=approx_total_weeks
        )
        current_max = date_to
        while True:
            if current_url in visited_urls:
                break
            visited_urls.add(current_url)

            html_content = fetch_html(current_url)
            soup = BeautifulSoup(html_content, "html.parser")

            # Parse doc links for relevant dates
            links_on_page = parse_hansard_rows(
                soup, base_url, date_from, current_max
            )
            xml_links.update(links_on_page)

            # Update progress and stop if done
            min_date_obj = get_min_date_on_page(soup)
            if min_date_obj is not None:
                progress.advance(
                    task, max(1, int((current_max - min_date_obj).days / 7))
                )
                current_max = min_date_obj
                if min_date_obj < date_from:
                    break
            else:
                break

            # Find link for previous page
            next_url = find_previous_week_url(soup, base_url)
            if not next_url:
                break
            current_url = next_url

    return xml_links


def scraper(path: str) -> str:
    """Fetch and return text for a given XML file path."""
    response = request_with_rate_limit_exception(path)
    if not response:
        raise Exception(f"Error: Could not fetch {path}")
    return response.text
