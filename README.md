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

A database format for the Australian Federal Parliament's Hansard -- the
verbatim transcript of everything said since 1901 in both houses of Parliament.
While all the text is available on ParlInfo, it is notoriously hard to
search and doesn't allow for more complex queries.

This repository offers both a way of combining previous scrapes of the Hansard
and parsing this into a SQL database for future work. This should allow
better access to the Hansard into the future.

## Installation and Setup

The Federal Hansard DB can be used in two ways, directly and through a Prisma  
submodule. For direct analysis of the data, it is recommended that you use the  
database standalone. Instead, for use as part of a dashboard, there are good  
ways to use the Prisma ORM to simplify DB connections and data management.

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

4. **Download the latest Version of the DB**

```{bash}
docker compose run download
```

5. **Connect to the DB**

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

Since the database is set up with Prisma, you can use the built in graphical
tools to look around. First run this command:

```{bash}
docker compose up studio
```

Then go to [[http://localhost:5555]].

The other option is to use the PSQL CLI, which can be accessed by running:

```{bash}
docker compose run -it db_manager
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

4. **Download the latest Version of the DB**

```{bash}
docker compose run download
```

5. **Generate the Prisma Client**

```{bash}
pip install prisma
prisma generate
```

6. **Import and use the ORM**

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

docker volume create  hansard_db_historic_cache
docker compose run update
```

This command is repeatable and will add any sitting days that have not yet been
included already.

### Downloading the DB

To save time and resources building from source, builds of the database can be
downloaded using the download script.

The to scrape and parse these sources - run the following command:

```{bash}
export SYS_DIR=$PWD
docker compose run download
```

### Database Structure

![Database Diagram](RD.svg)

### Fixes

While the point of this database is to present the Hansard and its accompanying
data in its original form, there are some clear mistakes within the XML that
have had to be manually fixed. All of these changes are stored in `fixes.json`.

#### Sitting Day Override

Some documents have the wrong sitting day in their header, leading to parsing
issues down the line. To fix this, a dict is created for each source id and then
the key maps to the document title that is being overwritten, with the value
mapping to the correct sitting date in YYYY-MM-DD format.

#### Preferred Name Update

When trying to join on the names of the politicians, it sometimes occurred that
the nickname used in Hansard was not the one listed in the parliamentary
handbook. In these cases (specifically when it broke the parsing), the preferred
name was updated to reflect this.

#### Alt IDs

Sometimes the speech of parliamentarians is tagged under a PHID that is not part
of the parliamentary handbook API. In these cases, the speaker was identified
through manual inspection and then given an alt id to fix the joins.

#### Party Affiliations

Some politicians lack info in the parliamentary handbook about party
affiliation, leading to issues with parsing and joins. In these cases additional
information was added to ensure working parsing.

#### Ignore IDs

Some ids are not linked to a specific parliamentarian, such as 10000 for the
speaker or others for foreign dignitaries. These ids are identified during the
parsing process to minimise warnings.

## Examples

For more information on example queries, see
[demo](https://github.com/Fonzzy1/federal-hansard-db/tree/main/demo)
