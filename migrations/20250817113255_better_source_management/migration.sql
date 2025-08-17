/*
  Warnings:

  - You are about to drop the column `file` on the `Source` table. All the data in the column will be lost.
  - Added the required column `outFile` to the `Source` table without a default value. This is not possible if the table is not empty.
  - Added the required column `scrape` to the `Source` table without a default value. This is not possible if the table is not empty.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Source" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "script" TEXT NOT NULL,
    "scrape" TEXT NOT NULL,
    "outFile" TEXT NOT NULL,
    "inFile" TEXT,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);
INSERT INTO "new_Source" ("dateAdded", "dateModified", "id", "name", "script") SELECT "dateAdded", "dateModified", "id", "name", "script" FROM "Source";
DROP TABLE "Source";
ALTER TABLE "new_Source" RENAME TO "Source";
CREATE UNIQUE INDEX "Source_name_key" ON "Source"("name");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
