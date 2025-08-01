/*
  Warnings:

  - A unique constraint covering the columns `[rawName]` on the table `Author` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "Author_rawName_key" ON "Author"("rawName");
