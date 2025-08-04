import json
import datetime
import prisma
import asyncio


def overlaps(service_start, service_end, parliament_start, parliament_end):
    return service_start < parliament_end and parliament_start < service_end


def extract_party(service):
    raw_party = [
        x
        for x in service["SecondaryService"]
        if x["RoSType"] == "Parties Represented"
    ]
    party = raw_party[0]["Value"] if len(raw_party) else None
    return party


def parse_dates(data, start_key, end_key):
    parsed = []
    for d in data:
        start_str = d.get(start_key, "")
        end_str = d.get(end_key, "")
        try:
            start = datetime.datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.datetime.strptime(end_str, "%Y-%m-%d")
            parsed.append((start, end, d))
        except (ValueError, TypeError):
            start = datetime.datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.datetime(2099, 1, 1)
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
                "update": {},
            },
        )
    return parliament_intervals


def format_politicians(party_dict, parliament_intervals):
    results = []

    with open("scrapers/raw_sources/politicians.json", "r") as f:
        data = json.load(f)

    for politician in data["value"]:
        format_dict = {
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
        for service in politician["PartyParliamentaryService"]:
            if len(service["SecondaryService"]):
                # Stupid exception for a one off date that didn't work
                try:
                    service_start = datetime.datetime.strptime(
                        service["DateStart"], "%Y-%m-%d"
                    )
                except ValueError:
                    service_start = datetime.datetime.strptime(
                        f"{service['DateStart'][:-1]}{int(service['DateStart'][-1]) - 1}",
                        "%Y-%m-%d",
                    )
                try:
                    service_end = (
                        datetime.datetime.strptime(
                            service.get("DateEnd"), "%Y-%m-%d"
                        )
                        if service.get("DateEnd")
                        else datetime.datetime(2099, 1, 1)
                    )
                except ValueError:
                    service_end = datetime.datetime.strptime(
                        f"{service.get('DateEnd')[:-1]}{int(service.get('DateEnd')[-1]) - 1}",
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
                                "endDate": start_date,
                                "startDate": end_date,
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
                                "endDate": datetime.datetime.strptime(
                                    service["DateStart"], "%Y-%m-%d"
                                ),
                                "startDate": datetime.datetime.strptime(
                                    service["DateEnd"], "%Y-%m-%d"
                                ),
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
    return


async def upload_politician(db, politician):
    await db.parliamentarian.create(politician)


async def main():
    db = prisma.Client()
    await db.connect()
    party_dict = await upload_parties(db)
    parliament_intervals = await upload_parliaments(db)
    politicians = format_politicians(party_dict, parliament_intervals)
    for politician in politicians:
        _ = await upload_politician(db, politician)

    await join_politicians_to_raw_authors(db)
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
