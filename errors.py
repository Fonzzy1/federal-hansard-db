import re
from pathlib import Path
from datetime import datetime, timedelta
from prisma import Client

# ---- configuration ----
ERROR_FILE = "errors.txt"


# regex pattern for each error block

ERROR_PATTERN = re.compile(
    r"^\s*[\u26A0]?\s*Speeches allocated outside of service window for "
    r"(?P<name>.+?) "
    r"\(ID:\s*(?P<id>[A-Z0-9]+)\)\s*"
    r"outside speech count:\s*(?P<count>\d+),\s*"
    r"first outside date:\s*(?P<first>\d{4}-\d{2}-\d{2}),\s*"
    r"last outside date:\s*(?P<last>\d{4}-\d{2}-\d{2}),\s*"
    r"service window:\s*(?P<start>\d{4}-\d{2}-\d{2})\s*to\s*(?P<end>\d{4}-\d{2}-\d{2})",
    re.IGNORECASE | re.MULTILINE,
)


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d")


def is_high_priority(record):
    return False


def print_services(services):
    for s in services:
        start = s.startDate.replace(tzinfo=None).date()
        end = s.endDate.replace(tzinfo=None).date()
        print(f"  - {start} → {end} | Seat: {s.seat} | Party: {s.party.name}")


def window_distance(service_start, service_end, outside_first, outside_last):
    """
    Returns distance in days between an outside speech window
    and a service window.
    """
    if outside_last < service_start:
        return (service_start - outside_last).days
    elif outside_first > service_end:
        return (outside_first - service_end).days
    else:
        return 0


from operator import itemgetter


def clamp_to_service(record, service):
    first = parse_date(record["first"])
    last = parse_date(record["last"])

    service_start = service.startDate.replace(tzinfo=None)
    service_end = service.endDate.replace(tzinfo=None)

    # outside AFTER service
    if first > service_end:
        return {
            "start": service_end,
            "end": last,
        }

    # outside BEFORE service
    if last < service_start:
        return {
            "start": first,
            "end": service_start,
        }

    # overlapping / already continuous
    return {
        "start": max(first, service_start),
        "end": min(last, service_end),
    }


def closest_service(services, record):
    outside_first = parse_date(record["first"])
    outside_last = parse_date(record["last"])

    distances = []
    for s in services:
        d = window_distance(
            s.startDate.replace(tzinfo=None),
            s.endDate.replace(tzinfo=None),
            outside_first,
            outside_last,
        )
        distances.append((d, s))

    # choose the service with minimum distance
    _, closest = min(distances, key=itemgetter(0))
    return closest


def relation_to_service(first, last, service_start, service_end):
    if last < service_start:
        return "BEFORE service"
    if first > service_end:
        return "AFTER service"
    return "OVERLAPS service"


db = Client()
await db.connect()
text = Path(ERROR_FILE).read_text(encoding="utf-8")

records = []
for m in ERROR_PATTERN.finditer(text):
    r = m.groupdict()
    r["high_priority"] = is_high_priority(r)
    records.append(r)

for record in records:
    if record["high_priority"]:
        continue

    services = await db.service.find_many(
        where={"parliamentarianId": record["id"]},
        include={"party": True},
    )

    if not services:
        continue

    service = closest_service(services, record)
    window = clamp_to_service(record, service)

    record["fixed_start"] = window["start"].strftime("%Y-%m-%d")
    record["fixed_end"] = window["end"].strftime("%Y-%m-%d")
    record["seat"] = service.seat
    record["party"] = service.party.name
    outside_first = parse_date(record["first"])
    outside_last = parse_date(record["last"])

    service_start = service.startDate.replace(tzinfo=None)
    service_end = service.endDate.replace(tzinfo=None)

    distance = window_distance(
        service_start,
        service_end,
        outside_first,
        outside_last,
    )

    relation = relation_to_service(
        outside_first,
        outside_last,
        service_start,
        service_end,
    )

    print("=" * 70)
    print(f'{record["name"]} ({record["id"]})')
    print()
    print("Outside speeches:")
    print(
        f"  {record['first']} → {record['last']}  ({record['count']} speeches)"
    )

    last_speech = await db.document.find_first(
        where={
            "rawAuthor": {"parliamentarianId": record["id"]},
            "date": {"date": outside_last},
        },
        include={"rawAuthor": True, "date": True},
    )

    print()
    print(last_speech.date.date.strftime("%Y-%m-%d"), last_speech.date.house)
    print(
        f'https://parlinfo.aph.gov.au/parlInfo/search/summary/summary.w3p;adv=yes;orderBy=customrank;page=0;query=Date%3A{last_speech.date.date.strftime("%d")}%2F{last_speech.date.date.strftime("%m")}%2F{last_speech.date.date.strftime("%Y")}%20Dataset%3Ahansardr,hansardr80,hansardrIndex,hansards,hansards80,hansardsIndex;resCount=Default'
    )
    print(last_speech.text[:80])

    print()
    print("All services on record:")
    print_services(services)
    print()
    print()
    print("Closest service:")
    print(f"  {service_start.date()} → {service_end.date()}")
    print(f"  Seat: {service.seat}")
    print(f"  Party: {service.party.name}")
    print()
    print(f"Relation: {relation}")
    print(f"Distance to service: {distance} days")
    print()
    print("Clamped window:")
    print(f"  {record['fixed_start']} → {record['fixed_end']}")
    print("=" * 70)
    print(
        f'{{ "phid": "{record["id"]}", "term_start":"{record["fixed_start"]}", "term_end":"{record["fixed_end"]}", "comment": "auto-fix", "party_name": "{record["party"]}"  }},'
    )
    print(
        f'{{ "phid": "{record["id"]}", "term_start":"{record["fixed_start"]}", "term_end":"{record["fixed_end"]}", "comment": "auto-fix", "seat_name": "{record["seat"]}"  }},'
    )

    print("=" * 70)

    print(
        f'{{ "id": "{record["id"]}", "start":"{outside_first.strftime("%Y-%m-%d")}", "end":"{outside_last.strftime("%Y-%m-%d")}", "comment": "auto-fix"  }},'
    )

    print("=" * 70)

    print(
        f'"{record["id"]}": {{"after":"{outside_first.strftime("%Y-%m-%d")}", "before":"{outside_last.strftime("%Y-%m-%d")}", "comment":"auto-fix", "id": ""}},'
    )

    print("=" * 70)
    input("n")
