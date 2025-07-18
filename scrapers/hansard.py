from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# Define a custom user agent
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept':
'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.aph.gov.au/',
    'Cookie': 'Parlinfo-aphgovau-externalCORS=4ba52bd73866085a6864fd89ed103e9e; Parlinfo-aphgovau-external=4ba52bd73866085a6864fd89ed103e9e; parlInfo-session-cookie=1580277504185423176517254025611411939274'
}

start_date = datetime(1999, 12, 1)
end_date   = datetime(1999, 12, 10)
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
            f"http://parlinfo.aph.gov.au/parlInfo/search/display/display.w3p;"
            f'query%3DId%3A%22chamber/{chamber}/{date_str}/0000%22'
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
    date += timedelta(days=1)
