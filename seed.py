from prisma import Prisma

db = Prisma()

async def main():
    await db.connect()

    await db.source.create(
        data = {
            "name": "House of Reps Hansard",
            "script": "parsers/hansard.js",
            "scrape": "scrapers/hansard.js",
            "outFile": "/Data/raw_sources/hansard/hofreps",
            "inFile": "",
            "groups": {
                "connectOrCreate": [
                    {
                        "where": { "name": "Hansard" },
                        "create": { "name": "Hansard" },
                    },
                ],
            },
        }
    )

    await db.source.create(
        data = {
            "name": "Senate Hansard",
            "script": "parsers/hansard.js",
            "scrape": "scrapers/hansard.js",
            "outFile": "/Data/raw_sources/hansard/senate",
            "inFile": "--is-senate",
            "groups": {
                "connectOrCreate": [
                    {
                        "where": { "name": "Hansard" },
                        "create": { "name": "Hansard" },
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
