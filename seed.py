from prisma import Prisma

db = Prisma()


async def main():
    await db.connect()
    await db.source.create(
        data={
            "name": "Historic House of Reps Hansard",
            "script": "parsers/hansard.py",
            "scrape": "scrapers/historic_hansard.py",
            "inFile": "",
            "groups": {
                "connectOrCreate": [
                    {
                        "where": {"name": "Hansard"},
                        "create": {"name": "Hansard"},
                    },
                    {
                        "where": {"name": "House of Reps"},
                        "create": {"name": "House of Reps"},
                    },
                ],
            },
        }
    )

    await db.source.create(
        data={
            "name": "Historic Senate Hansard",
            "script": "parsers/hansard.py",
            "scrape": "scrapers/historic_hansard.py",
            "inFile": "--is-senate",
            "groups": {
                "connectOrCreate": [
                    {
                        "where": {"name": "Hansard"},
                        "create": {"name": "Hansard"},
                    },
                    {
                        "where": {"name": "Senate"},
                        "create": {"name": "Senate"},
                    },
                ],
            },
        }
    )

    await db.source.create(
        data={
            "name": "Modern House of Reps Hansard",
            "script": "parsers/hansard.py",
            "scrape": "scrapers/hansard.py",
            "inFile": "",
            "groups": {
                "connectOrCreate": [
                    {
                        "where": {"name": "Hansard"},
                        "create": {"name": "Hansard"},
                    },
                    {
                        "where": {"name": "House of Reps"},
                        "create": {"name": "House of Reps"},
                    },
                ],
            },
        }
    )

    await db.source.create(
        data={
            "name": "Modern Senate Hansard",
            "script": "parsers/hansard.py",
            "inFile": "--is-senate",
            "groups": {
                "connectOrCreate": [
                    {
                        "where": {"name": "Hansard"},
                        "create": {"name": "Hansard"},
                    },
                    {
                        "where": {"name": "Senate"},
                        "create": {"name": "Senate"},
                    },
                ],
            },
        }
    )


import asyncio

try:
    asyncio.run(main())
except Exception as e:
    print(e)
    asyncio.run(db.disconnect())
