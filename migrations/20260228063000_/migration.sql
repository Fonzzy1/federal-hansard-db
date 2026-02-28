/*
  Warnings:

  - You are about to drop the column `isGeneral` on the `Interjection` table. All the data in the column will be lost.
  - Added the required column `type` to the `Interjection` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "Interjection" DROP COLUMN "isGeneral",
ADD COLUMN     "type" INTEGER NOT NULL;
