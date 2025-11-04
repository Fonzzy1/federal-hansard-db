# Federal Hansard DB

A database format for the Australian Federal Parliament's Hansard -- the
verbatim transcript of everything said since 1901 in both houses of Parliament.
While all the text is available on ParlInfo, it is notoriously hard to
search and doesn't allow for more complex queries.

This repository offers both a way of combining previous scrapes of the Hansard
and parsing this into a SQL database for future work. This should allow
better access to the Hansard into the future.

## Installation and Setup

The Federal Hansard DB can be used in two ways:

---

### Option 1: Run Standalone with Docker Compose

1. **Clone the repository**

```bash
git clone https://github.com/Fonzzy1/federal-hansard-db.git
cd federal-hansard-db
```

2. **Ensure Docker and Docker Compose are installed**

```{bash}
docker --version
```

3. **Start the Container**

```{bash}
docker compose up db -d
```

4. **Connect to the DB**

Using the DB connector of your choice, set up the following connection
parameters

```{yaml}
Port: 5432
Username: prisma_user
Password: prisma_password
Database: prisma_db
```

```{bash}

DATABASE_URL=postgresql://prisma_user:prisma_password@localhost:5432/prisma_db?schema=public
```

1. **Use Prisma Studio**

To use the built in db GUI, run:

```{bash}
docker compose up studio
```

---

### Option 2: As a submodule with Prisma

This database is built on top of [Prisma](https://www.prisma.io/), which acts as
a Python and JS ORM for easier access and integration. To make use of this, it
is recommended that the database is initialised as a git submodule.

1. **Add the Submodule**

```{bash}
git submodule add https://github.com/Fonzzy1/federal-hansard-db.git path/to/submodule
git submodule update --init --recursive
```

2. **Ensure Docker and Docker Compose are installed**

```{bash}
docker --version
```

3. **Start the DB**

```{bash}
cd path/to/submodule
docker compose up db -d
```

4. **Generate the Prisma Client**

```{bash}
pip install prisma
prisma generate
```

5. **Import and use the ORM**

```{py}
from prisma import Client

db = Client()

await db.connect()
```

## Usage

The database comes empty with just the table format.

### Building the DB from source

The database is designed to pull in information from two existing scrapes:
[Historic Hansard](https://github.com/wragge/hansard-xml) and
[OpenAustralia](http://data.openaustralia.org.au/), which provide the pre-2005
and post 2005 content respectively.

The to scrape and parse these sources - run the following command:

```{bash}
docker compose run update
```

This command is repeatable and will add any sitting days that have not yet been
included already.

### Downloading the DB

To save time and resources building from source, builds of the database can be
downloaded using the download script. To access this, contact
alfie.chadwick@monash.edu to obtain the download credentials, which will be in
the form of a client.json file.

The to scrape and parse these sources - run the following command:

```{bash}
export SYS_DIR=$PWD
docker compose run download
```

### Database Structure

![Database Diagram](RD.svg)

---

#### 🗂 **Source**

Represents a _source of raw documents_ (e.g., a scraper or parser for a website, archive, or dataset).

| Field           | Description                                                                       |
| --------------- | --------------------------------------------------------------------------------- |
| `id`            | Unique identifier for the source.                                                 |
| `name`          | Name of the source (must be unique).                                              |
| `parserModule`  | Name of the Python module used to parse data from this source.                    |
| `scraperModule` | Name of the Python module used to scrape or fetch data.                           |
| `args`          | Additional arguments passed to the scraper/parser modules.                        |
| `dateAdded`     | Timestamp for when the source was first added.                                    |
| `dateModified`  | Automatically updated timestamp for last modification.                            |
| `rawDocuments`  | One-to-many relationship: all `RawDocument` entries originating from this source. |
| `groups`        | Many-to-many relationship linking this source to one or more `SourceGroup`s.      |

---

### 🧩 **SourceGroup**

Groups related sources together, used when I want to get all documents from a group, for example, all senate speeches.

| Field                        | Description                                                       |
| ---------------------------- | ----------------------------------------------------------------- |
| `id`                         | Unique identifier.                                                |
| `name`                       | Name of the source group (must be unique).                        |
| `dateAdded` / `dateModified` | Metadata timestamps.                                              |
| `sources`                    | Many-to-many relationship: all `Source`s belonging to this group. |

---

### 📄 **RawDocument**

Represents _unprocessed documents_ collected from a given `Source`.

| Field                        | Description                                                                            |
| ---------------------------- | -------------------------------------------------------------------------------------- |
| `id`                         | Unique identifier.                                                                     |
| `name`                       | Name or identifier of the raw document (unique per source).                            |
| `text`                       | Full text of the raw document.                                                         |
| `sourceId`                   | Foreign key linking to the `Source` it originated from.                                |
| `dateAdded` / `dateModified` | Metadata timestamps.                                                                   |
| `documents`                  | One-to-many relationship: processed `Document` records derived from this raw document. |

---

### 📑 **Document**

Represents a _processed and parsed document_, derived from a RawDocument.

| Field                        | Description                                                                         |
| ---------------------------- | ----------------------------------------------------------------------------------- |
| `id`                         | Unique identifier.                                                                  |
| `text`                       | Cleaned or structured text from the raw document.                                   |
| `date`                       | Original publication or event date of the document.                                 |
| `title`                        | Title of the Document.                                               |
| `type`                       | Type/category of the document.                    |
| `rawDocumentId`              | Foreign key to the originating `RawDocument`.                                       |
| `rawAuthorId`                | Foreign key linking to the `rawAuthor`.                                             |
| `citedBy` / `references`     | Self-referential many-to-many relation indicating document citations or references. |
| `dateAdded` / `dateModified` | Metadata timestamps.                                                                |

---

### ✍️ **rawAuthor**

Represents an _unmatched or raw author name_ extracted from documents before being linked (if possible) to a verified `Parliamentarian`.

| Field                        | Description                                                       |
| ---------------------------- | ----------------------------------------------------------------- |
| `id`                         | Unique identifier.                                                |
| `name`                       | Name string of the raw author (must be unique).                   |
| `parliamentarianId`          | Optional link to a verified `Parliamentarian`.                    |
| `Document`                   | One-to-many relationship: all `Document`s written by this author. |
| `dateAdded` / `dateModified` | Metadata timestamps.                                              |

---

### 🧑‍⚖️ **Parliamentarian**

Represents an _individual member of parliament_, including their identifying details and service history.

| Field                                    | Description                                                                 |
| ---------------------------------------- | --------------------------------------------------------------------------- |
| `id`                                     | Persistent unique identifier.                                               |
| `altId`                                  | Array of alternative IDs (for legacy systems or cross-references).          |
| `firstName` / `lastName` / `middleNames` | Personal name details.                                                      |
| `altName`                                | Alternative or informal name.                                               |
| `firstNations`                           | Boolean indicating First Nations identification.                            |
| `image`                                  | Path or URL to a portrait image.                                            |
| `gender`                                 | Integer code for gender.                                                    |
| `dob`                                    | Date of birth (optional).                                                   |
| `services`                               | One-to-many relationship: all `Service` records for this person.            |
| `rawAuthors`                             | One-to-many relationship linking raw author entries matched to this person. |
| `dateAdded` / `dateModified`             | Metadata timestamps.                                                        |

---

### 🏛️ **Service**

Represents a _specific parliamentary service period_ for a parliamentarian, this
is the unique combination of parliamentarian, party, and parliament.

| Field                        | Description                                                                                         |
| ---------------------------- | --------------------------------------------------------------------------------------------------- |
| `id`                         | Unique identifier.                                                                                  |
| `startDate` / `endDate`      | Period of service.                                                                                  |
| `isSenate`                   | Boolean indicating whether the service is in the Senate (true) or House of Representatives (false). |
| `seat`                       | Optional seat name or title.                                                                        |
| `state`                      | State or territory of representation.                                                               |
| `parliamentarianId`          | Foreign key to the `Parliamentarian`.                                                               |
| `parliamentId`               | Foreign key to the `Parliament` during which the service occurred.                                  |
| `partyId`                    | Foreign key to the associated `Party`.                                                              |
| `dateAdded` / `dateModified` | Metadata timestamps.                                                                                |

---

### 🏛 **Parliament**

Represents a _specific Parliament term_ (e.g., the 46th Parliament).

| Field                        | Description                                                                      |
| ---------------------------- | -------------------------------------------------------------------------------- |
| `id`                         | Unique identifier.                                                               |
| `firstDate` / `lastDate`     | Dates marking the beginning and end of the parliamentary term.                   |
| `services`                   | One-to-many relationship: all `Service`s that took place during this parliament. |
| `dateAdded` / `dateModified` | Metadata timestamps.                                                             |

---

### 🏴 **Party**

Represents a _political party_.

| Field      | Description                                                          |
| ---------- | -------------------------------------------------------------------- |
| `id`       | Unique identifier.                                                   |
| `name`     | Name of the party (must be unique).                                  |
| `services` | One-to-many relationship: all `Service`s associated with this party. |

## Expansion

The database is designed with expansion in mind. While Hansard data is the
primary concern, including other sources such as tweets or press releases should
be fairly straightforward.

### Sources

To add an additional source, you would add a new row to the `Source` table.
As part of this, you will need to build a scraper, and a parser.

### Scrapers

Scraper modules will have two functions: `file_list_extractor(**args)` and
`scraper(file)`.

`file_list_extractor` returns a dict of file names and paths, while
`scraper(file)`
will take in a file path and return the raw text of the file.

### Parsers

Parser modules have a single exportable function: `parse(file_text)`, taking the
raw text from a file and producing documents, which is a list of dicts each with
a `date`, `type`, `text` and `author`.

### RawAuthors and Joins

To join the authors from the documents to parliamentarians, you can add more
content to fixes.json. Politicians are joined to authors on `id` and `altId`; to
ensure the join works, make sure that the alt_id for the parliamentarian is set
in fixes.json.

## Examples

### Big Query

To pull out all the row-wise information for the documents through various
joins:

```{sql connection = "con" }

SELECT
    doc.*,
    rau.*,
    par.*,
    svc.*,
    prt.*
FROM
    "Document" doc
JOIN
    "rawAuthor" rau ON doc."rawAuthorId" = rau.id
JOIN
    "Parliamentarian" par ON rau."parliamentarianId" = par.id
JOIN
    "Service" svc ON par.id = svc."parliamentarianId"
    AND doc."date" BETWEEN svc."startDate" AND svc."endDate"
JOIN
    "Party" prt ON prt.id = svc."partyId"

```
