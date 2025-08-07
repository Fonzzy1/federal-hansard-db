import json
import datetime
import prisma
import asyncio
from tqdm.asyncio import tqdm_asyncio


def overlaps(service_start, service_end, parliament_start, parliament_end):
    if parliament_end == None:
        return service_start <= parliament_start and service_end == parliament_end
    ## Case for the 2nd last parliament in a 2 term senate seat
    elif service_end == None and parliament_end != None:
        return service_start <= parliament_start 
    else:
        return service_start < parliament_end and parliament_start < service_end

def extract_party(service):
    party = service["Value"] if service["ROSTypeID"] == 0 else None
    return party


def parse_dates(data, start_key, end_key):
    parsed = []
    for d in data:
        start_str = d.get(start_key, "")
        end_str = d.get(end_key, "")
        try:
            start = datetime.datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.datetime.strptime(end_str, "%Y-%m-%d") if end_str!='1900-01-01' else None
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
    results = []

    with open("scrapers/raw_sources/politicians.json", "r") as f:
        data = json.load(f)

    fetch_date = data['fetchDate']

    for politician in data["value"]:
        # if politician["FamilyName"]=="DARMANIN":
        #     break
        format_dict = {
            'id': politician['PHID'],
            "firstName": (
                politician["PreferredName"][1:-1]
                if politician["PreferredName"]
                else politician["GivenName"]
            ),
            "lastName": politician["FamilyName"],
            "firstNations": politician["FirstNations"],
            "image": politician["Image"],
            "gender": (
                1
                if politician["Gender"] == "Male"
                else 2 if politician["Gender"] == "Female" else 9
            ),
            "services": {"create": []},
            "dob": (
                datetime.datetime.strptime(
                    politician["DateOfBirth"], "%Y-%m-%d"
                )
                if len(politician["DateOfBirth"]) == 10
                else None
            ),
        }

        # service (in raw form) will span 1 election or one change of allegiace to a specific party.
        raw_seat_service = politician["ElectorateService"]
        seat_intervals = parse_dates(
            raw_seat_service, "ServiceStart", "ServiceEnd"
        )
        for primary_service in politician["PartyParliamentaryService"]:
            for service in primary_service['SecondaryService']:
                if service["DateEnd"] < service["DateStart"]:
                    continue
                else:
                    start_string = max(primary_service['DateStart'],service['DateStart'])
                    end_string = min(primary_service['DateEnd'], service['DateEnd'])
                    # Stupid exception for a one off date that didn't work
                    try:
                        service_start = datetime.datetime.strptime(
                            start_string, "%Y-%m-%d"
                        )
                    except ValueError:
                        service_start = datetime.datetime.strptime(
                            f"{start_string[:-1]}{int(start_string[-1]) - 1}",
                            "%Y-%m-%d",
                        )
                    try:
                        if end_string == fetch_date:
                            service_end = None
                        else:
                            service_end = datetime.datetime.strptime( end_string, "%Y-%m-%d") if end_string else None
                    except ValueError:
                        service_end = datetime.datetime.strptime(
                            f"{end_string[:-1]}{int(end_string[-1]) - 1}",
                            "%Y-%m-%d",
                        )

                    matching_parliaments = [
                        d
                        for s, e, d in parliament_intervals
                        if overlaps(service_start, service_end, s, e)
                    ]

                    # For the sake of this database, a service is tied to only on
                    # parliament ever...
                    for parliament in matching_parliaments:
                        # We now need to see if there is a corresponding Seat
                        # Service, else they are in the Senate.
                        # In the case where they are serving in a seat, this will
                        # work with the overall service date as there should be only
                        # one matching parliament
                        
                        seat = [
                            d
                            for s, e, d in seat_intervals
                            if overlaps(service_start, service_end, s, e)
                        ]
                        isSenate = len(seat) == 0
                        if isSenate:
                            # This is the workaround for the fact that senators
                            # don't line up with parliaments
                            start_date = max(
                                datetime.datetime.strptime(
                                    parliament["DateOpening"], "%Y-%m-%d"
                                ),
                                service_start,
                            )
                            if service_end == None:
                                end_date = None
                            else:
                                end_date = min(
                                    service_end,
                                    (
                                        datetime.datetime.strptime(
                                            parliament.get("DateDissolution"),
                                            "%Y-%m-%d",
                                        )
                                        if service.get("DateDissolution")
                                        else datetime.datetime(2099, 1, 1)
                                    ),
                                )
                            format_dict["services"]["create"].append(
                                {
                                    "startDate": start_date,
                                    "endDate": end_date,
                                    "isSenate": isSenate,
                                    "seat": None,
                                    "state": politician["SenateState"],
                                    "party": {
                                        "connect": {
                                            "id": party_dict[extract_party(service)]
                                        }
                                    },
                                    "parliament": {
                                        "connect": {"id": parliament["PID"]}
                                    },
                                }
                            )
                        else:
                            format_dict["services"]["create"].append(
                                {
                                    "startDate": datetime.datetime.strptime(
                                        start_string, "%Y-%m-%d"
                                    )  ,
                                    "endDate": datetime.datetime.strptime(
                                        end_string, "%Y-%m-%d"
                                    ) if service_end != None else None,
                                    "isSenate": isSenate,
                                    "seat": seat[0]["Electorate"],
                                    "state": seat[0]["State"],
                                    "party": {
                                        "connect": {
                                            "id": party_dict[extract_party(service)]
                                        }
                                    },
                                    "parliament": {
                                        "connect": {"id": parliament["PID"]}
                                    },
                                }
                            )

        results.append(format_dict)

    return results


async def join_politicians_to_raw_authors(db):
    # Loop through the parliaments
    all_parliaments = await db.parliament.find_many(
        include={"services": {"include": {"Parliamentarian": True}}}
    )
    for parliament in all_parliaments:
        # Grab the authors and the parliamentarians that are part of this
        # parliament
        documents = await db.document.find_many(
            where={
                "date": {"gte": parliament.firstDate, "lte":
                         parliament.lastDate if parliament.lastDate else
                         datetime.datetime(2099,1,1)},
                'author': {'parliamentarian':None}
            },
            include={"author": True, 'source':True},
            )

        for house in ['House of Representatives', 'Senate']:
            print(house,parliament.id)
            authors = {doc.author.id: doc.author for doc in
                                          documents if house in
                                          doc.source.name }
            politicians = { service.Parliamentarian.id: service.Parliamentarian
                for service in parliament.services if service.isSenate == (house == 'Senate')
               }

            for auth in authors.values():
                potential_matches = [ x for x in politicians.values() if
                                     x.lastName.lower() in auth.rawName.lower()]
                if len(potential_matches) == 0:
                    print(auth.rawName)


#         await db.author.update(
#             where={"id": author.id},
#             data={
#                 "parliamentarian": {
#                     "connect": {"id": parliamentarian_map[author.rawName]}
#                 }
#             },
#         )


async def upload_politician(db, politician):
    await db.parliamentarian.upsert(
            where={'id': politician["id"]},
        data={
            'create': politician,
            'update': politician
        }
        )

async def clean(db):
    await db.author.update_many(
        where={
            'parliamentarianId': {'not': None}
        },
        data={
            'parliamentarianId': None,
        }
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
    # print("Joining politicians to raw authors...")
    # await join_politicians_to_raw_authors(db)
    print("Disconnecting from database...")
    await db.disconnect()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
