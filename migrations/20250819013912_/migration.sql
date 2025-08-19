/*
  Warnings:

  - Made the column `infrastructureTypeId` on table `Infrastructure` required. This step will fail if there are existing NULL values in that column.
  - Made the column `infrastructureGroupId` on table `InfrastructureType` required. This step will fail if there are existing NULL values in that column.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Infrastructure" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    "infrastructureTypeId" INTEGER NOT NULL,
    CONSTRAINT "Infrastructure_infrastructureTypeId_fkey" FOREIGN KEY ("infrastructureTypeId") REFERENCES "InfrastructureType" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Infrastructure" ("dateAdded", "dateModified", "id", "infrastructureTypeId", "name") SELECT "dateAdded", "dateModified", "id", "infrastructureTypeId", "name" FROM "Infrastructure";
DROP TABLE "Infrastructure";
ALTER TABLE "new_Infrastructure" RENAME TO "Infrastructure";
CREATE UNIQUE INDEX "Infrastructure_name_key" ON "Infrastructure"("name");
CREATE TABLE "new_InfrastructureType" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    "infrastructureGroupId" INTEGER NOT NULL,
    CONSTRAINT "InfrastructureType_infrastructureGroupId_fkey" FOREIGN KEY ("infrastructureGroupId") REFERENCES "InfrastructureGroup" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_InfrastructureType" ("dateAdded", "dateModified", "id", "infrastructureGroupId", "name") SELECT "dateAdded", "dateModified", "id", "infrastructureGroupId", "name" FROM "InfrastructureType";
DROP TABLE "InfrastructureType";
ALTER TABLE "new_InfrastructureType" RENAME TO "InfrastructureType";
CREATE UNIQUE INDEX "InfrastructureType_name_key" ON "InfrastructureType"("name");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
