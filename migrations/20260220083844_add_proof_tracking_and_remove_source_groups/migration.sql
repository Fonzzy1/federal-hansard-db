/*
  Warnings:

  - You are about to drop the `SourceGroup` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `_SourceToSourceGroup` table. If the table is not empty, all the data it contains will be lost.
  - Added the required column `is_proof` to the `RawDocument` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "_SourceToSourceGroup" DROP CONSTRAINT "_SourceToSourceGroup_A_fkey";

-- DropForeignKey
ALTER TABLE "_SourceToSourceGroup" DROP CONSTRAINT "_SourceToSourceGroup_B_fkey";

-- AlterTable
ALTER TABLE "RawDocument" ADD COLUMN     "is_proof" BOOLEAN NOT NULL;

-- DropTable
DROP TABLE "SourceGroup";

-- DropTable
DROP TABLE "_SourceToSourceGroup";
