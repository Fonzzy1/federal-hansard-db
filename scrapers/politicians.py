import json
import requests


def main():
    data = requests.get("https://handbookapi.aph.gov.au/api/individuals").json()

    with open("scrapers/raw_sources/politicians.json", "w") as f:
        json.dump(data, f, indent=2)

    data = requests.get("https://handbookapi.aph.gov.au/api/parliaments").json()

    with open("scrapers/raw_sources/parliaments.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
