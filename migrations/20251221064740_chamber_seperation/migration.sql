/*
  Warnings:

  - You are about to drop the column `date` on the `Document` table. All the data in the column will be lost.
  - Added the required column `sittingDayId` to the `Document` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "Document" DROP CONSTRAINT "Document_rawAuthorId_fkey";

-- AlterTable
ALTER TABLE "Document" DROP COLUMN "date",
ADD COLUMN     "sittingDayId" INTEGER NOT NULL,
ALTER COLUMN "rawAuthorId" DROP NOT NULL;

-- CreateTable
CREATE TABLE "SittingDay" (
    "id" SERIAL NOT NULL,
    "date" TIMESTAMP(3) NOT NULL,
    "chamber" TEXT NOT NULL,
    "parliament" TEXT NOT NULL,
    "session" TEXT NOT NULL,
    "period" TEXT NOT NULL,

    CONSTRAINT "SittingDay_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "Document" ADD CONSTRAINT "Document_sittingDayId_fkey" FOREIGN KEY ("sittingDayId") REFERENCES "SittingDay"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Document" ADD CONSTRAINT "Document_rawAuthorId_fkey" FOREIGN KEY ("rawAuthorId") REFERENCES "rawAuthor"("id") ON DELETE SET NULL ON UPDATE CASCADE;
