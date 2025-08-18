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


def add_alt_id(data, phid, alt_id):
    """
    Adds in the alternative ID sometimes used in the records
    """
    people = data.get("value", [])
    for person in people:
        if person.get("PHID") == phid:
            print(f"➕ Adding new field altId = '{alt_id}' for {phid}")
            person["alt_id"] = alt_id
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
    parser = argparse.ArgumentParser()
    parser.add_argument("outfile")
    args = parser.parse_args()

    parliaments_data = requests.get(
        "https://handbookapi.aph.gov.au/api/parliaments"
    ).json()
    data = requests.get("https://handbookapi.aph.gov.au/api/individuals").json()

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

    add_alt_id(data, "KIM", "YI7")
    add_alt_id(data, "009MA", "EL7")
    add_alt_id(data, "00ATA", "TE7")
    add_alt_id(data, "JRD", "037")
    add_alt_id(data, "KCT", "Y87")
    add_alt_id(data, "KSF", "DL7")
    add_alt_id(data, "JVD", "9M7")
    add_alt_id(data, "JRU", "837")
    add_alt_id(data, "KNK", "XD7")
    add_alt_id(data, "KJA", "LF7")
    add_alt_id(data, "K9M", "6G7")
    add_alt_id(data, "KCE", "B87")
    add_alt_id(data, "K5A", "AN7")
    add_alt_id(data, "KVM", "FS7")
    add_alt_id(data, "KSJ", "014")
    add_alt_id(data, "KVY", "ZS7")
    add_alt_id(data, "KDP", "V97")
    add_alt_id(data, "JVV", "WM7")
    add_alt_id(data, "DRW", "XF7")
    add_alt_id(data, "009OD", "0N7")
    add_alt_id(data, "JUST", "ML7")
    add_alt_id(data, "JM9", "Q07")
    add_alt_id(data, "KJU", "WF7")
    add_alt_id(data, "KEO", "6A7")
    add_alt_id(data, "JNG", "457")
    add_alt_id(data, "KB8", "8C7")
    add_alt_id(data, "JXQ", "GB7")
    add_alt_id(data, "KWZ", "VT7")
    add_alt_id(data, "009DB", "6M7")
    add_alt_id(data, "KRR", "8L7")
    add_alt_id(data, "KKT", "BJ7")
    add_alt_id(data, "L0J", "8Q7")
    add_alt_id(data, "KDV", "FG7")
    add_alt_id(data, "JT9", "Z37")
    add_alt_id(data, "JPG", "D27")
    add_alt_id(data, "KIK", "VI7")
    add_alt_id(data, "4I4", "BL7")
    add_alt_id(data, "DQF", "MR7")
    add_alt_id(data, "JMI", "IT4")
    add_alt_id(data, "ZD4", "ZD7")
    add_alt_id(data, "KEI", "4H7")
    add_alt_id(data, "1B6", "DU7")
    add_alt_id(data, "KYP", "4P7")
    add_alt_id(data, "KOH", "8K7")
    add_alt_id(data, "K17", "L67")
    add_alt_id(data, "KAO", "4U7")
    add_alt_id(data, "6V5", "P47")
    # "R56" is tony blair
    # "G5F" Harper steven
    add_alt_id(data, "00APG", "APG")
    add_alt_id(data, "8IS", "81S")
    # DVB president of indonesia
    # "GYB" OBAMA
    add_alt_id(data, "DYN", "oneDYNDYN")
    # "TO3" Chairman of committees
    add_alt_id(data, "KRE", "KEROSENE")
    add_alt_id(data, "K5H", "MQ7")
    add_alt_id(data, "KPV", "IH7")
    add_alt_id(data, "KKD", "2G7")
    add_alt_id(data, "KUU", "YL7")
    add_alt_id(data, "KVK", "GM7")
    add_alt_id(data, "K6F", "757")
    add_alt_id(data, "C7D", "6D7")
    add_alt_id(data, "K1Y", "F27")
    add_alt_id(data, "K2U", "OP7")
    add_alt_id(data, "KBY", "HV7")
    add_alt_id(data, "KUJ", "OL7")
    add_alt_id(data, "KPG", "SG7")
    add_alt_id(data, "KTZ", "4L7")
    add_alt_id(data, "L8O", "YJ7")
    add_alt_id(data, "JXG", "NM7")
    add_alt_id(data, "K1M", "SO7")
    add_alt_id(data, "KQD", "NH7")
    add_alt_id(data, "JTT", "287")
    add_alt_id(data, "CJO", "IU7")
    add_alt_id(data, "CAK", "0P7")
    add_alt_id(data, "JYI", "O97")
    add_alt_id(data, "K8H", "TS7")
    add_alt_id(data, "KOM", "FE7")
    add_alt_id(data, "KSY", "9K7")
    add_alt_id(data, "KTJ", "WK7")
    add_alt_id(data, "KTA", "EK7")
    add_alt_id(data, "KSW", "6K7")
    add_alt_id(data, "K69", "9R7")
    add_alt_id(data, "K8R", "8T7")
    add_alt_id(data, "JYA", "4N7")
    add_alt_id(data, "KQN", "YH7")
    add_alt_id(data, "KNA", "WJ7")
    add_alt_id(data, "K7H", "C67")
    add_alt_id(data, "EVL", "8R7")
    add_alt_id(data, "JYL", "S97")
    add_alt_id(data, "KA8", "OT7")
    add_alt_id(data, "JUI", "J87")
    add_alt_id(data, "OI4", "O14")
    add_alt_id(data, "KBS", "8V7")
    add_alt_id(data, "QD4", "D4")
    add_alt_id(data, "7Y6", "Y6")
    add_alt_id(data, "I0V", "00AF1")
    add_alt_id(data, "00AOS", "Is00AOS")
    add_alt_id(data, "E68", "sE68")
    add_alt_id(data, "281558", "009FX")
    add_alt_id(data, "283585", "FRD")

    out = {
        "fetchDate": datetime.today().strftime("%Y-%m-%d"),
        "parliaments": parliaments_data,
        "politicians": data,
    }

    with open(args.outfile, "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
