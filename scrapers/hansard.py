import requests
from bs4 import BeautifulSoup
import re

url_sen = 'https://www.aph.gov.au/Parliamentary_Business/Hansard/Hanssen261110'
url_reps = 'https://www.aph.gov.au/Parliamentary_Business/Hansard/Hansreps_2011'

base_url = 'https://www.aph.gov.au'

# Pattern for Hansard_Display URLs
pattern = re.compile(r'^/Parliamentary_Business/Hansard/Hansard_Display[?].*')

all_links = set()
for url in [url_sen, url_reps]:
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Sometimes links are relative; we deal with that
        if href.startswith('/Parliamentary_Business/Hansard/Hansard_Display'):
            full_url = base_url + href
            all_links.add(full_url)
        elif
        href.startswith('https://www.aph.gov.au/Parliamentary_Business/Hansard/Hansard_Display'):
            all_links.add(href)

# Print (or save) all URLs
for link in sorted(all_links):
    print(link)



