import datetime
import requests
from concurrent.futures import ThreadPoolExecutor
import json


with open("fixes.json", "r") as f:
    fixes = json.load(f)

fetch_date = datetime.datetime.today().strftime("%Y-%m-%d")


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


def fetch_raw_parliament_data():
    parliament_data = requests.get(
        "https://handbookapi.aph.gov.au/api/parliaments"
    ).json()
    return parliament_data["value"]


def fetch_raw_data():
    data = requests.get(
        "https://handbookapi.aph.gov.au/api/individuals"
    ).json()["value"]

    # Load all fixes from one JSON file
    with open("fixes.json", "r") as f:
        fixes = json.load(f)

    # Apply preferred names
    for phid, name in fixes["preferred_name_updates"].items():
        update_personal_info(data, phid, {"PreferredName": name})

    # Apply alt_ids
    for phid, alt_list in fixes["alt_ids"].items():
        add_alt_id(data, phid, alt_list)

    return data


def string_to_date(str):
    if not str:
        return None
    if str == fetch_date or str == "" or len(str) != 10 or str == "1900-01-01":
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


def overlaps(service_list, start, end):
    overlapping = []
    for start_string, end_string, service in service_list:
        service_start = string_to_date(start_string)
        service_end = string_to_date(end_string)
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
    seat_fixes = [x for x in fixes["seats"] if x["phid"] == politician["PHID"]]
    raw_services = {}
    for seat_fix in seat_fixes:
        raw_services[seat_fix["term_start"]] = [
            seat_fix["term_end"],
            seat_fix["seat_name"],
        ]
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
    party_fixes = [
        x
        for x in fixes["party_affiliations"]
        if x["phid"] == politician["PHID"]
    ]
    for party_fix in party_fixes:
        raw_services[party_fix["term_start"]] = [
            party_fix["term_end"],
            party_fix["party_name"],
        ]
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


def merge_continuous(ints):
    if not ints:
        return []
    # Convert date strings to date objects, handle None for end date
    ints = [
        (
            string_to_date(s),
            string_to_date(e),
            p,
        )
        for s, e, p in ints
    ]
    ints.sort(key=lambda x: x[0])
    merged = [ints[0]]
    for start, end, party in ints[1:]:
        last_start, last_end, last_party = merged[-1]
        if party == last_party:
            if last_end is None or end is None:
                merged[-1] = (last_start, None, last_party)
            elif start <= last_end + datetime.timedelta(days=1):
                merged[-1] = (last_start, max(last_end, end), last_party)
            else:
                merged.append((start, end, party))
        else:
            merged.append((start, end, party))
    # Convert date objects back to strings, handle None for end date
    return [
        (
            s.strftime("%Y-%m-%d"),
            e.strftime("%Y-%m-%d") if e is not None else None,
            p,
        )
        for s, e, p in merged
    ]


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

    # if politician["PHID"]=="276714":
    #     politician
    #     break
    format_dict = {
        "id": politician["PHID"],
        "altId": politician.get("alt_id", []),
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
        "dob": string_to_date(politician["DateOfBirth"]),
    }

    isSenate = politician["ElectedSenatorNo"] > 0
    isHOR = politician["ElectedMemberNo"] > 0
    parties = politician["RepresentedParties"]
    state = politician["State"]
    electorate = politician["RepresentedElectorates"]
    parliaments = fixes["parliaments"].get(
        politician["PHID"], politician["RepresentedParliaments"]
    )
    start = string_to_date(politician["ServiceHistory_Start"])
    end = string_to_date(politician["ServiceHistory_End"])

    # Standard Case
    # if isSenate != isHOR and len(parties) == 1 and len(electorate) < 2:
    #     for s, e, p in parliament_intervals:
    #         if int(p["PID"]) in parliaments:
    #             true_start = null_max(start, s)
    #             true_end = null_min(end, e)
    #             format_dict["services"]["create"].append(
    #                 {
    #                     "startDate": true_start,
    #                     "endDate": true_end,
    #                     "isSenate": isSenate,
    #                     "seat": electorate[0] if len(electorate) else None,
    #                     "state": state,
    #                     "party": {"connect": {"name": parties[0]}},
    #                     "parliament": {"connect": {"id": p["PID"]}},
    #                 }
    #             )
    # # The special Case where they rep various parties, seats or both senate
    # # and
    # # Avoid because the data is really unclean and needs various fixes
    # else:
    party_intervals = merge_continuous(extract_party(politician))
    seat_intervals = merge_continuous(extract_seat(politician))
    for s, e, p in parliament_intervals:
        if int(p["PID"]) in parliaments:
            overlapping_party = overlaps(party_intervals, s, e)
            for ps, pe, party in overlapping_party:
                overlappping_seat = overlaps(seat_intervals, ps, pe)
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


def fetch_ministries():

    return_list = []
    ministries = requests.get(
        "https://handbookapi.aph.gov.au/api/StatisticalInformation/Ministries"
    ).json()
    shadow_ministries = requests.get(
        "https://handbookapi.aph.gov.au/api/StatisticalInformation/ShadowMinistries"
    ).json()

    ministers = requests.get(
        "https://handbookapi.aph.gov.au/api/ministryrecords"
    ).json()["value"]
    shadow_ministers = requests.get(
        "https://handbookapi.aph.gov.au/api/shadowministryrecords"
    ).json()["value"]

    for ministry in ministries:
        ministry_members = [x for x in ministers if x["MID"] == ministry["Id"]]
        return_list.append(
            {
                "leader": ministry["LeaderPHID"],
                "name": ministry["MinistryName"],
                "firstDate": date_parse(ministry["DateStart"]),
                "lastDate": date_parse(ministry["DateEnd"]),
                "isShadow": False,
                "ministers": [
                    {
                        "firstDate": date_parse(x["MDateStart"]),
                        "lastDate": date_parse(x["RDateEnd"]),
                        "role": x["Role"],
                        "portfolio": x["Entity"],
                        "displayString": f'{x["Role"]} {x["Prep"]} {x["Entity"]}',
                        "parliamentarian": x["PHID"],
                    }
                    for x in ministry_members
                ],
            }
        )
    for ministry in shadow_ministries:
        if ministry["LeaderPHID"]:
            ministry_members = [
                x for x in shadow_ministers if x["SMID"] == ministry["Id"]
            ]
            return_list.append(
                {
                    "leader": ministry["LeaderPHID"],
                    "name": ministry["MinistryName"],
                    "firstDate": date_parse(ministry["DateStart"]),
                    "lastDate": date_parse(ministry["DateEnd"]),
                    "isShadow": True,
                    "ministers": [
                        {
                            "firstDate": date_parse(x["MDateStart"]),
                            "lastDate": date_parse(x["RDateEnd"]),
                            "role": x["Role"],
                            "portfolio": x["Entity"],
                            "displayString": f'{x["Role"]} {x["Prep"]} {x["Entity"]}',
                            "parliamentarian": x["PHID"],
                        }
                        for x in ministry_members
                    ],
                }
            )
        else:
            pass
    return return_list


def date_parse(date_str):
    if not date_str:
        return None
    if len(date_str) == 4:
        return datetime.datetime.strptime(date_str, "%Y")
    elif len(date_str) >= 10:
        return datetime.datetime.strptime(date_str[:10], "%Y-%m-%d")
    else:
        return datetime.datetime.strptime(date_str[:7], "%Y-%m")


def main():
    ministries = fetch_ministries()
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
    return ministries, parties, parliaments, parliament_intervals, politicians
