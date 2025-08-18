from prisma import Client
import subprocess
import asyncio


async def main():
    db = Client()
    await db.connect()
    sources = await db.source.find_many()

    for source in sources:
        try:
            if source.inFile:
                subprocess.run(
                    ["python3", source.scrape, source.inFile, source.outFile],
                    check=True,
                )
            else:
                subprocess.run(
                    ["python3", source.scrape, source.outFile], check=True
                )
            subprocess.run(
                ["python3", source.script, source.outFile], check=True
            )
        except subprocess.CalledProcessError:
            break

    await db.disconnect()


asyncio.run(main())
