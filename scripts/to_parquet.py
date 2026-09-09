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
WITH base AS (
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
        p."lastName" AS last_name
    FROM "Document" d
    JOIN "SittingDay" sd
        ON sd.id = d."sittingDayId"
    LEFT JOIN "rawAuthor" ra
        ON ra.id = d."rawAuthorId"
    LEFT JOIN "Parliamentarian" p
        ON p.id = ra."parliamentarianId"
    WHERE sd.date >= $1::date
      AND sd.date < ($2::date + INTERVAL '1 day')
),
author_dates AS (
    SELECT DISTINCT
        parliamentarian_id,
        date
    FROM base
    WHERE parliamentarian_id IS NOT NULL
),
service_for_date AS (
    SELECT
        ad.parliamentarian_id,
        ad.date,
        svc.id AS service_id,
        svc.seat,
        svc.state,
        svc."isSenate" AS is_senate,
        svc."parliamentId" AS parliament_id,
        party.name AS party
    FROM author_dates ad
    LEFT JOIN LATERAL (
        SELECT s.*
        FROM "Service" s
        WHERE s."parliamentarianId" = ad.parliamentarian_id
          AND s."startDate" <= ad.date
          AND (s."endDate" IS NULL OR s."endDate" >= ad.date)
        ORDER BY s."startDate" DESC, s.id DESC
        LIMIT 1
    ) svc ON TRUE
    LEFT JOIN "Party" party
        ON party.id = svc."partyId"
),
minister_for_date AS (
    SELECT
        ad.parliamentarian_id,
        ad.date,
        minister.role AS minister_role,
        minister.portfolio AS minister_portfolio,
        minister."displayString" AS minister_display_string,
        ministry.name AS ministry_name,
        ministry."isShadow" AS ministry_is_shadow
    FROM author_dates ad
    LEFT JOIN LATERAL (
        SELECT m.*
        FROM "Minister" m
        WHERE m."parliamentarianId" = ad.parliamentarian_id
          AND m."firstDate" <= ad.date
          AND (m."lastDate" IS NULL OR m."lastDate" >= ad.date)
        ORDER BY m."firstDate" DESC, m.id DESC
        LIMIT 1
    ) minister ON TRUE
    LEFT JOIN "Ministry" ministry
        ON ministry.id = minister."ministryId"
)
SELECT
    b.document_id,
    b.text,
    b.title,
    b.type,
    b.date,
    b.house,
    b.chamber,
    b.raw_author_name,
    b.parliamentarian_id,
    b.first_name,
    b.last_name,
    sfd.party,
    sfd.seat,
    sfd.state,
    sfd.is_senate,
    sfd.parliament_id,
    mfd.minister_role,
    mfd.minister_portfolio,
    mfd.minister_display_string,
    mfd.ministry_name,
    mfd.ministry_is_shadow
FROM base b
LEFT JOIN service_for_date sfd
    ON sfd.parliamentarian_id = b.parliamentarian_id
   AND sfd.date = b.date
LEFT JOIN minister_for_date mfd
    ON mfd.parliamentarian_id = b.parliamentarian_id
   AND mfd.date = b.date
ORDER BY b.date, b.document_id;

"""

INTERJECTIONS_SQL = """
WITH base AS (
    SELECT
        i.id AS interjection_id,
        i."documentId" AS document_id,
        i.sequence,
        i.type AS interjection_type,
        i.text,
        sd.date::date AS date,
        ra.name AS raw_author_name,
        p.id AS parliamentarian_id,
        p."firstName" AS first_name,
        p."lastName" AS last_name
    FROM "Interjection" i
    JOIN "Document" d
        ON d.id = i."documentId"
    JOIN "SittingDay" sd
        ON sd.id = d."sittingDayId"
    LEFT JOIN "rawAuthor" ra
        ON ra.id = i."rawAuthorId"
    LEFT JOIN "Parliamentarian" p
        ON p.id = ra."parliamentarianId"
    WHERE sd.date >= $1::date
      AND sd.date < ($2::date + INTERVAL '1 day')
),
author_dates AS (
    SELECT DISTINCT
        parliamentarian_id,
        date
    FROM base
    WHERE parliamentarian_id IS NOT NULL
),
service_for_date AS (
    SELECT
        ad.parliamentarian_id,
        ad.date,
        svc.id AS service_id,
        svc.seat,
        svc.state,
        svc."isSenate" AS is_senate,
        svc."parliamentId" AS parliament_id,
        party.name AS party
    FROM author_dates ad
    LEFT JOIN LATERAL (
        SELECT s.*
        FROM "Service" s
        WHERE s."parliamentarianId" = ad.parliamentarian_id
          AND s."startDate" <= ad.date
          AND (s."endDate" IS NULL OR s."endDate" >= ad.date)
        ORDER BY s."startDate" DESC, s.id DESC
        LIMIT 1
    ) svc ON TRUE
    LEFT JOIN "Party" party
        ON party.id = svc."partyId"
),
minister_for_date AS (
    SELECT
        ad.parliamentarian_id,
        ad.date,
        minister.role AS minister_role,
        minister.portfolio AS minister_portfolio,
        minister."displayString" AS minister_display_string,
        ministry.name AS ministry_name,
        ministry."isShadow" AS ministry_is_shadow
    FROM author_dates ad
    LEFT JOIN LATERAL (
        SELECT m.*
        FROM "Minister" m
        WHERE m."parliamentarianId" = ad.parliamentarian_id
          AND m."firstDate" <= ad.date
          AND (m."lastDate" IS NULL OR m."lastDate" >= ad.date)
        ORDER BY m."firstDate" DESC, m.id DESC
        LIMIT 1
    ) minister ON TRUE
    LEFT JOIN "Ministry" ministry
        ON ministry.id = minister."ministryId"
)
SELECT
    b.interjection_id,
    b.document_id,
    b.sequence,
    b.interjection_type,
    b.text,
    b.raw_author_name,
    b.parliamentarian_id,
    b.first_name,
    b.last_name,
    sfd.party,
    sfd.seat,
    sfd.state,
    sfd.is_senate,
    sfd.parliament_id,
    mfd.minister_role,
    mfd.minister_portfolio,
    mfd.minister_display_string,
    mfd.ministry_name,
    mfd.ministry_is_shadow
FROM base b
LEFT JOIN service_for_date sfd
    ON sfd.parliamentarian_id = b.parliamentarian_id
   AND sfd.date = b.date
LEFT JOIN minister_for_date mfd
    ON mfd.parliamentarian_id = b.parliamentarian_id
   AND mfd.date = b.date
ORDER BY b.date, b.document_id, b.sequence, b.interjection_id;

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

