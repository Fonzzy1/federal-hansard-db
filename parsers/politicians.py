import json
import re
import datetime
import prisma
import calendar
import asyncio
from tqdm.asyncio import tqdm_asyncio
from tqdm import tqdm
import string
import re
import datetime
import re
import string
from fuzzywuzzy import process, fuzz  # or from rapidfuzz import process, fuzz


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


async def upload_parties(db):
    party_dict = {}
    with open("scrapers/raw_sources/parliaments.json", "r") as f:
        parliaments = json.load(f)["value"]
    parties = set(
        x["Name"] for y in parliaments for x in y["PartiesByParliament"]
    )
    for party in parties:
        p = await db.party.upsert(
            where={"name": party},
            data={"create": {"name": party}, "update": {}},
        )
        party_dict[party] = p.id
    return party_dict


async def upload_parliaments(db):
    with open("scrapers/raw_sources/parliaments.json", "r") as f:
        parliaments = json.load(f)["value"]
    parliament_intervals = parse_dates(
        parliaments, "DateOpening", "DateDissolution"
    )

    for parliament in parliaments:
        _ = await db.parliament.upsert(
            where={"id": parliament["PID"]},
            data={
                "create": {
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
                },
                "update": {
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
                },
            },
        )
    return parliament_intervals


def format_politicians(party_dict, parliament_intervals):
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

    results = []

    with open("scrapers/raw_sources/politicians.json", "r") as f:
        data = json.load(f)

    fetch_date = data["fetchDate"]

    for politician in data["value"]:
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
            "image": politician["Image"],
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
                            "party": {
                                "connect": {"id": party_dict[parties[0]]}
                            },
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
                    overlapping_party = overlaps(
                        party_intervals, s, e, fetch_date
                    )
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
                                        "party": {
                                            "connect": {"id": party_dict[party]}
                                        },
                                        "parliament": {
                                            "connect": {"id": p["PID"]}
                                        },
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
                                    "party": {
                                        "connect": {"id": party_dict[party]}
                                    },
                                    "parliament": {"connect": {"id": p["PID"]}},
                                }
                            )
        results.append(format_dict)
    return results


def normalize(text):
    if not text:
        return ""
    return re.sub(rf"[{re.escape(string.punctuation)}\s]", "", text).lower()


async def join_politicians_to_raw_authors(db):
    all_services = await db.parliamentarian.find_many()
    politicians = {normalize(p.id): p for p in all_services}
    politicians.update(
        {normalize(p.altId): p for p in all_services if hasattr(p, "altId")}
    )

    authors = {
        k.id: k
        for k in await db.author.find_many(
            where={"parliamentarian": None},
        )
    }

    for auth in authors.values():
        auth_name_clean = normalize(auth.rawName)

        # Skip if cleaned rawName is empty
        if auth_name_clean == "":
            continue
        elif auth_name_clean in politicians.keys():
            matched_id = politicians[auth_name_clean].id
            await db.author.update(
                where={"id": auth.id},
                data={"parliamentarian": {"connect": {"id": matched_id}}},
            )
        else:
            print(f"{auth.rawName} is an alt_name")


async def upload_politician(db, politician):
    await db.parliamentarian.upsert(
        where={"id": politician["id"]},
        data={"create": politician, "update": politician},
    )


async def clean(db):
    await db.author.update_many(
        where={"parliamentarianId": {"not": None}},
        data={
            "parliamentarianId": None,
        },
    )
    await db.service.delete_many()
    await db.parliament.delete_many()
    await db.party.delete_many()
    await db.parliamentarian.delete_many()


async def main():
    print("Connecting to database...")
    db = prisma.Client()
    await db.connect()

    print("Cleaning db...")
    await clean(db)
    print("Uploading parties...")
    party_dict = await upload_parties(db)
    print("Uploading parliaments...")
    parliament_intervals = await upload_parliaments(db)
    print("Formatting politicians...")
    politicians = format_politicians(party_dict, parliament_intervals)
    for politician in tqdm_asyncio(politicians, desc="Uploading politicians"):
        _ = await upload_politician(db, politician)
    print("Joining politicians to raw authors...")
    await join_politicians_to_raw_authors(db)
    print("Disconnecting from database...")
    await db.disconnect()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
