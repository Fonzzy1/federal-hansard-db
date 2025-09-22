/*
  Warnings:

  - A unique constraint covering the columns `[name,text]` on the table `RawDocument` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "RawDocument_name_text_key" ON "RawDocument"("name", "text");
