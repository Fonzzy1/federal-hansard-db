import json

with open("scrapers/raw_sources/politicians.json", "r") as f:
    data  = json.load(f)


for politician in data['value']:
    format_dict = {
            'firstName':
            'surname':
            'firstNations'

            }
    print(politician.keys())





