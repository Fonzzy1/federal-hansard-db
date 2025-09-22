import datetime
import requests
from concurrent.futures import ThreadPoolExecutor


def update_personal_info(people, phid, updates):
    """
    Update Level 1 personal information for a given individual.

    Parameters:
    - data: dict from the Handbook API (with 'value' as the list of individuals)
    - phid: PHID of the individual to update
    - updates: dict of fields to update, e.g., {"Surname": "Smith", "GivenNames": "John"}
    """
    for person in people:
        if person.get("PHID") == phid:
            for key, value in updates.items():
                person[key] = value
            return
    print(f"PHID {phid} not found in dataset")


def add_alt_id(people, phid, alt_id):
    """
    Adds in the alternative ID sometimes used in the records
    """
    for person in people:
        if person.get("PHID") == phid:
            person["alt_id"] = alt_id
            return


def add_party_affiliation(
    people,
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
                            f"Party already present for {phid} ({term_start} to {term_end})"
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
                return

        print(f"No matching term found for {phid} ({term_start} to {term_end})")
        return

    print(f"PHID {phid} not found in dataset")


def fetch_raw_parliament_data():
    parliament_data = requests.get(
        "https://handbookapi.aph.gov.au/api/parliaments"
    ).json()
    return parliament_data["value"]


def fetch_raw_data():
    data = requests.get(
        "https://handbookapi.aph.gov.au/api/individuals"
    ).json()["value"]

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
        term_end=datetime.datetime.today().strftime("%Y-%m-%d"),
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

    return data


def string_to_date(str, fetch_date_str):
    if (
        str == fetch_date_str
        or str == ""
        or len(str) != 10
        or str == "1900-01-01"
    ):
        return None
    return datetime.datetime.strptime(str, "%Y-%m-%d")


## These functiuons deal with nulls in the max and min
def null_max(a, b):
    if a is None or b is None:
        return None
    return max(a, b)


def null_min(a, b):
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b)


def overlaps(service_list, start, end, fetch_date_str):
    overlapping = []
    for start_string, end_string, service in service_list:
        service_start = string_to_date(start_string, fetch_date_str)
        service_end = string_to_date(end_string, fetch_date_str)
        # both haven't ended, then always include
        if end == None and service_end == None:
            sub_service_start = null_max(service_start, start)
            sub_service_end = null_min(service_end, end)
            overlapping.append([sub_service_start, sub_service_end, service])
        elif end == None and service_end != None:
            if service_end > start:
                sub_service_start = null_max(service_start, start)
                sub_service_end = null_min(service_end, end)
                overlapping.append(
                    [sub_service_start, sub_service_end, service]
                )
        elif end != None and service_end == None:
            if end > service_start:
                sub_service_start = null_max(service_start, start)
                sub_service_end = null_min(service_end, end)
                overlapping.append(
                    [sub_service_start, sub_service_end, service]
                )
        ## The most normal condition
        elif end != None and service_end != None:
            if service_start < end and service_end > start:
                sub_service_start = null_max(service_start, start)
                sub_service_end = null_min(service_end, end)
                overlapping.append(
                    [sub_service_start, sub_service_end, service]
                )
    return overlapping


def extract_seat(politician):
    raw_services = {}
    for service in politician["ElectorateService"]:
        electorate, start, end = (
            service["Electorate"],
            service["ServiceStart"],
            service["ServiceEnd"],
        )
        raw_services[start] = [end, electorate]
    return [(s, e, electorate) for s, (e, electorate) in raw_services.items()]


def extract_party(politician):
    raw_services = {}
    for service in politician["PartyParliamentaryService"]:
        secondary_service = service["SecondaryService"]
        for party_service in secondary_service:
            party, start, end = (
                party_service["Value"],
                party_service["DateStart"],
                party_service["DateEnd"],
            )
            raw_services[start] = [end, party]
    return [(s, e, party) for s, (e, party) in raw_services.items()]


def parse_dates(data, start_key, end_key):
    parsed = []
    for d in data:
        start_str = d.get(start_key, "")
        end_str = d.get(end_key, "")
        try:
            start = datetime.datetime.strptime(start_str, "%Y-%m-%d")
            end = (
                datetime.datetime.strptime(end_str, "%Y-%m-%d")
                if end_str != "1900-01-01"
                else None
            )
            parsed.append((start, end, d))
        except (ValueError, TypeError):
            start = datetime.datetime.strptime(start_str, "%Y-%m-%d")
            end = None
            parsed.append((start, end, d))
    return parsed


def parse_parties(parliaments):
    parties = set(
        x["Name"] for y in parliaments for x in y["PartiesByParliament"]
    )
    return list(parties)


def parse_parliaments(parliaments):
    parliament_intervals = parse_dates(
        parliaments, "DateOpening", "DateDissolution"
    )

    parsed_parliaments = []
    for parliament in parliaments:
        data = {
            "id": parliament["PID"],
            "firstDate": datetime.datetime.strptime(
                parliament["DateOpening"], "%Y-%m-%d"
            ),
            "lastDate": (
                datetime.datetime.strptime(
                    parliament["DateDissolution"], "%Y-%m-%d"
                )
                if parliament["ParliamentEnd"]
                else None
            ),
        }
        parsed_parliaments.append(data)
    return parsed_parliaments, parliament_intervals


def format_politician(politician, party_dict, parliament_intervals):
    """
    95% of politicians are going to be for lifers in one house, representing the
    same seat or state and representing one party

    We start by seeing if this is true, and then go harder later


    Exceptions

    Switching Party
    Switching House
    Switching Electorate
    Gaps in Electoral Service
    """

    fetch_date = datetime.datetime.today().strftime("%Y-%m-%d")

    # if politician["PHID"]=="276714":
    #     politician
    #     break
    format_dict = {
        "id": politician["PHID"],
        "altId": politician.get("alt_id", None),
        "firstName": (
            politician["PreferredName"][1:-1]
            if politician["PreferredName"]
            else politician["GivenName"]
        ),
        "lastName": politician["FamilyName"],
        "middleNames": politician["MiddleNames"],
        "altName": (
            politician["GivenName"].rstrip()
            if politician["PreferredName"]
            else None
        ),
        "firstNations": politician["FirstNations"],
        "image": f'https://www.aph.gov.au/api/parliamentarian/{politician["PHID"]}/image',
        "gender": (
            1
            if politician["Gender"] == "Male"
            else 2 if politician["Gender"] == "Female" else 9
        ),
        "services": {"create": []},
        "dob": string_to_date(politician["DateOfBirth"], fetch_date),
    }

    isSenate = politician["ElectedSenatorNo"] > 0
    isHOR = politician["ElectedMemberNo"] > 0
    parties = politician["RepresentedParties"]
    state = politician["State"]
    electorate = politician["RepresentedElectorates"]
    parliaments = politician["RepresentedParliaments"]
    start = string_to_date(politician["ServiceHistory_Start"], fetch_date)
    end = string_to_date(politician["ServiceHistory_End"], fetch_date)

    # Standard Case
    if isSenate != isHOR and len(parties) == 1 and len(electorate) < 2:
        for s, e, p in parliament_intervals:
            if int(p["PID"]) in parliaments:
                true_start = null_max(start, s)
                true_end = null_min(end, e)
                format_dict["services"]["create"].append(
                    {
                        "startDate": true_start,
                        "endDate": true_end,
                        "isSenate": isSenate,
                        "seat": electorate[0] if len(electorate) else None,
                        "state": state,
                        "party": {"connect": {"name": parties[0]}},
                        "parliament": {"connect": {"id": p["PID"]}},
                    }
                )
    # The special Case where they rep various parties, seats or both senate
    # and
    # Avoid because the data is really unclean and needs various fixes
    else:
        party_intervals = extract_party(politician)
        seat_intervals = extract_seat(politician)
        for s, e, p in parliament_intervals:
            if int(p["PID"]) in parliaments:
                overlapping_party = overlaps(party_intervals, s, e, fetch_date)
                for ps, pe, party in overlapping_party:
                    overlappping_seat = overlaps(
                        seat_intervals, ps, pe, fetch_date
                    )
                    # There is a seat
                    if len(overlappping_seat):
                        for ss, se, seat in overlappping_seat:
                            format_dict["services"]["create"].append(
                                {
                                    "startDate": ss,
                                    "endDate": se,
                                    "isSenate": False,
                                    "seat": seat,
                                    "state": state,
                                    "party": {"connect": {"name": party}},
                                    "parliament": {"connect": {"id": p["PID"]}},
                                }
                            )
                    # If no seat then its a senate seat
                    else:
                        format_dict["services"]["create"].append(
                            {
                                "startDate": ps,
                                "endDate": pe,
                                "isSenate": True,
                                "seat": None,
                                "state": state,
                                "party": {"connect": {"name": party}},
                                "parliament": {"connect": {"id": p["PID"]}},
                            }
                        )
    return format_dict


def main():
    raw_politicians = fetch_raw_data()
    raw_parliaments = fetch_raw_parliament_data()
    parties = parse_parties(raw_parliaments)
    parliaments, parliament_intervals = parse_parliaments(raw_parliaments)
    with ThreadPoolExecutor() as executor:
        politicians = list(
            executor.map(
                lambda x: format_politician(x, parties, parliament_intervals),
                raw_politicians,
            )
        )
    return parties, parliaments, parliament_intervals, politicians
