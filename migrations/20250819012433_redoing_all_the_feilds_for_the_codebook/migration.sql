/*
  Warnings:

  - You are about to drop the `Dimension` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `InfrastructureGroupOnInfrastructure` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `SourceGroupSource` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `_InfraToInfraGroup` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the column `dimensionId` on the `Deconstruction` table. All the data in the column will be lost.
  - You are about to drop the column `dimensionid` on the `Issue` table. All the data in the column will be lost.
  - Added the required column `infrastructureGroupId` to the `Deconstruction` table without a default value. This is not possible if the table is not empty.
  - Added the required column `issueId` to the `Deconstruction` table without a default value. This is not possible if the table is not empty.
  - Added the required column `issueTypeId` to the `Issue` table without a default value. This is not possible if the table is not empty.

*/
-- DropIndex
DROP INDEX "Dimension_name_key";

-- DropIndex
DROP INDEX "_InfraToInfraGroup_B_index";

-- DropIndex
DROP INDEX "_InfraToInfraGroup_AB_unique";

-- DropTable
PRAGMA foreign_keys=off;
DROP TABLE "Dimension";
PRAGMA foreign_keys=on;

-- DropTable
PRAGMA foreign_keys=off;
DROP TABLE "InfrastructureGroupOnInfrastructure";
PRAGMA foreign_keys=on;

-- DropTable
PRAGMA foreign_keys=off;
DROP TABLE "SourceGroupSource";
PRAGMA foreign_keys=on;

-- DropTable
PRAGMA foreign_keys=off;
DROP TABLE "_InfraToInfraGroup";
PRAGMA foreign_keys=on;

-- CreateTable
CREATE TABLE "IssueType" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "InfrastructureType" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    "infrastructureGroupId" INTEGER,
    CONSTRAINT "InfrastructureType_infrastructureGroupId_fkey" FOREIGN KEY ("infrastructureGroupId") REFERENCES "InfrastructureGroup" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Deconstruction" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "claimId" INTEGER NOT NULL,
    "valence" INTEGER NOT NULL,
    "issueId" INTEGER NOT NULL,
    "deconstructorId" INTEGER NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    "infrastructureId" INTEGER,
    "infrastructureTypeId" INTEGER,
    "infrastructureGroupId" INTEGER NOT NULL,
    CONSTRAINT "Deconstruction_deconstructorId_fkey" FOREIGN KEY ("deconstructorId") REFERENCES "Deconstructor" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Deconstruction_issueId_fkey" FOREIGN KEY ("issueId") REFERENCES "Issue" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Deconstruction_claimId_fkey" FOREIGN KEY ("claimId") REFERENCES "Claim" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Deconstruction_infrastructureId_fkey" FOREIGN KEY ("infrastructureId") REFERENCES "Infrastructure" ("id") ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT "Deconstruction_infrastructureTypeId_fkey" FOREIGN KEY ("infrastructureTypeId") REFERENCES "InfrastructureType" ("id") ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT "Deconstruction_infrastructureGroupId_fkey" FOREIGN KEY ("infrastructureGroupId") REFERENCES "InfrastructureGroup" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Deconstruction" ("claimId", "dateAdded", "dateModified", "deconstructorId", "id", "infrastructureId", "valence") SELECT "claimId", "dateAdded", "dateModified", "deconstructorId", "id", "infrastructureId", "valence" FROM "Deconstruction";
DROP TABLE "Deconstruction";
ALTER TABLE "new_Deconstruction" RENAME TO "Deconstruction";
CREATE UNIQUE INDEX "Deconstruction_claimId_deconstructorId_key" ON "Deconstruction"("claimId", "deconstructorId");
CREATE TABLE "new_Infrastructure" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    "infrastructureTypeId" INTEGER,
    CONSTRAINT "Infrastructure_infrastructureTypeId_fkey" FOREIGN KEY ("infrastructureTypeId") REFERENCES "InfrastructureType" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);
INSERT INTO "new_Infrastructure" ("dateAdded", "dateModified", "id", "name") SELECT "dateAdded", "dateModified", "id", "name" FROM "Infrastructure";
DROP TABLE "Infrastructure";
ALTER TABLE "new_Infrastructure" RENAME TO "Infrastructure";
CREATE UNIQUE INDEX "Infrastructure_name_key" ON "Infrastructure"("name");
CREATE TABLE "new_Issue" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "issueTypeId" INTEGER NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    CONSTRAINT "Issue_issueTypeId_fkey" FOREIGN KEY ("issueTypeId") REFERENCES "IssueType" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Issue" ("dateAdded", "dateModified", "id", "name") SELECT "dateAdded", "dateModified", "id", "name" FROM "Issue";
DROP TABLE "Issue";
ALTER TABLE "new_Issue" RENAME TO "Issue";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;

-- CreateIndex
CREATE UNIQUE INDEX "IssueType_name_key" ON "IssueType"("name");

-- CreateIndex
CREATE UNIQUE INDEX "InfrastructureType_name_key" ON "InfrastructureType"("name");
