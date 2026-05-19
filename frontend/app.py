from contextlib import asynccontextmanager

import html
import re
from urllib.parse import urlencode

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from prisma import Prisma

db = Prisma()
templates = Jinja2Templates(directory="frontend/templates")

PAGE_SIZE = 10


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    try:
        yield
    finally:
        await db.disconnect()


app = FastAPI(lifespan=lifespan)


def build_query_string(**params) -> str:
    clean = {k: v for k, v in params.items() if v not in (None, "", [])}
    return urlencode(clean)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def build_day_url(day) -> str:
    return f"/day/{day.date.isoformat()}/{slugify(day.house)}/{slugify(day.chamber)}"


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    house: str | None = Query(default=None),
    chamber: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
):
    where = {}
    if house:
        where["house"] = house
    if chamber:
        where["chamber"] = chamber

    skip = (page - 1) * PAGE_SIZE

    days = await db.sittingday.find_many(
        where=where if where else None,
        order=[
            {"date": "desc"},
            {"house": "asc"},
            {"chamber": "asc"},
        ],
        skip=skip,
        take=PAGE_SIZE,
    )

    houses_raw = await db.sittingday.find_many(
        distinct=["house"],
        order={"house": "asc"},
    )
    chambers_raw = await db.sittingday.find_many(
        distinct=["chamber"],
        order={"chamber": "asc"},
    )

    houses = [d.house for d in houses_raw]
    chambers = [d.chamber for d in chambers_raw]

    items = [
        {
            "url": build_day_url(day),
            "date": day.date,
            "house": day.house,
            "chamber": day.chamber,
            "parliament": day.parliament,
            "session": day.session,
            "period": day.period,
        }
        for day in days
    ]

    has_prev = page > 1
    has_next = len(items) == PAGE_SIZE

    prev_query = build_query_string(
        house=house,
        chamber=chamber,
        page=page - 1 if has_prev else None,
    )
    next_query = build_query_string(
        house=house,
        chamber=chamber,
        page=page + 1 if has_next else None,
    )

    return templates.TemplateResponse(
        request=request,
        name="index.html_template",
        context={
            "days": items,
            "houses": houses,
            "chambers": chambers,
            "selected_house": house,
            "selected_chamber": chamber,
            "page": page,
            "page_size": PAGE_SIZE,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_url": f"/?{prev_query}" if has_prev else None,
            "next_url": f"/?{next_query}" if has_next else None,
        },
    )


@app.get(
    "/day/{date_str}/{house_slug}/{chamber_slug}", response_class=HTMLResponse
)
async def day_view(
    request: Request,
    date_str: str,
    house_slug: str,
    chamber_slug: str,
):
    candidates = await db.sittingday.find_many(
        where={"date": date_str},
        include={
            "documents": {
                "include": {
                    "rawAuthor": {
                        "include": {
                            "parliamentarian": True,
                        }
                    },
                    "references": True,
                    "citedBy": True,
                }
            },
        },
    )

    day = next(
        (
            d
            for d in candidates
            if slugify(d.house) == house_slug
            and slugify(d.chamber) == chamber_slug
        ),
        None,
    )

    if not day:
        raise HTTPException(status_code=404, detail="Sitting day not found")

    doc_ids = [doc.id for doc in day.documents]

    raw_doc = None
    if day.documents:
        raw_doc = await db.rawdocument.find_unique(
            where={"id": day.documents[0].rawDocumentId}
        )

    interjection_rows = await db.interjection.find_many(
        where={"documentId": {"in": doc_ids}} if doc_ids else None,
        include={
            "rawAuthor": {
                "include": {
                    "parliamentarian": True,
                }
            },
            "document": True,
        },
    )

    interjections_by_doc = {}
    for i in interjection_rows:
        interjections_by_doc.setdefault(i.documentId, []).append(i)

    documents = []

    for doc in day.documents:
        paired_ids = []
        paired_ids.extend([r.id for r in doc.references])
        paired_ids.extend([c.id for c in doc.citedBy])

        seen = set()
        deduped_paired_ids = []
        for pid in paired_ids:
            if pid not in seen:
                seen.add(pid)
                deduped_paired_ids.append(pid)

        doc_interjections = interjections_by_doc.get(doc.id, [])

        interjections = sorted(
            [
                {
                    "id": i.id,
                    "sequence": i.sequence,
                    "type": i.type,
                    "text": i.text,
                    "speaker": (
                        i.rawAuthor.parliamentarian.firstName
                        + " "
                        + i.rawAuthor.parliamentarian.lastName
                        if i.rawAuthor and i.rawAuthor.parliamentarian
                        else "Unknown speaker"
                    ),
                }
                for i in doc_interjections
            ],
            key=lambda x: (x["sequence"], x["id"]),
        )

        interjections_by_sequence = {
            interjection["sequence"]: interjection
            for interjection in interjections
        }

        def replace_interjection(match):
            sequence = int(match.group(1))
            interjection = interjections_by_sequence.get(sequence)
            if not interjection:
                return match.group(0)

            speaker = interjection["speaker"] or "Unknown speaker"
            text = interjection["text"] or ""

            safe_speaker = html.escape(speaker, quote=True)
            safe_text = html.escape(text, quote=True)

            return (
                f'<span class="interjection" '
                f'data-speaker="{safe_speaker}" '
                f'data-text="{safe_text}" '
                f'tabindex="0">'
                f"[{ {1: 'SPEAKER', 2: 'GENERAL', 3: 'OFFICE'}.get(interjection['type'], '') } INTERJECTION]"
                f"</span>"
            )

        rendered_text = re.sub(
            r"\[INTERJECTION(\d+)\]",
            replace_interjection,
            doc.text or "",
        )

        documents.append(
            {
                "id": doc.id,
                "title": doc.title,
                "type": doc.type,
                "rendered_text": rendered_text,
                "speaker": (
                    f"{doc.rawAuthor.parliamentarian.firstName} {doc.rawAuthor.parliamentarian.lastName}"
                    if doc.rawAuthor and doc.rawAuthor.parliamentarian
                    else "Unknown speaker"
                ),
                "paired_ids": deduped_paired_ids,
                "interjections": interjections,
            }
        )

    documents.sort(key=lambda x: x["id"])

    groups = []
    current_group = None

    for doc in documents:
        if current_group is None or current_group["title"] != doc["title"]:
            current_group = {
                "title": doc["title"],
                "documents": [],
            }
            groups.append(current_group)

        current_group["documents"].append(doc)

    return templates.TemplateResponse(
        request=request,
        name="day.html",
        context={
            "day": day,
            "groups": groups,
            "raw_doc": raw_doc.text if raw_doc else "",
        },
    )
