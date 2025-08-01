/*
  Warnings:

  - A unique constraint covering the columns `[name]` on the table `Party` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "Party_name_key" ON "Party"("name");
