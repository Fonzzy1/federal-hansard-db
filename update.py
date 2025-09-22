from prisma import Client
import subprocess
import asyncio
from politicians import main as import_politician_metadata
import importlib
import json


async def main():
    db = Client()
    await db.connect()

    # Fisrt run the politician script
    # This will get all the information about the parliamentarians and store the
    # metadata in the db
    asyncio.run(import_politician_metadata())

    # Grab the data from all sources
    sources = await db.source.find_many()

    for source in sources:
        # First have the scrape scripts, that will take in the inFile, which is
        # either a url or a arg for the scraper. These will create a heap of
        # rawDocument objects we can then go on to parse. All the rawDocuments
        # are create or update so this can be run freely

        ## Scrapers expect a db and then any args that it might want to include
        scraper = importlib.import_module(source.scraperModule).scrape
        args = json.loads(source.args)
        args["source_id"] = source.id
        source_documents = scraper(*args)

        # Parsers will take in a raw_document_id and then create both the
        # documents and join these docuemtents back to the parliamentatians
        parser = importlib.import_module(source.parserModule).parse

        for document in source_documents:
            parsed_doucments = parser(document)
            ## next we insert 

    await db.disconnect()


asyncio.run(main())
