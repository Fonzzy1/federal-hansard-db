from prisma import Prisma
import json


async def seed(db: Prisma):
    sources = [
        {
            "id": 1,
            "name": "Hansard 1901-1980",
            "parserModule": "parsers.hansard1901",
            "scraperModule": "scrapers.historic_hansard",
            "args_dict": {"from_day": "1901-01-01", "to_day": "1980-12-31"},
        },
        {
            "id": 2,
            "name": "Hansard 1981-1991",
            "parserModule": "parsers.hansard1981",
            "scraperModule": "scrapers.historic_hansard",
            "args_dict": {"from_day": "1981-01-01", "to_day": "1991-10-31"},
        },
        {
            "id": 3,
            "name": "Hansard 1992-1996",
            "parserModule": "parsers.hansard1992",
            "scraperModule": "scrapers.historic_hansard",
            "args_dict": {"from_day": "1991-11-01", "to_day": "1996-12-31"},
        },
        {
            "id": 4,
            "name": "Hansard 1997",
            "parserModule": "parsers.hansard1997",
            "scraperModule": "scrapers.historic_hansard",
            "args_dict": {"from_day": "1997-01-01", "to_day": "1997-12-31"},
        },
        {
            "id": 5,
            "name": "Hansard 1998-1999",
            "parserModule": "parsers.hansard1998",
            "scraperModule": "scrapers.historic_hansard",
            "args_dict": {
                "from_day": "1998-01-01",
                "to_day": "1999-12-31",
                "use_fine_dates": False,
            },
        },
        {
            "id": 6,
            "name": "Hansard 2000-2011",
            "parserModule": "parsers.hansard2000",
            "scraperModule": "scrapers.parli_info_hansard",
            "args_dict": {"from_day": "2000-01-01", "to_day": "2011-04-30"},
        },
        {
            "id": 7,
            "name": "Hansard 2011",
            "parserModule": "parsers.hansard2011",
            "scraperModule": "scrapers.parli_info_hansard",
            "args_dict": {"from_day": "2011-05-01", "to_day": "2011-12-31"},
        },
        {
            "id": 8,
            "name": "Hansard 2012-2021",
            "parserModule": "parsers.hansard2012",
            "scraperModule": "scrapers.parli_info_hansard",
            "args_dict": {"from_day": "2012-01-01", "to_day": "2021-09-05"},
        },
        {
            "id": 9,
            "name": "Hansard 2021-Present",
            "parserModule": "parsers.hansard2021",
            "scraperModule": "scrapers.parli_info_hansard",
            "args_dict": {"from_day": "2021-09-06", "to_day": "2026-12-31"},
        },
    ]

    for source in sources:
        args_json = json.dumps(source["args_dict"])
        await db.source.upsert(
            where={"id": source["id"]},
            data={
                "update": {
                    "name": source["name"],
                    "parserModule": source["parserModule"],
                    "scraperModule": source["scraperModule"],
                    "args": args_json,
                },
                "create": {
                    "id": source["id"],
                    "name": source["name"],
                    "parserModule": source["parserModule"],
                    "scraperModule": source["scraperModule"],
                    "args": args_json,
                },
            },
        )


async def main() -> None:
    db = Prisma()
    await db.connect()
    await seed(db)
    await db.disconnect()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
