/*
  Warnings:

  - Added the required column `type` to the `Document` table without a default value. This is not possible if the table is not empty.

*/
-- CreateTable
CREATE TABLE "_RelatedDocuments" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL,
    CONSTRAINT "_RelatedDocuments_A_fkey" FOREIGN KEY ("A") REFERENCES "Document" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "_RelatedDocuments_B_fkey" FOREIGN KEY ("B") REFERENCES "Document" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Document" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "text" TEXT NOT NULL,
    "date" DATETIME NOT NULL,
    "url" TEXT,
    "type" TEXT NOT NULL,
    "authorId" INTEGER NOT NULL,
    "sourceId" INTEGER NOT NULL,
    "dateAdded" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dateModified" DATETIME NOT NULL,
    "documentId" INTEGER,
    CONSTRAINT "Document_authorId_fkey" FOREIGN KEY ("authorId") REFERENCES "Author" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "Document_sourceId_fkey" FOREIGN KEY ("sourceId") REFERENCES "Source" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_Document" ("authorId", "date", "dateAdded", "dateModified", "id", "sourceId", "text", "url") SELECT "authorId", "date", "dateAdded", "dateModified", "id", "sourceId", "text", "url" FROM "Document";
DROP TABLE "Document";
ALTER TABLE "new_Document" RENAME TO "Document";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;

-- CreateIndex
CREATE UNIQUE INDEX "_RelatedDocuments_AB_unique" ON "_RelatedDocuments"("A", "B");

-- CreateIndex
CREATE INDEX "_RelatedDocuments_B_index" ON "_RelatedDocuments"("B");
