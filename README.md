# Federal Hansard DB

A database format for the Australian Federal Parliament's Hansard -- the
verbatim transcript of everything said since 1901 in both houses of Parliament. 
While all of the text is available on ParlInfo, it is notoriously hard to
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
docker-compose --version
```

3. **Start the Container**

```{bash}
docker-compose up db -d
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
docker-compose --version
```

3. **Start the DB**

```{bash}
cd path/to/submodule
docker-compose up db -d
```

2. **Generate the Prisma Client**

```{bash}
pip install prisma
prisma generate
```

## Usage

## Support

## Expansion
