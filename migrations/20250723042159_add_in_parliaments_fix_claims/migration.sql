/*
  Warnings:

  - You are about to drop the column `issueid` on the `Claim` table. All the data in the column will be lost.

*/
-- CreateTable
CREATE TABLE "Parliament" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "governmentParty" TEXT NOT NULL,
    "firstDate" DATETIME NOT NULL,
    "lastDate" DATETIME NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "ParliamentarianParlement" (
    "parliamentarianId" INTEGER NOT NULL,
    "parliamentId" INTEGER NOT NULL,

    PRIMARY KEY ("parliamentarianId", "parliamentId"),
    CONSTRAINT "ParliamentarianParlement_parliamentarianId_fkey" FOREIGN KEY ("parliamentarianId") REFERENCES "Parliamentarian" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "ParliamentarianParlement_parliamentId_fkey" FOREIGN KEY ("parliamentId") REFERENCES "Parliament" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Claim" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "text" TEXT NOT NULL,
    "documentid" INTEGER NOT NULL,
    "extractor_id" INTEGER NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    CONSTRAINT "Claim_documentid_fkey" FOREIGN KEY ("documentid") REFERENCES "Document" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Claim_extractor_id_fkey" FOREIGN KEY ("extractor_id") REFERENCES "Extractor" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Claim" ("dateAdded", "dateModified", "documentid", "extractor_id", "id", "text") SELECT "dateAdded", "dateModified", "documentid", "extractor_id", "id", "text" FROM "Claim";
DROP TABLE "Claim";
ALTER TABLE "new_Claim" RENAME TO "Claim";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
