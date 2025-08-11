import json
import requests
from datetime import datetime


def update_personal_info(data, phid, updates):
    """
    Update Level 1 personal information for a given individual.

    Parameters:
    - data: dict from the Handbook API (with 'value' as the list of individuals)
    - phid: PHID of the individual to update
    - updates: dict of fields to update, e.g., {"Surname": "Smith", "GivenNames": "John"}
    """
    people = data.get("value", [])
    for person in people:
        if person.get("PHID") == phid:
            for key, value in updates.items():
                if key in person:
                    print(
                        f"🔁 Updating {key} from '{person[key]}' to '{value}'"
                    )
                else:
                    print(f"➕ Adding new field {key} = '{value}'")
                person[key] = value
            return
    print(f"❌ PHID {phid} not found in dataset")


def add_party_affiliation(
    data,
    phid,
    term_start,
    term_end,
    party_name="Australian Labor Party",
    party_id=1,
):
    """
    Add or correct the party affiliation for a given individual's term.

    Parameters:
    - data: dict from the Handbook API (with 'value' as the list of individuals)
    - phid: PHID of the individual to modify
    - term_start: YYYY-MM-DD string
    - term_end: YYYY-MM-DD string
    - party_name: party name to insert
    - party_id: optional numeric ID forthe party
    """

    people = data.get("value", [])
    for person in people:
        if person.get("PHID") != phid:
            continue

        service_list = person.get("PartyParliamentaryService", [])
        for service in service_list:
            if (
                service.get("DateStart") == term_start
                and service.get("DateEnd") == term_end
            ):
                if not service.get("SecondaryService"):
                    service["SecondaryService"] = []

                # Check if already added
                for ss in service["SecondaryService"]:
                    if (
                        ss.get("RoSType") == "Parties Represented"
                        and ss.get("DateStart") == term_start
                        and ss.get("DateEnd") == term_end
                        and ss.get("Value") == party_name
                    ):
                        print(
                            f"✅ Party already present for {phid} ({term_start} to {term_end})"
                        )
                        return

                # Insert the missing party
                correction = {
                    "RoSId": 0,
                    "RoSType": "Parties Represented",
                    "ROSTypeID": 0,
                    "PHID": phid,
                    "Value": party_name,
                    "ValueID": party_id,
                    "DateStart": term_start,
                    "DateEnd": term_end,
                    "SecondaryService": [],
                }

                service["SecondaryService"].append(correction)
                print(f"✅ Added party for {phid} ({term_start} to {term_end})")
                return

        print(
            f"⚠️ No matching term found for {phid} ({term_start} to {term_end})"
        )
        return

    print(f"❌ PHID {phid} not found in dataset")


def main():
    data = requests.get("https://handbookapi.aph.gov.au/api/individuals").json()
    data["fetchDate"] = datetime.today().strftime("%Y-%m-%d")

    add_party_affiliation(
        data,
        phid="KLL",
        term_start="1943-09-21",
        term_end="1946-08-14",
        party_name="Australian Labor Party",
    )
    add_party_affiliation(
        data,
        phid="291406",
        term_start="2025-05-03",
        term_end=data["fetchDate"],
        party_name="Liberal Party of Australia",
    )
    update_personal_info(data, "5U4", {"PreferredName": "(Jim)"})
    update_personal_info(data, "JWX", {"PreferredName": "(Jim)"})
    update_personal_info(data, "ZG4", {"PreferredName": "(Ted)"})
    update_personal_info(data, "K9M", {"PreferredName": "(Les)"})
    update_personal_info(data, "K0O", {"PreferredName": "(Rex)"})
    update_personal_info(data, "BU4", {"PreferredName": "(Doug)"})

    with open("scrapers/raw_sources/politicians.json", "w") as f:
        json.dump(data, f, indent=2)

    data = requests.get("https://handbookapi.aph.gov.au/api/parliaments").json()

    with open("scrapers/raw_sources/parliaments.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
