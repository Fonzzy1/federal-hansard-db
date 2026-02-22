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
import argparse
import json

console = Console()
fixes = json.load(open("fixes.json", "r"))

# -------------------- Helpers --------------------


def normalize(text: str) -> str:
    """Normalize text by removing punctuation/whitespace and lowering case."""
    if not text:
        return ""
    return re.sub(rf"[{re.escape(string.punctuation)}\s]", "", text).lower()


def log(msg: str) -> None:
    """Simple logger with consistent style."""
    console.print(f"[bold green]▶[/bold green] {msg}")


def apply_raw_author_fixes(author, sitting_day):
    for key in [author, f"_{author}"]:
        fix = fixes["raw_author_fixes"].get(key)
        if not fix:
            continue

        before = fix.get("before")
        after = fix.get("after")
        house = fix.get("house")

        sitting_date_str = sitting_day.date.strftime("%Y-%m-%d")

        if house is not None and house.lower() != sitting_day.house.lower():
            continue

        if before is not None and sitting_date_str > before:
            continue

        if after is not None and sitting_date_str < after:
            continue

        return fix["id"]

    return author


def raw_author_connect_or_create(name, sitting_day):
    fixed_name = apply_raw_author_fixes(name, sitting_day)
    return {
        "connectOrCreate": {
            "where": {"name": fixed_name},
            "create": {"name": fixed_name},
        }
    }


def build_interjections(interjections, sitting_day):
    return {
        "create": [
            {
                "text": inter["text"],
                "sequence": inter["sequence"],
                "rawAuthor": raw_author_connect_or_create(
                    inter["author"], sitting_day
                ),
            }
            for inter in interjections or []
        ]
    }


def build_base_document_data(document, sitting_day, raw_document_id):
    return {
        "text": document["text"],
        "title": document["title"],
        "type": document["type"],
        "date": {"connect": {"id": sitting_day.id}},
        "rawDocument": {"connect": {"id": raw_document_id}},
        "rawAuthor": raw_author_connect_or_create(
            document["author"], sitting_day
        ),
        "interjections": build_interjections(
            document.get("interjections"), sitting_day
        ),
    }


def build_answer_data(answer, sitting_day, raw_document_id):
    return {
        "text": answer["text"],
        "title": answer["title"],
        "type": answer["type"],
        "date": {"connect": {"id": sitting_day.id}},
        "rawDocument": {"connect": {"id": raw_document_id}},
        "rawAuthor": raw_author_connect_or_create(
            answer["author"], sitting_day
        ),
        "interjections": build_interjections(
            answer.get("interjections"), sitting_day
        ),
    }


async def insert_document(db, document, raw_document_id, sitting_day):
    data = build_base_document_data(document, sitting_day, raw_document_id)

    if document["type"] == "question" and "answer" in document:
        data["citedBy"] = {
            "create": build_answer_data(
                document["answer"], sitting_day, raw_document_id
            )
        }

    await db.document.create(data=data)


async def create_sitting_day(db, info, date_override=None) -> None:

    chamber_override = fixes["chamber_override"]
    house_override = fixes["chamber_override"]
    try:
        sitting_day = await db.sittingday.create(
            data={
                "date": datetime.datetime.strptime(
                    date_override if date_override else info["date"], "%Y-%m-%d"
                ),
                "house": house_override.get(info["house"], info["house"]),
                "chamber": chamber_override.get(
                    info["chamber"], info["chamber"]
                ),
                "parliament": info["parliament"],
                "session": info["session"],
                "period": info["period"],
            }
        )
        return sitting_day
    except Exception as e:
        log(
            f"Cannot create sitting day for: {info['date']}, house: {info['house']}, chamber: {info['chamber']}"
        )
        raise e


async def reset_politician_links(db: Client) -> None:
    log("Resetting politician links from raw authors...")
    await db.rawauthor.update_many(
        where={"parliamentarianId": {"not": None}},
        data={"parliamentarianId": None},
    )
    log("Done resetting links.")


async def load_politician_metadata(db: Client) -> None:
    log("Loading politician metadata...")

    ministries, parties, parliaments, parliament_intervals, politicians = (
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

    log("Upserting ministries...")
    await db.query_raw('TRUNCATE "Ministry" CASCADE;')
    await db.query_raw('TRUNCATE "Minister" CASCADE;')
    with Progress(console=console, transient=False) as progress:
        task = progress.add_task("Ministries", total=len(ministries))
        for x in ministries:
            await db.ministry.create(
                data={
                    "leader": {"connect": {"id": x["leader"]}},
                    "name": x["name"],
                    "firstDate": x["firstDate"],
                    "lastDate": x["lastDate"],
                    "isShadow": x["isShadow"],
                    "ministers": {
                        "create": [
                            {
                                **{
                                    k: v
                                    for k, v in y.items()
                                    if k != "parliamentarian"
                                },
                                "parliamentarianId": y[
                                    "parliamentarian"
                                ],  # Use parliamentarianId
                            }
                            for y in x["ministers"]
                        ]
                    },
                }
            )
            progress.advance(task)

    log("Finished loading metadata.")


async def scrape_and_parse_sources(db: Client) -> None:

    sitting_day_override = fixes["sitting_day_override"]
    log("Scraping and parsing sources...")

    sources = await db.source.find_many()
    sources.reverse()

    for source in sources:
        log(f"Processing source: [cyan]{source.name}[/cyan]")

        module = importlib.import_module(source.scraperModule)
        parser = importlib.import_module(source.parserModule).parse

        sitting_day_override_for_source = sitting_day_override.get(
            str(source.id), {}
        )

        args = json.loads(source.args) if source.args else {}
        file_dict = module.file_list_extractor(**args)

        print("Finding Existing Files")
        offset = 0
        existing_names = set()
        while True:
            existing = await db.rawdocument.find_many(
                where={"sourceId": source.id, "is_proof": False},
                include={"text": False},
                take=1000,
                skip=offset,
            )
            if not existing:
                break
            existing_names.update({doc.name for doc in existing})
            offset += 1000

        await remove_proofs(db, source)

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

                for name, info in new_documents.items():
                    try:
                        raw_document_text = module.scraper(info["path"])
                        raw_inserted_document = await db.rawdocument.create(
                            data={
                                "name": name,
                                "text": raw_document_text,
                                "is_proof": info["is_proof"],
                                "sourceId": source.id,
                            }
                        )
                        override = sitting_day_override_for_source.get(
                            raw_inserted_document.name, None
                        )
                        parsed_document = parser(raw_inserted_document.text)
                        for extract in parsed_document:
                            sitting_day = await create_sitting_day(
                                db, extract, override
                            )
                            for document in extract["documents"]:
                                await insert_document(
                                    db,
                                    document,
                                    raw_inserted_document.id,
                                    sitting_day,
                                )
                        progress.advance(task_docs)

                    except Exception as e:
                        print(e)
                        print(name)
                        print(info)
                        raise

        else:
            console.print(f"[dim]No new files for {source.name}[/dim]")

    log("Finished scraping sources.")


async def join_politicians_to_raw_authors(db: Client) -> None:
    log("Joining raw authors to politicians...")
    ignore_ids = fixes["ignore_ids"]

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
                if auth.name not in ignore_ids:
                    console.print(
                        f"[yellow]⚠[/yellow] Could not match: {auth.name} (possible alt name)"
                    )
            progress.advance(task)

    log("Finished joining authors.")


async def reparse_all_sources(db: Client) -> None:
    """Re-parse all existing raw documents."""
    log("Re-parsing all existing raw documents...")

    sitting_day_override = fixes["sitting_day_override"]

    sources = await db.source.find_many()

    await db.query_raw('TRUNCATE "Document" CASCADE;')
    await db.query_raw('TRUNCATE "SittingDay" CASCADE;')

    for source in sources:
        log(f"Re-parsing source: [cyan]{source.name}[/cyan]")

        parser = importlib.import_module(source.parserModule).parse

        raw_documents = await db.rawdocument.find_many(
            where={"sourceId": source.id},
        )

        sitting_day_override_for_source = sitting_day_override.get(
            str(source.id), {}
        )

        with Progress(console=console, transient=False) as progress:
            task_docs = progress.add_task(
                f"[green]Re-parsing {source.name}[/green]",
                total=len(raw_documents),
            )

            for raw_doc in raw_documents:
                try:
                    parsed_document = parser(raw_doc.text)
                    for extract in parsed_document:
                        override = sitting_day_override_for_source.get(
                            raw_doc.name, None
                        )
                        sitting_day = await create_sitting_day(
                            db, extract, override
                        )
                        for document in extract["documents"]:
                            await insert_document(
                                db, document, raw_doc.id, sitting_day
                            )
                except Exception as e:
                    console.print(
                        f"[red]Error re-parsing {raw_doc.name}: {e}[/red]"
                    )
                    raise e
                progress.advance(task_docs)

    log("Finished re-parsing all sources.")


async def check_authors_join(db):

    docs = await db.query_raw("""
    SELECT
        p.id                         AS parliamentarian_id,
        p."firstName"                AS first_name,
        p."lastName"                 AS last_name,

        COUNT(DISTINCT d.id)                  AS outside_speech_count,
        MIN(sd.date)                 AS first_outside_date,
        MAX(sd.date)                 AS last_outside_date,

        MIN(s_all."startDate")       AS min_service_start,
        MAX(s_all."endDate")         AS max_service_end

    FROM "Document" d
    JOIN "SittingDay" sd
        ON d."sittingDayId" = sd.id
    JOIN "rawAuthor" ra
        ON d."rawAuthorId" = ra.id
    JOIN "Parliamentarian" p
        ON ra."parliamentarianId" = p.id

    -- Services that WOULD cover the document date
    LEFT JOIN "Service" s_match
        ON s_match."parliamentarianId" = p.id
       AND s_match."startDate" <= sd.date
       AND (s_match."endDate" IS NULL OR s_match."endDate" >= sd.date)

    -- All services, only for bounds
    LEFT JOIN "Service" s_all
        ON s_all."parliamentarianId" = p.id

    WHERE s_match.id IS NULL 
       AND sd."chamber" <> 'Answers Upon Notice'

    GROUP BY
        p.id,
        p."firstName",
        p."lastName"

    ORDER BY
        outside_speech_count DESC,
        p."lastName";
                               """)

    for doc in docs:
        ignore = [
            x
            for x in fixes["ignore_periods"]
            if x["id"] == doc["parliamentarian_id"]
            and doc["first_outside_date"][:10] >= x["start"]
            and doc["last_outside_date"][:10] <= x["end"]
        ]
        if not ignore:
            console.print(
                f"[yellow]⚠[/yellow] Speeches allocated outside of service window for {doc['first_name']} {doc['last_name']} (ID: {doc['parliamentarian_id']})"
            )
            console.print(
                f"outside speech count: {doc['outside_speech_count']}, first outside date: {doc['first_outside_date'][:10]}, last outside date: {doc['last_outside_date'][:10]}, service window: {doc['min_service_start'][:10]} to {doc['max_service_end'][:10]}"
            )


async def remove_proofs(db, source):

    proof_rawdocs = await db.rawdocument.find_many(
        where={"sourceId": source.id, "is_proof": True}
    )
    proof_ids = [rd.id for rd in proof_rawdocs]

    with Progress(console=console, transient=False) as progress:
        task = progress.add_task("Cleaning Proofs", total=len(proof_ids))

        for id in proof_ids:
            # 1) Fetch documents first
            documents = await db.document.find_many(where={"rawDocumentId": id})

            if documents:
                sitting_day_ids = list({d.sittingDayId for d in documents})

                # 2) Delete documents
                await db.document.delete_many(where={"rawDocumentId": id})

                # 3) Delete sitting days
                await db.sittingday.delete_many(
                    where={"id": {"in": sitting_day_ids}}
                )

            # 4) Delete rawdocument
            await db.rawdocument.delete(where={"id": id})

            progress.advance(task)


async def main():
    parser = argparse.ArgumentParser(description="Run the data pipeline.")
    parser.add_argument(
        "--reparse", action="store_true", help="Re-parse all raw documents."
    )
    args = parser.parse_args()

    console.rule("[bold blue]Pipeline Start")
    db = Client()
    await db.connect()

    await seed_sources(db)
    await reset_politician_links(db)
    await load_politician_metadata(db)

    if args.reparse:
        await reparse_all_sources(db)
    else:
        await scrape_and_parse_sources(db)

    await join_politicians_to_raw_authors(db)
    await check_authors_join(db)

    await db.disconnect()
    console.rule("[bold blue]Pipeline Complete")


if __name__ == "__main__":
    asyncio.run(main())
