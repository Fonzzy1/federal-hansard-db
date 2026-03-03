from prisma import Prisma


async def seed(db: Prisma):
    await db.source.create(
        data={
            "name": "Hansard 1901",
            "parserModule": "parsers.hansard1901",
            "scraperModule": "scrapers.historic_hansard",
            "args": '{"from_year": 1901, "to_year": 1980}',
        }
    )
    await db.source.create(
        data={
            "name": "Hansard 1981",
            "parserModule": "parsers.hansard1981",
            "scraperModule": "scrapers.historic_hansard",
            "args": '{"from_year": 1981, "to_year": 1997}',
        }
    )

    await db.source.create(
        data={
            "name": "Modern Hansard",
            "parserModule": "parsers.hansard",
            "scraperModule": "scrapers.parli_info_hansard",
            "args": '{"start_year":2006}',
        },
    )


async def main() -> None:
    db = Client()
    await db.connect()
    await seed(db)
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
