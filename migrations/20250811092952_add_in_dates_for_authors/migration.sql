/*
  Warnings:

  - Added the required column `month` to the `Author` table without a default value. This is not possible if the table is not empty.
  - Added the required column `year` to the `Author` table without a default value. This is not possible if the table is not empty.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Author" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "rawName" TEXT NOT NULL,
    "year" INTEGER NOT NULL,
    "month" INTEGER NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    "parliamentarianId" TEXT,
    CONSTRAINT "Author_parliamentarianId_fkey" FOREIGN KEY ("parliamentarianId") REFERENCES "Parliamentarian" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);
INSERT INTO "new_Author" ("dateAdded", "dateModified", "id", "parliamentarianId", "rawName") SELECT "dateAdded", "dateModified", "id", "parliamentarianId", "rawName" FROM "Author";
DROP TABLE "Author";
ALTER TABLE "new_Author" RENAME TO "Author";
CREATE UNIQUE INDEX "Author_rawName_year_month_key" ON "Author"("rawName", "year", "month");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
