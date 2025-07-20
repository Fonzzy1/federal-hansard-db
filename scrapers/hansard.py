from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import time
! pip install playwright
! playwright install
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://parlinfo.aph.gov.au/parlInfo/search/display/display.w3p...')
    page.wait_for_selector('#react-root')  # Wait for main content to load
    print(page.content())
    browser.close()

# Define a custom user agent
HEADERS = {
}

start_date = datetime(2025, 3, 25)
end_date   = datetime(2025, 3, 25)
chambers   = ['hansardr', 'hansards']

def find_xml_link(soup, chamber, dt):
    links = soup.find_all('a', href=True)
    for a in links:
        href = a['href']
        if (
            href.startswith(f"/parlInfo/download/chamber/{chamber}/{dt}/toc_unixml/")
            and href.endswith('.xml;fileType=text%2Fxml')
        ):
            return "http://parlinfo.aph.gov.au" + href
    return None

date = start_date
while date <= end_date:
    date_str = date.strftime('%Y-%m-%d')
    for chamber in chambers:
        url = (
            f"http://parlinfo.aph.gov.au/parlInfo/search/display/display.w3p;query=Id:chamber/{chamber}/{date_str}/0000"
        )
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)  # <-- HEADERS here!
            soup = BeautifulSoup(response.content, 'html.parser')
            xml_link = find_xml_link(soup, chamber, date_str)
            if xml_link:
                print(f"{chamber} on {date_str}: XML link found: {xml_link}")
            else:
                print(f"{chamber} on {date_str}: No XML link")
        except Exception as e:
            print(f"{chamber} on {date_str}: Error: {e}")
        time.sleep(1)
    date += timedelta(days=1)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_selector('#react-root')  # Wait for main content to load
    print(page.content())
    browser.close()



