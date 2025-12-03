/*
  Warnings:

  - Added the required column `sequence` to the `Interjection` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "Interjection" ADD COLUMN     "sequence" INTEGER NOT NULL;
