-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Service" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "startDate" DATETIME NOT NULL,
    "endDate" DATETIME,
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
INSERT INTO "new_Service" ("dateAdded", "dateModified", "endDate", "id", "isSenate", "parliamentId", "parliamentarianId", "partyId", "seat", "startDate", "state") SELECT "dateAdded", "dateModified", "endDate", "id", "isSenate", "parliamentId", "parliamentarianId", "partyId", "seat", "startDate", "state" FROM "Service";
DROP TABLE "Service";
ALTER TABLE "new_Service" RENAME TO "Service";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
