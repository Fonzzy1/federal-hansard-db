/*
  Warnings:

  - Added the required column `type` to the `Interjection` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "Interjection" ADD COLUMN     "type" INTEGER NOT NULL,
ALTER COLUMN "text" DROP NOT NULL;
