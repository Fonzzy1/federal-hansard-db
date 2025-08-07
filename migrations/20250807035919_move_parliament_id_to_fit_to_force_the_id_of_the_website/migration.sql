/*
  Warnings:

  - The primary key for the `Parliamentarian` table will be changed. If it partially fails, the table could be left without primary key constraint.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Author" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "rawName" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    "parliamentarianId" TEXT,
    CONSTRAINT "Author_parliamentarianId_fkey" FOREIGN KEY ("parliamentarianId") REFERENCES "Parliamentarian" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);
INSERT INTO "new_Author" ("dateAdded", "dateModified", "id", "parliamentarianId", "rawName") SELECT "dateAdded", "dateModified", "id", "parliamentarianId", "rawName" FROM "Author";
DROP TABLE "Author";
ALTER TABLE "new_Author" RENAME TO "Author";
CREATE UNIQUE INDEX "Author_rawName_key" ON "Author"("rawName");
CREATE TABLE "new_Parliamentarian" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "firstName" TEXT NOT NULL,
    "lastName" TEXT NOT NULL,
    "firstNations" BOOLEAN NOT NULL,
    "image" TEXT NOT NULL,
    "gender" INTEGER NOT NULL,
    "dob" DATETIME,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);
INSERT INTO "new_Parliamentarian" ("dateAdded", "dateModified", "dob", "firstName", "firstNations", "gender", "id", "image", "lastName") SELECT "dateAdded", "dateModified", "dob", "firstName", "firstNations", "gender", "id", "image", "lastName" FROM "Parliamentarian";
DROP TABLE "Parliamentarian";
ALTER TABLE "new_Parliamentarian" RENAME TO "Parliamentarian";
CREATE TABLE "new_Service" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "startDate" DATETIME NOT NULL,
    "endDate" DATETIME,
    "isSenate" BOOLEAN NOT NULL,
    "seat" TEXT,
    "state" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    "parliamentarianId" TEXT NOT NULL,
    "parliamentId" INTEGER NOT NULL,
    "partyId" INTEGER NOT NULL,
    CONSTRAINT "Service_parliamentarianId_fkey" FOREIGN KEY ("parliamentarianId") REFERENCES "Parliamentarian" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Service_parliamentId_fkey" FOREIGN KEY ("parliamentId") REFERENCES "Parliament" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Service_partyId_fkey" FOREIGN KEY ("partyId") REFERENCES "Party" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Service" ("dateAdded", "dateModified", "endDate", "id", "isSenate", "parliamentId", "parliamentarianId", "partyId", "seat", "startDate", "state") SELECT "dateAdded", "dateModified", "endDate", "id", "isSenate", "parliamentId", "parliamentarianId", "partyId", "seat", "startDate", "state" FROM "Service";
DROP TABLE "Service";
ALTER TABLE "new_Service" RENAME TO "Service";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
