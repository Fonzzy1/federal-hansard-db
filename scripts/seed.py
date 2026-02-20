from prisma import Prisma


async def seed(db: Prisma):
    await db.source.upsert(
        where={"name": "Historic Hansard"},
        data={
            "update": {
                "parserModule": "parsers.hansard",
                "scraperModule": "scrapers.historic_hansard",
                "args": "",
            },
            "create": {
                "name": "Historic Hansard",
                "parserModule": "parsers.hansard",
                "scraperModule": "scrapers.historic_hansard",
                "args": "",
            },
        },
    )

    await db.source.upsert(
        where={"name": "Modern Hansard"},
        data={
            "update": {
                "parserModule": "parsers.hansard",
                "scraperModule": "scrapers.parli_info_hansard",
                "args": '{"start_year":2006}',
            },
            "create": {
                "name": "Modern Hansard",
                "parserModule": "parsers.hansard",
                "scraperModule": "scrapers.parli_info_hansard",
                "args": '{"start_year":2006}',
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
