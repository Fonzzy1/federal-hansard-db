/*
  Warnings:

  - The `parliament` column on the `SittingDay` table would be dropped and recreated. This will lead to data loss if there is data in the column.
  - The `session` column on the `SittingDay` table would be dropped and recreated. This will lead to data loss if there is data in the column.
  - The `period` column on the `SittingDay` table would be dropped and recreated. This will lead to data loss if there is data in the column.
  - A unique constraint covering the columns `[date,chamber]` on the table `SittingDay` will be added. If there are existing duplicate values, this will fail.

*/
-- AlterTable
ALTER TABLE "SittingDay" DROP COLUMN "parliament",
ADD COLUMN     "parliament" INTEGER,
DROP COLUMN "session",
ADD COLUMN     "session" INTEGER,
DROP COLUMN "period",
ADD COLUMN     "period" INTEGER;

-- CreateIndex
CREATE UNIQUE INDEX "SittingDay_date_chamber_key" ON "SittingDay"("date", "chamber");
