/*
  Warnings:

  - You are about to drop the column `LastDate` on the `Minister` table. All the data in the column will be lost.
  - You are about to drop the `CommitteeMembers` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropForeignKey
ALTER TABLE "CommitteeMembers" DROP CONSTRAINT "CommitteeMembers_parliamentarianId_fkey";

-- AlterTable
ALTER TABLE "Minister" DROP COLUMN "LastDate",
ADD COLUMN     "lastDate" TIMESTAMP(3);

-- AlterTable
ALTER TABLE "Ministry" ALTER COLUMN "lastDate" DROP NOT NULL;

-- DropTable
DROP TABLE "CommitteeMembers";
