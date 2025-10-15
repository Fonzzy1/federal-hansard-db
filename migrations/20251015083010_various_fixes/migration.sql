/*
  Warnings:

  - The `altId` column on the `Parliamentarian` table would be dropped and recreated. This will lead to data loss if there is data in the column.
  - A unique constraint covering the columns `[name,sourceId]` on the table `RawDocument` will be added. If there are existing duplicate values, this will fail.
  - A unique constraint covering the columns `[name]` on the table `rawAuthor` will be added. If there are existing duplicate values, this will fail.

*/
-- DropIndex
DROP INDEX "RawDocument_name_text_key";

-- AlterTable
ALTER TABLE "Parliamentarian" DROP COLUMN "altId",
ADD COLUMN     "altId" TEXT[];

-- CreateIndex
CREATE UNIQUE INDEX "RawDocument_name_sourceId_key" ON "RawDocument"("name", "sourceId");

-- CreateIndex
CREATE UNIQUE INDEX "rawAuthor_name_key" ON "rawAuthor"("name");
