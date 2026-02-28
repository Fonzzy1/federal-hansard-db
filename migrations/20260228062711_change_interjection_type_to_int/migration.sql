/*
  Warnings:

  - Changed the type of `isGeneral` on the `Interjection` table. No cast exists, the column would be dropped and recreated, which cannot be done if there is data, since the column is required.

*/
-- AlterTable
ALTER TABLE "Interjection" DROP COLUMN "isGeneral",
ADD COLUMN     "isGeneral" INTEGER NOT NULL;
