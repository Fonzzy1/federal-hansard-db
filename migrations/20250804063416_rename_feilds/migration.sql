/*
  Warnings:

  - You are about to drop the column `extractor_id` on the `Claim` table. All the data in the column will be lost.
  - You are about to drop the column `deconstructor_id` on the `Deconstruction` table. All the data in the column will be lost.
  - Added the required column `extractorId` to the `Claim` table without a default value. This is not possible if the table is not empty.
  - Added the required column `deconstructorId` to the `Deconstruction` table without a default value. This is not possible if the table is not empty.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Claim" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "text" TEXT NOT NULL,
    "documentid" INTEGER NOT NULL,
    "extractorId" INTEGER NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    CONSTRAINT "Claim_documentid_fkey" FOREIGN KEY ("documentid") REFERENCES "Document" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Claim_extractorId_fkey" FOREIGN KEY ("extractorId") REFERENCES "Extractor" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Claim" ("dateAdded", "dateModified", "documentid", "id", "text") SELECT "dateAdded", "dateModified", "documentid", "id", "text" FROM "Claim";
DROP TABLE "Claim";
ALTER TABLE "new_Claim" RENAME TO "Claim";
CREATE TABLE "new_Deconstruction" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "claimId" INTEGER NOT NULL,
    "infrastructureId" INTEGER NOT NULL,
    "valence" INTEGER NOT NULL,
    "dimensionId" INTEGER,
    "deconstructorId" INTEGER NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    CONSTRAINT "Deconstruction_claimId_fkey" FOREIGN KEY ("claimId") REFERENCES "Claim" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Deconstruction_infrastructureId_fkey" FOREIGN KEY ("infrastructureId") REFERENCES "Infrastructure" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Deconstruction_dimensionId_fkey" FOREIGN KEY ("dimensionId") REFERENCES "Dimension" ("id") ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT "Deconstruction_deconstructorId_fkey" FOREIGN KEY ("deconstructorId") REFERENCES "Deconstructor" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Deconstruction" ("claimId", "dateAdded", "dateModified", "dimensionId", "id", "infrastructureId", "valence") SELECT "claimId", "dateAdded", "dateModified", "dimensionId", "id", "infrastructureId", "valence" FROM "Deconstruction";
DROP TABLE "Deconstruction";
ALTER TABLE "new_Deconstruction" RENAME TO "Deconstruction";
CREATE UNIQUE INDEX "Deconstruction_claimId_deconstructorId_key" ON "Deconstruction"("claimId", "deconstructorId");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
