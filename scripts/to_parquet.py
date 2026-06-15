#!/usr/bin/env python3
"""
Export documents for a date range to parquet files.

Usage:
    python scripts/to_parquet.py START_DATE END_DATE
    python scripts/to_parquet.py START_DATE END_DATE --include-interjections

Outputs:
    <output>.parquet
    <output>.interjections.parquet (optional)
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import httpx
import pandas as pd
from prisma import Prisma


DOCUMENTS_SQL = """
SELECT
    d.id AS document_id,
    d.text,
    d.title,
    d.type,
    sd.date::date AS date,
    sd.house,
    sd.chamber,
    ra.name AS raw_author_name,
    p.id AS parliamentarian_id,
    p."firstName" AS first_name,
    p."lastName" AS last_name,
    party.name AS party,
    svc.seat,
    svc.state,
    svc."isSenate" AS is_senate,
    svc."parliamentId" AS parliament_id,
    minister.role AS minister_role,
    minister.portfolio AS minister_portfolio,
    minister."displayString" AS minister_display_string,
    ministry.name AS ministry_name,
    ministry."isShadow" AS ministry_is_shadow
FROM "Document" d
JOIN "SittingDay" sd
    ON sd.id = d."sittingDayId"
LEFT JOIN "rawAuthor" ra
    ON ra.id = d."rawAuthorId"
LEFT JOIN "Parliamentarian" p
    ON p.id = ra."parliamentarianId"
LEFT JOIN LATERAL (
    SELECT s.*
    FROM "Service" s
    WHERE s."parliamentarianId" = p.id
      AND s."startDate" <= sd.date
      AND (s."endDate" IS NULL OR s."endDate" >= sd.date)
    ORDER BY s."startDate" DESC, s.id DESC
    LIMIT 1
) svc ON TRUE
LEFT JOIN "Party" party
    ON party.id = svc."partyId"
LEFT JOIN LATERAL (
    SELECT m.*
    FROM "Minister" m
    WHERE m."parliamentarianId" = p.id
      AND m."firstDate" <= sd.date
      AND (m."lastDate" IS NULL OR m."lastDate" >= sd.date)
    ORDER BY m."firstDate" DESC, m.id DESC
    LIMIT 1
) minister ON TRUE
LEFT JOIN "Ministry" ministry
    ON ministry.id = minister."ministryId"
WHERE sd.date >= $1::date
  AND sd.date < ($2::date + INTERVAL '1 day')
ORDER BY sd.date, d.id;
"""

INTERJECTIONS_SQL = """
SELECT
    i.id AS interjection_id,
    i."documentId" AS document_id,
    i.sequence,
    i.type AS interjection_type,
    i.text,
    ra.name AS raw_author_name,
    p.id AS parliamentarian_id,
    p."firstName" AS first_name,
    p."lastName" AS last_name,
    party.name AS party,
    svc.seat,
    svc.state,
    svc."isSenate" AS is_senate,
    svc."parliamentId" AS parliament_id,
    minister.role AS minister_role,
    minister.portfolio AS minister_portfolio,
    minister."displayString" AS minister_display_string,
    ministry.name AS ministry_name,
    ministry."isShadow" AS ministry_is_shadow
FROM "Interjection" i
JOIN "Document" d
    ON d.id = i."documentId"
JOIN "SittingDay" sd
    ON sd.id = d."sittingDayId"
LEFT JOIN "rawAuthor" ra
    ON ra.id = i."rawAuthorId"
LEFT JOIN "Parliamentarian" p
    ON p.id = ra."parliamentarianId"
LEFT JOIN LATERAL (
    SELECT s.*
    FROM "Service" s
    WHERE s."parliamentarianId" = p.id
      AND s."startDate" <= sd.date
      AND (s."endDate" IS NULL OR s."endDate" >= sd.date)
    ORDER BY s."startDate" DESC, s.id DESC
    LIMIT 1
) svc ON TRUE
LEFT JOIN "Party" party
    ON party.id = svc."partyId"
LEFT JOIN LATERAL (
    SELECT m.*
    FROM "Minister" m
    WHERE m."parliamentarianId" = p.id
      AND m."firstDate" <= sd.date
      AND (m."lastDate" IS NULL OR m."lastDate" >= sd.date)
    ORDER BY m."firstDate" DESC, m.id DESC
    LIMIT 1
) minister ON TRUE
LEFT JOIN "Ministry" ministry
    ON ministry.id = minister."ministryId"
WHERE sd.date >= $1::date
  AND sd.date < ($2::date + INTERVAL '1 day')
ORDER BY sd.date, i."documentId", i.sequence, i.id;
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export documents for a date range to parquet."
    )
    parser.add_argument("start_date", help="Start date in YYYY-MM-DD format")
    parser.add_argument("end_date", help="End date in YYYY-MM-DD format")
    parser.add_argument(
        "--output",
        default="documents",
        help="Base output filename written inside the output directory",
    )
    parser.add_argument(
        "--output-dir",
        default="/exports",
        help="Directory to write parquet files to",
    )
    parser.add_argument(
        "--include-interjections",
        action="store_true",
        help="Also export a companion interjections parquet file",
    )
    return parser.parse_args()


def ensure_parquet_suffix(name: str) -> str:
    if name.endswith(".parquet"):
        return name
    return f"{name}.parquet"


def make_interjections_filename(main_filename: str) -> str:
    if main_filename.endswith(".parquet"):
        base = main_filename[:-8]
    else:
        base = main_filename
    return f"{base}.interjections.parquet"


async def fetch_dataframe(db: Prisma, sql: str, start_date: str, end_date: str) -> pd.DataFrame:
    rows = await db.query_raw(sql, start_date, end_date)
    return pd.DataFrame(rows)


async def async_main() -> None:
    args = parse_args()
    main_filename = ensure_parquet_suffix(args.output)
    interjections_filename = make_interjections_filename(main_filename)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    main_output_path = output_dir / main_filename
    interjections_output_path = output_dir / interjections_filename

    db = Prisma(http={"timeout": httpx.Timeout(600.0)})
    await db.connect()
    try:
        documents_df = await fetch_dataframe(db, DOCUMENTS_SQL, args.start_date, args.end_date)
        documents_df.to_parquet(main_output_path, index=False)

        if args.include_interjections:
            interjections_df = await fetch_dataframe(
                db,
                INTERJECTIONS_SQL,
                args.start_date,
                args.end_date,
            )
            interjections_df.to_parquet(interjections_output_path, index=False)
    finally:
        await db.disconnect()


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()

