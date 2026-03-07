from prisma import Prisma


async def seed(db: Prisma):
    await db.source.create(
        data={
            "name": "Hansard 1901",
            "parserModule": "parsers.hansard1901",
            "scraperModule": "scrapers.historic_hansard",
            "args": '{"from": "1901-01-01", "to": "1980-12-31"}',
        }
    )
    await db.source.create(
        data={
            "name": "Hansard 1981",
            "parserModule": "parsers.hansard1981",
            "scraperModule": "scrapers.historic_hansard",
            "args": '{"from": "1981-01-01", "to": "1991-10-31"}',
        }
    )

    await db.source.create(
        data={
            "name": "Hansard 1992",
            "parserModule": "parsers.hansard1992",
            "scraperModule": "scrapers.historic_hansard",
            "args": '{"from": "1991-11-01", "to": "1996-12-31"}',
        }
    )

    await db.source.create(
        data={
            "name": "Hansard 1997",
            "parserModule": "parsers.hansard1997",
            "scraperModule": "scrapers.historic_hansard",
            "args": '{"from": "1997-01-01", "to": "1997-12-31"}',
        }
    )

    await db.source.create(
        data={
            "name": "Hansard 1998",
            "parserModule": "parsers.hansard1998",
            "scraperModule": "scrapers.historic_hansard",
            "args": '{"from": "1998-01-01", "to": "2005-12-31"}',
        }
    )

    await db.source.create(
        data={
            "name": "Hansard 1998",
            "parserModule": "parsers.hansard1998",
            "scraperModule": "scrapers.parli_info_hansard",
            "args": '{"from": "2006-01-01", "to": "2011-04-30"}',
        }
    )

    await db.source.create(
        data={
            "name": "Hansard 2011",
            "parserModule": "parsers.hansard2011",
            "scraperModule": "scrapers.parli_info_hansard",
            "args": '{"from": "2011-05-01", "to": "2011-12-31"}',
        }
    )

    await db.source.create(
        data={
            "name": "Hansard 2012",
            "parserModule": "parsers.hansard2012",
            "scraperModule": "scrapers.parli_info_hansard",
            "args": '{"from": "2012-01-01", "to": "2021-09-30"}',
        }
    )
    await db.source.create(
        data={
            "name": "Hansard 2021",
            "parserModule": "parsers.hansard2021",
            "scraperModule": "scrapers.parli_info_hansard",
            "args": '{"from": "2021-10-01", "to": "2026-01-31"}',
        }
    )


async def main() -> None:
    db = Client()
    await db.connect()
    await seed(db)
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
