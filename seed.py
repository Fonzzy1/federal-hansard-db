from prisma import Prisma
import asyncio

db = Prisma()


async def main():
    await db.connect()
    await db.source.create(
        data={
            "name": "Historic House of Reps Hansard",
            "parserModule": "parsers/hansard",
            "scraperModule": "scrapers/historic_hansard",
            "args": "",
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
            "parserModule": "parsers/hansard.py",
            "scraperModule": "scrapers/historic_hansard.py",
            "args": "{'senate':true}",
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
            "parserModule": "parsers/hansard.py",
            "scraperModule": "scrapers/hansard.py",
            "args": "",
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
            "parserModule": "parsers/hansard.py",
            "scraperModule": "scrapers/hansard.py",
            "args": "{'senate':true}",
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



try:
    asyncio.run(main())
except Exception as e:
    print(e)
    asyncio.run(db.disconnect())
