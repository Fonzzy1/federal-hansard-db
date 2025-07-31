/*
  Warnings:

  - Added the required column `dob` to the `Parliamentarian` table without a default value. This is not possible if the table is not empty.
  - Added the required column `firstName` to the `Parliamentarian` table without a default value. This is not possible if the table is not empty.
  - Added the required column `firstNations` to the `Parliamentarian` table without a default value. This is not possible if the table is not empty.
  - Added the required column `gender` to the `Parliamentarian` table without a default value. This is not possible if the table is not empty.
  - Added the required column `image` to the `Parliamentarian` table without a default value. This is not possible if the table is not empty.
  - Added the required column `lastName` to the `Parliamentarian` table without a default value. This is not possible if the table is not empty.

*/
-- DropIndex
DROP INDEX "Author_name_key";

-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Parliamentarian" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "firstName" TEXT NOT NULL,
    "lastName" TEXT NOT NULL,
    "firstNations" BOOLEAN NOT NULL,
    "image" TEXT NOT NULL,
    "gender" INTEGER NOT NULL,
    "dob" DATETIME NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);
INSERT INTO "new_Parliamentarian" ("dateAdded", "dateModified", "id") SELECT "dateAdded", "dateModified", "id" FROM "Parliamentarian";
DROP TABLE "Parliamentarian";
ALTER TABLE "new_Parliamentarian" RENAME TO "Parliamentarian";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
