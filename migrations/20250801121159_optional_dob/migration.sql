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
    "dob" DATETIME,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);
INSERT INTO "new_Parliamentarian" ("dateAdded", "dateModified", "dob", "firstName", "firstNations", "gender", "id", "image", "lastName") SELECT "dateAdded", "dateModified", "dob", "firstName", "firstNations", "gender", "id", "image", "lastName" FROM "Parliamentarian";
DROP TABLE "Parliamentarian";
ALTER TABLE "new_Parliamentarian" RENAME TO "Parliamentarian";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
