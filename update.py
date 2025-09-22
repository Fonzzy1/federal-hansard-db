from prisma import Client
import subprocess
import asyncio
from politicians import main as politician_metadata
import importlib
import json
import re
import string


def normalize(text):
    if not text:
        return ""
    return re.sub(rf"[{re.escape(string.punctuation)}\s]", "", text).lower()


async def join_politicians_to_raw_authors(db):
    all_services = await db.parliamentarian.find_many()
    politicians = {normalize(p.id): p for p in all_services}
    politicians.update(
        {normalize(p.altId): p for p in all_services if hasattr(p, "altId")}
    )

    authors = {
        k.id: k
        for k in await db.author.find_many(
            where={"parliamentarian": None},
        )
    }

    for auth in authors.values():
        auth_name_clean = normalize(auth.rawName)

        # Skip if cleaned rawName is empty
        if auth_name_clean == "":
            continue
        elif auth_name_clean in politicians.keys():
            matched_id = politicians[auth_name_clean].id
            await db.author.update(
                where={"id": auth.id},
                data={"parliamentarian": {"connect": {"id": matched_id}}},
            )
        else:
            print(f"{auth.rawName} is an alt_name")


async def main():
    db = Client()
    await db.connect()

    # Unjoin the politicians
    await db.rawauthor.update_many(
        where={"parliamentarianId": {"not": None}},
        data={
            "parliamentarianId": None,
        },
    )
    # Fisrt run the politician script
    await db.rawauthor.update_many(
        where={"parliamentarianId": {"not": None}},
        data={
            "parliamentarianId": None,
        },
    )
    parties, parliaments, parliament_intervals, politicians = (
        politician_metadata()
    )

    await db.party.create_many(
        [{"name": x} for x in parties], skip_duplicates=True
    )
    _ = [
        await db.parliament.upsert(
            where={"id": x["id"]}, data={"create": x, "update": x}
        )
        for x in parliaments
    ]
    _ = [
        await db.parliamentarian.upsert(
            where={"id": x["id"]},
            data={
                "update": {
                    **x,
                    "services": {
                        "deleteMany": {},  # remove all existing services
                        "create": x["services"]["create"],  # add new ones
                    },
                },
                "create": x,
            },
        )
        for x in politicians
    ]

    sources = await db.source.find_many()
    for source in sources:
        # First have the scrape scripts, that will take in the inFile, which is
        # either a url or a arg for the scraper. These will create a heap of
        # rawDocument objects we can then go on to parse. All the rawDocuments
        # are create or update so this can be run freely

        ## All scrapers will have 2 parts, a file list extractor and a scraper
        module = importlib.import_module(source.scraperModule)
        parser = importlib.import_module(source.parserModule).parse

        ## Will create a dict of raw names to scraper inputs
        args = json.loads(source.args) if source.args else {}
        file_dict = module.file_list_extractor(**args)

        # Get the current existing documents
        existing = await db.rawdocument.find_many(
            where={"sourceId": source.id}, include={"text": False}
        )

        # Find the elements of file_dict that aren't in the db
        existing_names = {doc.name for doc in existing}
        new_documents = {
            name: val
            for name, val in file_dict.items()
            if name not in existing_names
        }

        for name, file in new_documents:
            raw_docuent = module.scaper(file)
            document_id = await db.rawdocument.create(
                data={"name": name, "text": raw_document, "sourceId": source.id}
            )
            documents = parser(raw_document, document_id)
            for document in documents:
                await db.document.create(data=document)

    # Do all the joins
    await join_politicians_to_raw_authors(db)

    await db.disconnect()


asyncio.run(main())
