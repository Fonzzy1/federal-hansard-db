-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Parliament" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "governmentPartyId" INTEGER NOT NULL,
    "oppositionPartyId" INTEGER NOT NULL,
    "firstDate" DATETIME NOT NULL,
    "lastDate" DATETIME NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);
INSERT INTO "new_Parliament" ("dateAdded", "dateModified", "firstDate", "governmentPartyId", "id", "lastDate", "oppositionPartyId") SELECT "dateAdded", "dateModified", "firstDate", "governmentPartyId", "id", "lastDate", "oppositionPartyId" FROM "Parliament";
DROP TABLE "Parliament";
ALTER TABLE "new_Parliament" RENAME TO "Parliament";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
