/*
  Warnings:

  - You are about to drop the `ParliamentarianParlement` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the column `governmentParty` on the `Parliament` table. All the data in the column will be lost.
  - You are about to drop the column `party` on the `Parliamentarian` table. All the data in the column will be lost.
  - You are about to drop the column `seat` on the `Parliamentarian` table. All the data in the column will be lost.
  - Added the required column `governmentPartyId` to the `Parliament` table without a default value. This is not possible if the table is not empty.
  - Added the required column `oppositionPartyId` to the `Parliament` table without a default value. This is not possible if the table is not empty.

*/
-- DropTable
PRAGMA foreign_keys=off;
DROP TABLE "ParliamentarianParlement";
PRAGMA foreign_keys=on;

-- CreateTable
CREATE TABLE "Service" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "startDate" DATETIME NOT NULL,
    "endDate" DATETIME NOT NULL,
    "isSenate" BOOLEAN NOT NULL,
    "seat" TEXT,
    "state" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    "parliamentarianId" INTEGER NOT NULL,
    "parliamentId" INTEGER NOT NULL,
    "partyId" INTEGER NOT NULL,
    CONSTRAINT "Service_partyId_fkey" FOREIGN KEY ("partyId") REFERENCES "Party" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Service_parliamentId_fkey" FOREIGN KEY ("parliamentId") REFERENCES "Parliament" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Service_parliamentarianId_fkey" FOREIGN KEY ("parliamentarianId") REFERENCES "Parliamentarian" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Party" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL
);

-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Author" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    "parliamentarianId" INTEGER,
    CONSTRAINT "Author_parliamentarianId_fkey" FOREIGN KEY ("parliamentarianId") REFERENCES "Parliamentarian" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);
INSERT INTO "new_Author" ("dateAdded", "dateModified", "id", "name") SELECT "dateAdded", "dateModified", "id", "name" FROM "Author";
DROP TABLE "Author";
ALTER TABLE "new_Author" RENAME TO "Author";
CREATE UNIQUE INDEX "Author_name_key" ON "Author"("name");
CREATE TABLE "new_Parliament" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "governmentPartyId" INTEGER NOT NULL,
    "oppositionPartyId" INTEGER NOT NULL,
    "firstDate" DATETIME NOT NULL,
    "lastDate" DATETIME NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    CONSTRAINT "Parliament_governmentPartyId_fkey" FOREIGN KEY ("governmentPartyId") REFERENCES "Party" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Parliament_oppositionPartyId_fkey" FOREIGN KEY ("oppositionPartyId") REFERENCES "Party" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Parliament" ("dateAdded", "dateModified", "firstDate", "id", "lastDate") SELECT "dateAdded", "dateModified", "firstDate", "id", "lastDate" FROM "Parliament";
DROP TABLE "Parliament";
ALTER TABLE "new_Parliament" RENAME TO "Parliament";
CREATE TABLE "new_Parliamentarian" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);
INSERT INTO "new_Parliamentarian" ("dateAdded", "dateModified", "id") SELECT "dateAdded", "dateModified", "id" FROM "Parliamentarian";
DROP TABLE "Parliamentarian";
ALTER TABLE "new_Parliamentarian" RENAME TO "Parliamentarian";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
