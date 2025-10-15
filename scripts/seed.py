from prisma import Prisma


async def seed(db: Prisma):
    await db.source.upsert(
        where={"name": "Historic House of Reps Hansard"},
        update={
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
        },
        create={
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
        },
    )

    await db.source.upsert(
        where={"name": "Historic Senate Hansard"},
        update={
            "parserModule": "parsers.hansard",
            "scraperModule": "scrapers.historic_hansard",
            "args": '{"senate":true}',
            "groups": {
                "connectOrCreate": [
                    {
                        "where": {"name": "Hansard"},
                        "create": {"name": "Hansard"},
                    },
                    {"where": {"name": "Senate"}, "create": {"name": "Senate"}},
                ],
            },
        },
        create={
            "name": "Historic Senate Hansard",
            "parserModule": "parsers.hansard",
            "scraperModule": "scrapers.historic_hansard",
            "args": '{"senate":true}',
            "groups": {
                "connectOrCreate": [
                    {
                        "where": {"name": "Hansard"},
                        "create": {"name": "Hansard"},
                    },
                    {"where": {"name": "Senate"}, "create": {"name": "Senate"}},
                ],
            },
        },
    )

    await db.source.upsert(
        where={"name": "Modern House of Reps Hansard"},
        update={
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
        },
        create={
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
        },
    )

    await db.source.upsert(
        where={"name": "Modern Senate Hansard"},
        update={
            "parserModule": "parsers.hansard",
            "scraperModule": "scrapers.hansard",
            "args": '{"senate":true}',
            "groups": {
                "connectOrCreate": [
                    {
                        "where": {"name": "Hansard"},
                        "create": {"name": "Hansard"},
                    },
                    {"where": {"name": "Senate"}, "create": {"name": "Senate"}},
                ],
            },
        },
        create={
            "name": "Modern Senate Hansard",
            "parserModule": "parsers.hansard",
            "scraperModule": "scrapers.hansard",
            "args": '{"senate":true}',
            "groups": {
                "connectOrCreate": [
                    {
                        "where": {"name": "Hansard"},
                        "create": {"name": "Hansard"},
                    },
                    {"where": {"name": "Senate"}, "create": {"name": "Senate"}},
                ],
            },
        },
    )

async def main() -> None:
    db = Client()
    await db.connect()
    await seed(db)
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
