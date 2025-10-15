#! /bin/env/python3
from prisma import Client
import asyncio
import importlib
import json
import re
import string
import datetime
from scripts.politicians import main as politician_metadata
from rich.console import Console
from rich.progress import Progress
from scripts.seed import seed as seed_sources

console = Console()


# -------------------- Helpers --------------------


def normalize(text: str) -> str:
    """Normalize text by removing punctuation/whitespace and lowering case."""
    if not text:
        return ""
    return re.sub(rf"[{re.escape(string.punctuation)}\s]", "", text).lower()


def log(msg: str) -> None:
    """Simple logger with consistent style."""
    console.print(f"[bold green]▶[/bold green] {msg}")


# -------------------- DB Operations --------------------
async def insert_document(db, document, raw_document_id):
    if document["type"] == "question" and "answer" in document:
        await db.document.create(
            data={
                "text": document["text"],
                "date": datetime.datetime.strptime(
                    document["date"], "%Y-%m-%d"
                ),
                "type": document["type"],
                "rawAuthor": {
                    "connectOrCreate": {
                        "where": {"name": document["author"]},
                        "create": {"name": document["author"]},
                    }
                },
                "rawDocument": {"connect": {"id": raw_document_id}},
                "citedBy": {
                    "create": {
                        "text": document["answer"]["text"],
                        "date": datetime.datetime.strptime(
                            document["answer"]["date"], "%Y-%m-%d"
                        ),
                        "type": document["answer"]["type"],
                        "rawAuthor": {
                            "connectOrCreate": {
                                "where": {"name": document['answer']["author"]},
                                "create": {"name": document['answer']["author"]},
                            }
                        },
                        "rawDocument": {"connect": {"id": raw_document_id}},
                    }
                },
            }
        )
    else:
        await db.document.create(
            data={
                "text": document["text"],
                "date": datetime.datetime.strptime(
                    document["date"], "%Y-%m-%d"
                ),
                "type": document["type"],
                "rawAuthor": {
                    "connectOrCreate": {
                        "where": {"name": document["author"]},
                        "create": {"name": document["author"]},
                    }
                },
                "rawDocument": {"connect": {"id": raw_document_id}},
            }
        )


async def reset_politician_links(db: Client) -> None:
    log("Resetting politician links from raw authors...")
    await db.rawauthor.update_many(
        where={"parliamentarianId": {"not": None}},
        data={"parliamentarianId": None},
    )
    log("Done resetting links.")


async def load_politician_metadata(db: Client) -> None:
    log("Loading politician metadata...")

    parties, parliaments, parliament_intervals, politicians = (
        politician_metadata()
    )

    log("Inserting parties...")
    await db.party.create_many(
        [{"name": x} for x in parties], skip_duplicates=True
    )

    log("Upserting parliaments...")
    with Progress(console=console, transient=False) as progress:
        task = progress.add_task("Parliaments", total=len(parliaments))
        for x in parliaments:
            await db.parliament.upsert(
                where={"id": x["id"]}, data={"create": x, "update": x}
            )
            progress.advance(task)

    log("Upserting politicians...")
    with Progress(console=console, transient=False) as progress:
        task = progress.add_task("Politicians", total=len(politicians))
        for x in politicians:
            await db.parliamentarian.upsert(
                where={"id": x["id"]},
                data={
                    "update": {
                        **x,
                        "services": {
                            "deleteMany": {},
                            "create": x["services"]["create"],
                        },
                    },
                    "create": x,
                },
            )
            progress.advance(task)

    log("Finished loading metadata.")


async def scrape_and_parse_sources(db: Client) -> None:
    log("Scraping and parsing sources...")

    sources = await db.source.find_many()

    for source in sources:
        log(f"Processing source: [cyan]{source.name}[/cyan]")

        module = importlib.import_module(source.scraperModule)
        parser = importlib.import_module(source.parserModule).parse

        args = json.loads(source.args) if source.args else {}
        file_dict = module.file_list_extractor(**args)

        existing = await db.rawdocument.find_many(
            where={"sourceId": source.id}, include={"text": False}
        )
        existing_names = {doc.name for doc in existing}

        new_documents = {
            name: val
            for name, val in file_dict.items()
            if name not in existing_names
        }

        if new_documents:
            with Progress(console=console, transient=False) as progress:
                task_docs = progress.add_task(
                    f"[green]New files for {source.name}[/green]",
                    total=len(new_documents),
                )

                for name, file in new_documents.items():
                    try:
                        raw_document = module.scraper(file)
                        raw_inserted_document = await db.rawdocument.create(
                            data={
                                "name": name,
                                "text": raw_document,
                                "sourceId": source.id,
                            }
                        )
                        raw_document_id = raw_inserted_document.id
                        documents: dict = parser(raw_document)
                        for document in documents:
                            await insert_document(db, document, raw_document_id)

                        progress.advance(task_docs)

                    except Exception as e:
                        print(e)
                        print(name)
                        print(file)
                        raise

        else:
            console.print(f"[dim]No new files for {source.name}[/dim]")

    log("Finished scraping sources.")


async def join_politicians_to_raw_authors(db: Client) -> None:
    log("Joining raw authors to politicians...")

    all_services = await db.parliamentarian.find_many()
    politicians = {normalize(p.id): p for p in all_services}
    politicians.update(
        {
            normalize(alt_id): p
            for p in all_services
            if hasattr(p, "altId")
            for alt_id in p.altId
        }
    )

    authors = {
        k.id: k
        for k in await db.rawauthor.find_many(where={"parliamentarian": None})
    }

    with Progress(console=console, transient=False) as progress:
        task = progress.add_task("Authors", total=len(authors))

        for auth in authors.values():
            auth_name_clean = normalize(auth.name)
            if not auth_name_clean:
                progress.advance(task)
                continue
            elif auth_name_clean in politicians:
                matched_id = politicians[auth_name_clean].id
                await db.rawauthor.update(
                    where={"id": auth.id},
                    data={"parliamentarian": {"connect": {"id": matched_id}}},
                )
            else:
                console.print(
                    f"[yellow]⚠[/yellow] Could not match: {auth.name} (possible alt name)"
                )
            progress.advance(task)

    log("Finished joining authors.")


# -------------------- Main Orchestration --------------------


async def main() -> None:
    console.rule("[bold blue]Pipeline Start")
    db = Client()
    await db.connect()

    await seed_sources(db)
    await reset_politician_links(db)
    await load_politician_metadata(db)
    await scrape_and_parse_sources(db)
    await join_politicians_to_raw_authors(db)

    await db.disconnect()
    console.rule("[bold blue]Pipeline Complete")


if __name__ == "__main__":
    asyncio.run(main())
