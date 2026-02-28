/*
  Warnings:

  - Added the required column `isGeneral` to the `Interjection` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "Interjection" ADD COLUMN     "isGeneral" BOOLEAN NOT NULL;
