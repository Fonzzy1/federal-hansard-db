[![DOI](https://zenodo.org/badge/1061476911.svg)](https://doi.org/10.5281/zenodo.17783854)

Cite as:

```bib
@misc{chadwick2025,
  doi = {10.5281/ZENODO.17783854},
  url = {https://zenodo.org/doi/10.5281/zenodo.17783854},
  author = {Alfie Chadwick},
  title = {Federal Hansard DB},
  publisher = {Zenodo},
  year = {2025},
  copyright = {Creative Commons Attribution 4.0 International}
}
```

# Federal Hansard DB

Federal Hansard DB is a structured PostgreSQL database of the Australian Federal
Parliament’s Hansard: the verbatim transcript of parliamentary speech in both
houses since 1901.

While the raw text is available through ParlInfo and related archives, it is not
well suited to large-scale search, reproducible analysis, or integration into
research tools and dashboards. This repository provides:

- a reproducible database schema for Hansard data
- scripts to build and update the database from source material
- a downloadable prebuilt database for faster setup
- Prisma support for use inside other applications

## What this repository is for

There are three main ways to use this project:

### 1. Browse the Hansard

If you want to inspect the data, look up speeches, test SQL queries, or explore
the schema, you can run the database locally and connect with:

- Prisma Studio
- `psql`
- DBeaver, DataGrip, TablePlus, or another PostgreSQL client
- R, Python, or any SQL-capable analysis environment

### 2. Integrate it into other tools

If you are building a dashboard, API, website, or data workflow, you can use
this repository as a submodule and access the database through
[Prisma](https://www.prisma.io/). This is the easiest path if you want type-safe
database access inside a larger application.

### 3. Extract slices of Hansard

If you want a subset of the corpus — for example:

- speeches by a particular parliamentarian
- all speeches from a date range
- all documents containing a keyword or phrase
- records linked to a party, chamber, source, or period

— you can run the database locally and query it directly with SQL, R, or Python.

For worked examples, see the [demo](https://github.com/Fonzzy1/federal-hansard-db/tree/main/demo).

---

## Quick start

For most users, the simplest workflow is:

1. Start PostgreSQL with Docker
2. Download the latest prebuilt database
3. Explore it with Prisma Studio or your preferred SQL client

### Clone the repository

```bash
git clone https://github.com/Fonzzy1/federal-hansard-db.git
cd federal-hansard-db
```

### Check Docker is available

```bash
docker --version
docker compose version
```

### Create the required Docker volumes

These volumes persist the database and parser cache between runs.

```bash
docker volume create hansard_db_data
docker volume create hansard_db_historic_cache
```

### Start the database

```bash
docker compose up db -d
```

### Download the latest prebuilt database

```bash
docker compose run --rm download
```

### Connection details

Use these settings in your database client:

```yaml
Host: localhost
Port: 5432
Username: prisma_user
Password: prisma_password
Database: prisma_db
```

Connection URL:

```bash
DATABASE_URL=postgresql://prisma_user:prisma_password@localhost:5432/prisma_db?schema=public
```

---

## Browsing the database

The easiest way to browse the Hansard in this repository is through the included
frontend.

### Option A: Built-in frontend

Start the frontend with:

```bash
docker compose up frontend
```

Then open:

```text
http://localhost:8000
```

This is the best option if you want to browse speeches and navigate the data in
a more user-friendly way than working directly with SQL tables.

### Option B: Prisma Studio

Prisma Studio gives you a graphical view of the database tables and records.

Start it with:

```bash
docker compose up studio
```

Then open:

```text
http://localhost:5555
```

This is useful for inspecting the schema and underlying row-level data, but it
is primarily a database viewer rather than a Hansard reading interface.

### Option C: psql

For direct SQL access from the command line:

```bash
docker compose run --rm -it db_manager
```

This opens a `psql` session inside the container, already configured to connect
to the database.

### Option D: external database clients

You can also connect using any PostgreSQL GUI client, such as:

- DBeaver
- DataGrip
- TablePlus
- pgAdmin

Use the connection details listed above.

## Integrating into other tools

This repository can also be used as a Git submodule inside a larger project. If
you want to build an app or service on top of the database, this is usually the
best approach.

Because the schema is managed with Prisma, you can generate a Prisma client for
application use.

### Add as a submodule

```bash
git submodule add https://github.com/Fonzzy1/federal-hansard-db.git path/to/submodule
git submodule update --init --recursive
```

### Start the database from the submodule

```bash
cd path/to/submodule
docker volume create hansard_db_data
docker volume create hansard_db_historic_cache
docker compose up db -d
docker compose run --rm download
```

### Generate the Prisma client

For Python:

```bash
pip install prisma
prisma generate
```

Example usage:

```python
from prisma import Client

db = Client()

await db.connect()
```

If you are working in JavaScript or TypeScript, use the standard Prisma client
workflow in your host project.

---

## Extracting slices of Hansard

One of the main reasons to use this database is to create targeted extracts of
Hansard for analysis.

Typical use cases include:

- retrieving all speeches by a member
- extracting all speeches in a particular chamber
- collecting debate text over a specific time period
- searching for mentions of particular issues or phrases
- linking speech to party, role, or service history

You can do this with SQL directly, or through R/Python database libraries.

### Example: speeches mentioning a phrase

```sql
SELECT
  id,
  date,
  title,
  text
FROM "Document"
WHERE text ILIKE '%climate change%'
ORDER BY date;
```

### Example: speeches in a date range

```sql
SELECT
  id,
  date,
  title
FROM "Document"
WHERE date BETWEEN '2020-01-01' AND '2020-12-31'
ORDER BY date;
```

### Example: speeches by a parliamentarian

```sql
SELECT
  d.id,
  d.date,
  d.title,
  d.text
FROM "Document" d
JOIN "rawAuthor" ra ON d."rawAuthorId" = ra.id
JOIN "Parliamentarian" p ON ra."parliamentarianId" = p.id
WHERE p."displayName" ILIKE '%albanese%'
ORDER BY d.date;
```

For larger examples in R, including visualisation workflows, see
[`demo/README.qmd`](./demo/README.qmd).

---

## Building or updating the database

The database can be populated in two ways:

1. **Download a prebuilt copy** using the `download` script
2. **Build/update from source** using the parser

The database ships empty except for the schema. You must either download a built
copy or populate it yourself.

### Download the latest database

This is the fastest option and is recommended for most users.

```bash
docker compose run --rm download
```

### Build or update from source

The parser pulls Hansard content from two upstream sources:

- [Historic Hansard](https://github.com/wragge/hansard-xml) for pre-2000 content
- Parli Info

To build or incrementally update the database:

```bash
docker volume create hansard_db_historic_cache
docker volume create hansard_db_data
docker compose run --rm update
```

This command is repeatable. It adds sitting days not already present in the
database.

### Reparse existing data

If parsing logic changes and you need to rebuild parsed records from the source
material:

```bash
docker compose run --rm reparse
```

---

## Database management

The `docker-compose.yml` file defines several services for database access and
maintenance.

### Core services

- `db`: PostgreSQL database
- `db_manager`: interactive `psql` access and shared management environment

### Data workflows

- `download`: download and load the latest prebuilt database
- `update`: fetch and parse source data into the database
- `reparse`: rerun parsing against existing source inputs
- `upload`: upload a built database artifact

### User-facing tools

- `studio`: launch Prisma Studio on port `5555`
- `frontend`: launch the included FastAPI frontend on port `8000`

### Notes on volumes

Two external Docker volumes are expected:

- `hansard_db_data`: persistent PostgreSQL data
- `hansard_db_historic_cache`: cached source material used during parsing

Because these are marked as `external: true`, you should create them before
first use:

```bash
docker volume create hansard_db_data
docker volume create hansard_db_historic_cache
```

### Stop the database

```bash
docker compose stop db
```

### Remove containers but keep data

```bash
docker compose down
```

### Remove the database volume entirely

```bash
docker volume rm hansard_db_data
```

Only do this if you want to delete the stored database.

---

## Database structure

![Database Diagram](RD.svg)

---

## Data corrections and manual fixes

The goal of this project is to preserve Hansard and associated metadata as
faithfully as possible. However, some upstream records contain errors or missing
information that prevent reliable parsing or joins. These corrections are stored
in `fixes.json`.

### Sitting day override

Some documents have an incorrect sitting day in their header. In these cases, a
mapping is provided from source identifier and document title to the corrected
date in `YYYY-MM-DD` format.

### Preferred name update

Some politicians are referred to in Hansard by a preferred name or nickname that
does not match the parliamentary handbook record closely enough for reliable
joining. Where necessary, the preferred name is adjusted to support parsing.

### Alt IDs

Some speeches are tagged with a PHID not present in the parliamentary handbook
API. In those cases, the speaker is identified manually and linked through an
alternate ID.

### Party affiliations

Some parliamentarians are missing party information in the handbook data. Extra
information is supplied where needed to keep parsing and joins working.

### Ignore IDs

Some identifiers do not refer to a specific parliamentarian, such as special
speaker IDs or foreign dignitaries. These are explicitly ignored to reduce
parsing noise and warnings.

---

## Examples

For example analysis workflows and queries, see:

- [demo](https://github.com/Fonzzy1/federal-hansard-db/tree/main/demo)

---

## Citation

If you use this database in research, please cite the Zenodo record above. A paper on the development process is in progress and will hopefully be available (In at least pre-print form) by mid-2026.
