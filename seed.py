from prisma import Prisma
import asyncio


async def main(db):
    await db.source.create(
        data={
            "name": "Historic House of Reps Hansard",
            "parserModule": "parsers.hansard",
            "scraperModule": "scrapers.historic_hansard",
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
            "parserModule": "parsers.hansard",
            "scraperModule": "scrapers.historic_hansard",
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
            "parserModule": "parsers.hansard",
            "scraperModule": "scrapers.hansard",
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
            "parserModule": "parsers.hansard",
            "scraperModule": "scrapers.hansard",
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


db = Prisma()


async def run():
    await db.connect()
    try:
        await main(db)
    except Exception as e:
        raise e
    finally:
        await db.disconnect()


asyncio.run(run())
