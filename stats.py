from prisma import Prisma
import asyncio

async def main():
    db = Prisma()
    await db.connect()
    result = await db.query_raw("""
        SELECT doc."rawDocumentId", count(*), raw.name
        FROM "Document" doc
        JOIN "RawDocument" raw on doc."rawDocumentId" = raw.id
        GROUP BY doc."rawDocumentId", raw.name
    """)
    print(result)
    await db.disconnect()

asyncio.run(main())
