from prisma import Prisma
import asyncio

"""
Interesting Stats

Raw Counts
- How many Documents?
- How many Authors?
- How many words?

Distributions
- Speeches per data
- Speech per author
- Speech per party
- Speech frequency and legnth of time in parliament


Types:
- Questions and answers
 - Who's asking who?


- Number of speeches vs number of seats?
- Number of speeches without authors

"""


async def main():
    db = Prisma()
    await db.connect()
    result = await db.query_raw(
        """
        SELECT doc."rawDocumentId", count(*), raw.name
        FROM "Document" doc
        JOIN "RawDocument" raw on doc."rawDocumentId" = raw.id
        GROUP BY doc."rawDocumentId", raw.name
    """
    )
    print(result)
    await db.disconnect()


asyncio.run(main())
