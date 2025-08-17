import asyncio
from prisma import Prisma


async def main():
    db = Prisma()
    await db.connect()

    # Example: add two sources
    await db.source.create(
        data={
            "name": "House of Reps Hansard",
            "script": "parsers/hansard.py",
            "scrape": "scrapers/hansard.py",
            "outFile": "scrapers/raw_sources/hansard/hofreps",
            "inFile": "",  # optional
            "groups": {
                "connectOrCreate": [
                    {
                        "where": {"name": "Hansard"},
                        "create": {"name": "Hansard"},
                    }
                ]
            },
        }
    )
    await db.source.create(
        data={
            "name": "Senate Hansard",
            "script": "parsers/hansard.py",
            "scrape": "scrapers/hansard.py",
            "outFile": "scrapers/raw_sources/hansard/senate",
            "inFile": "--is-senate",  # optional
            "groups": {
                "connectOrCreate": [
                    {
                        "where": {"name": "Hansard"},
                        "create": {"name": "Hansard"},
                    }
                ]
            },
        }
    )

    await db.source.create(
        data={
            "name": "Politicians",
            "script": "parsers/politicians.py",
            "scrape": "scrapers/politicians.py",
            "outFile": "scrapers/raw_sources/parliament_data.json",
            "groups": {
                "connectOrCreate": [
                    {
                        "where": {"name": "Metadata"},
                        "create": {"name": "Metadata"},
                    }
                ]
            },
        }
    )

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
