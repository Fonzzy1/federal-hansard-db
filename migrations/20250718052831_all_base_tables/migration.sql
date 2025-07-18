/*
  Warnings:

  - Added the required column `script` to the `Source` table without a default value. This is not possible if the table is not empty.

*/
-- CreateTable
CREATE TABLE "SourceGroup" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "SourceGroupSource" (
    "sourceId" INTEGER NOT NULL,
    "sourceGroupId" INTEGER NOT NULL,

    PRIMARY KEY ("sourceId", "sourceGroupId"),
    CONSTRAINT "SourceGroupSource_sourceId_fkey" FOREIGN KEY ("sourceId") REFERENCES "Source" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "SourceGroupSource_sourceGroupId_fkey" FOREIGN KEY ("sourceGroupId") REFERENCES "SourceGroup" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Author" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "Parliamentarian" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "party" TEXT NOT NULL,
    "seat" TEXT NOT NULL,
    CONSTRAINT "Parliamentarian_id_fkey" FOREIGN KEY ("id") REFERENCES "Author" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Document" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "text" TEXT NOT NULL,
    "date" DATETIME NOT NULL,
    "url" TEXT,
    "authorId" INTEGER NOT NULL,
    "sourceId" INTEGER NOT NULL,
    CONSTRAINT "Document_authorId_fkey" FOREIGN KEY ("authorId") REFERENCES "Author" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Document_sourceId_fkey" FOREIGN KEY ("sourceId") REFERENCES "Source" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Claim" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "text" TEXT NOT NULL,
    "documentid" INTEGER NOT NULL,
    "issueid" INTEGER NOT NULL,
    CONSTRAINT "Claim_documentid_fkey" FOREIGN KEY ("documentid") REFERENCES "Document" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Claim_issueid_fkey" FOREIGN KEY ("issueid") REFERENCES "Issue" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Issue" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dimensionid" INTEGER NOT NULL,
    CONSTRAINT "Issue_dimensionid_fkey" FOREIGN KEY ("dimensionid") REFERENCES "Dimension" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Dimension" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "Deconstruction" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "claimId" INTEGER NOT NULL,
    "infrastructureId" INTEGER NOT NULL,
    "valence" INTEGER NOT NULL,
    "dimensionId" INTEGER,
    CONSTRAINT "Deconstruction_claimId_fkey" FOREIGN KEY ("claimId") REFERENCES "Claim" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Deconstruction_infrastructureId_fkey" FOREIGN KEY ("infrastructureId") REFERENCES "Infrastructure" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Deconstruction_dimensionId_fkey" FOREIGN KEY ("dimensionId") REFERENCES "Dimension" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Infrastructure" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "InfrastructureGroupOnInfrastructure" (
    "infrastructureId" INTEGER NOT NULL,
    "infrastructureGroupId" INTEGER NOT NULL,

    PRIMARY KEY ("infrastructureId", "infrastructureGroupId"),
    CONSTRAINT "InfrastructureGroupOnInfrastructure_infrastructureId_fkey" FOREIGN KEY ("infrastructureId") REFERENCES "Infrastructure" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "InfrastructureGroupOnInfrastructure_infrastructureGroupId_fkey" FOREIGN KEY ("infrastructureGroupId") REFERENCES "InfrastructureGroup" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "InfrastructureGroup" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "_SourceToSourceGroup" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL,
    CONSTRAINT "_SourceToSourceGroup_A_fkey" FOREIGN KEY ("A") REFERENCES "Source" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "_SourceToSourceGroup_B_fkey" FOREIGN KEY ("B") REFERENCES "SourceGroup" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "_InfraToInfraGroup" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL,
    CONSTRAINT "_InfraToInfraGroup_A_fkey" FOREIGN KEY ("A") REFERENCES "Infrastructure" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "_InfraToInfraGroup_B_fkey" FOREIGN KEY ("B") REFERENCES "InfrastructureGroup" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Source" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "script" TEXT NOT NULL,
    "url" TEXT
);
INSERT INTO "new_Source" ("id", "name") SELECT "id", "name" FROM "Source";
DROP TABLE "Source";
ALTER TABLE "new_Source" RENAME TO "Source";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;

-- CreateIndex
CREATE UNIQUE INDEX "Dimension_name_key" ON "Dimension"("name");

-- CreateIndex
CREATE UNIQUE INDEX "Deconstruction_claimId_key" ON "Deconstruction"("claimId");

-- CreateIndex
CREATE UNIQUE INDEX "Infrastructure_name_key" ON "Infrastructure"("name");

-- CreateIndex
CREATE UNIQUE INDEX "InfrastructureGroup_name_key" ON "InfrastructureGroup"("name");

-- CreateIndex
CREATE UNIQUE INDEX "_SourceToSourceGroup_AB_unique" ON "_SourceToSourceGroup"("A", "B");

-- CreateIndex
CREATE INDEX "_SourceToSourceGroup_B_index" ON "_SourceToSourceGroup"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_InfraToInfraGroup_AB_unique" ON "_InfraToInfraGroup"("A", "B");

-- CreateIndex
CREATE INDEX "_InfraToInfraGroup_B_index" ON "_InfraToInfraGroup"("B");
