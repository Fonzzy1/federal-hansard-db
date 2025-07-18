/*
  Warnings:

  - Added the required column `dateModified` to the `Author` table without a default value. This is not possible if the table is not empty.
  - Added the required column `dateModified` to the `Claim` table without a default value. This is not possible if the table is not empty.
  - Added the required column `extractor_id` to the `Claim` table without a default value. This is not possible if the table is not empty.
  - Added the required column `dateModified` to the `Deconstruction` table without a default value. This is not possible if the table is not empty.
  - Added the required column `deconstructor_id` to the `Deconstruction` table without a default value. This is not possible if the table is not empty.
  - Added the required column `dateModified` to the `Dimension` table without a default value. This is not possible if the table is not empty.
  - Added the required column `dateModified` to the `Document` table without a default value. This is not possible if the table is not empty.
  - Added the required column `dateModified` to the `Infrastructure` table without a default value. This is not possible if the table is not empty.
  - Added the required column `dateModified` to the `InfrastructureGroup` table without a default value. This is not possible if the table is not empty.
  - Added the required column `dateModified` to the `Issue` table without a default value. This is not possible if the table is not empty.
  - Added the required column `dateModified` to the `Parliamentarian` table without a default value. This is not possible if the table is not empty.
  - Added the required column `dateModified` to the `Source` table without a default value. This is not possible if the table is not empty.
  - Added the required column `dateModified` to the `SourceGroup` table without a default value. This is not possible if the table is not empty.

*/
-- CreateTable
CREATE TABLE "Extractor" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "details" TEXT
);

-- CreateTable
CREATE TABLE "Deconstructor" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "details" TEXT
);

-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Author" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);
INSERT INTO "new_Author" ("id", "name") SELECT "id", "name" FROM "Author";
DROP TABLE "Author";
ALTER TABLE "new_Author" RENAME TO "Author";
CREATE TABLE "new_Claim" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "text" TEXT NOT NULL,
    "documentid" INTEGER NOT NULL,
    "issueid" INTEGER NOT NULL,
    "extractor_id" INTEGER NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    CONSTRAINT "Claim_documentid_fkey" FOREIGN KEY ("documentid") REFERENCES "Document" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Claim_issueid_fkey" FOREIGN KEY ("issueid") REFERENCES "Issue" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Claim_extractor_id_fkey" FOREIGN KEY ("extractor_id") REFERENCES "Extractor" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Claim" ("documentid", "id", "issueid", "text") SELECT "documentid", "id", "issueid", "text" FROM "Claim";
DROP TABLE "Claim";
ALTER TABLE "new_Claim" RENAME TO "Claim";
CREATE TABLE "new_Deconstruction" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "claimId" INTEGER NOT NULL,
    "infrastructureId" INTEGER NOT NULL,
    "valence" INTEGER NOT NULL,
    "dimensionId" INTEGER,
    "deconstructor_id" INTEGER NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    CONSTRAINT "Deconstruction_claimId_fkey" FOREIGN KEY ("claimId") REFERENCES "Claim" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Deconstruction_infrastructureId_fkey" FOREIGN KEY ("infrastructureId") REFERENCES "Infrastructure" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Deconstruction_dimensionId_fkey" FOREIGN KEY ("dimensionId") REFERENCES "Dimension" ("id") ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT "Deconstruction_deconstructor_id_fkey" FOREIGN KEY ("deconstructor_id") REFERENCES "Deconstructor" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Deconstruction" ("claimId", "dimensionId", "id", "infrastructureId", "valence") SELECT "claimId", "dimensionId", "id", "infrastructureId", "valence" FROM "Deconstruction";
DROP TABLE "Deconstruction";
ALTER TABLE "new_Deconstruction" RENAME TO "Deconstruction";
CREATE UNIQUE INDEX "Deconstruction_claimId_deconstructor_id_key" ON "Deconstruction"("claimId", "deconstructor_id");
CREATE TABLE "new_Dimension" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);
INSERT INTO "new_Dimension" ("id", "name") SELECT "id", "name" FROM "Dimension";
DROP TABLE "Dimension";
ALTER TABLE "new_Dimension" RENAME TO "Dimension";
CREATE UNIQUE INDEX "Dimension_name_key" ON "Dimension"("name");
CREATE TABLE "new_Document" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "text" TEXT NOT NULL,
    "date" DATETIME NOT NULL,
    "url" TEXT,
    "authorId" INTEGER NOT NULL,
    "sourceId" INTEGER NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    CONSTRAINT "Document_authorId_fkey" FOREIGN KEY ("authorId") REFERENCES "Author" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Document_sourceId_fkey" FOREIGN KEY ("sourceId") REFERENCES "Source" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Document" ("authorId", "date", "id", "sourceId", "text", "url") SELECT "authorId", "date", "id", "sourceId", "text", "url" FROM "Document";
DROP TABLE "Document";
ALTER TABLE "new_Document" RENAME TO "Document";
CREATE TABLE "new_Infrastructure" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);
INSERT INTO "new_Infrastructure" ("id", "name") SELECT "id", "name" FROM "Infrastructure";
DROP TABLE "Infrastructure";
ALTER TABLE "new_Infrastructure" RENAME TO "Infrastructure";
CREATE UNIQUE INDEX "Infrastructure_name_key" ON "Infrastructure"("name");
CREATE TABLE "new_InfrastructureGroup" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);
INSERT INTO "new_InfrastructureGroup" ("id", "name") SELECT "id", "name" FROM "InfrastructureGroup";
DROP TABLE "InfrastructureGroup";
ALTER TABLE "new_InfrastructureGroup" RENAME TO "InfrastructureGroup";
CREATE UNIQUE INDEX "InfrastructureGroup_name_key" ON "InfrastructureGroup"("name");
CREATE TABLE "new_Issue" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dimensionid" INTEGER NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    CONSTRAINT "Issue_dimensionid_fkey" FOREIGN KEY ("dimensionid") REFERENCES "Dimension" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Issue" ("dimensionid", "id", "name") SELECT "dimensionid", "id", "name" FROM "Issue";
DROP TABLE "Issue";
ALTER TABLE "new_Issue" RENAME TO "Issue";
CREATE TABLE "new_Parliamentarian" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "party" TEXT NOT NULL,
    "seat" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    CONSTRAINT "Parliamentarian_id_fkey" FOREIGN KEY ("id") REFERENCES "Author" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Parliamentarian" ("id", "party", "seat") SELECT "id", "party", "seat" FROM "Parliamentarian";
DROP TABLE "Parliamentarian";
ALTER TABLE "new_Parliamentarian" RENAME TO "Parliamentarian";
CREATE TABLE "new_Source" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "script" TEXT NOT NULL,
    "url" TEXT,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);
INSERT INTO "new_Source" ("id", "name", "script", "url") SELECT "id", "name", "script", "url" FROM "Source";
DROP TABLE "Source";
ALTER TABLE "new_Source" RENAME TO "Source";
CREATE TABLE "new_SourceGroup" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);
INSERT INTO "new_SourceGroup" ("id", "name") SELECT "id", "name" FROM "SourceGroup";
DROP TABLE "SourceGroup";
ALTER TABLE "new_SourceGroup" RENAME TO "SourceGroup";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
