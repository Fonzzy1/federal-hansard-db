from prisma import Prisma

db = Prisma()

async def main():
    await db.connect()

    await db.source.create(
        data = {
            "name": "Modern House of Reps Hansard",
            "script": "parsers/hansard.py",
            "scrape": "scrapers/hansard.py",
            "outFile": "/Data/raw_sources/hansard/modern/hofreps",
            "inFile": "",
            "groups": {
                "connectOrCreate": [
                    {
                        "where": { "name": "Hansard" },
                        "create": { "name": "Hansard" },
                    },
                    {
                        "where": { "name": "House of Reps" },
                        "create": { "name": "House of Reps" },
                    },
                ],
            },
        }
    )

    await db.source.create(
        data = {
            "name": "Modern Senate Hansard",
            "script": "parsers/hansard.py",
            "scrape": "scrapers/hansard.py",
            "outFile": "/Data/raw_sources/hansard/modern/senate",
            "inFile": "--is-senate",
            "groups": {
                "connectOrCreate": [
                    {
                        "where": { "name": "Hansard" },
                        "create": { "name": "Hansard" },
                    },
                    {
                        "where": { "name": "Senate" },
                        "create": { "name": "Senate" },
                    },
                ],
            },
        }
    )
    await db.source.create(
        data = {
            "name": "Historic House of Reps Hansard",
            "script": "parsers/hansard.py",
            "scrape": "scrapers/historic_hansard.py",
            "outFile": "/Data/raw_sources/hansard/historic/hofreps",
            "inFile": "",
            "groups": {
                "connectOrCreate": [
                    {
                        "where": { "name": "Hansard" },
                        "create": { "name": "Hansard" },
                    },
                    {
                        "where": { "name": "House of Reps" },
                        "create": { "name": "House of Reps" },
                    },
                ],
            },
        }
    )

    await db.source.create(
        data = {
            "name": "Historic Senate Hansard",
            "script": "parsers/hansard.py",
            "scrape": "scrapers/historic_hansard.py",
            "outFile": "/Data/raw_sources/hansard/historic/senate",
            "inFile": "--is-senate",
            "groups": {
                "connectOrCreate": [
                    {
                        "where": { "name": "Hansard" },
                        "create": { "name": "Hansard" },
                    },
                    {
                        "where": { "name": "Senate" },
                        "create": { "name": "Senate" },
                    },
                ],
            },
        }
    )

    await db.source.create(
        data = {
            "name": "Politicians",
            "script": "parsers/politicians.js",
            "scrape": "scrapers/politicians.js",
            "outFile": "/Data/raw_sources/parliament_data.json",
            "groups": {
                "connectOrCreate": [
                    {
                        "where": { "name": "Metadata" },
                        "create": { "name": "Metadata" },
                    },
                ],
            },
        }
    )

    await db.disconnect()

import asyncio
try:
    asyncio.run(main())
except Exception as e:
    print(e)
    asyncio.run(db.disconnect())
