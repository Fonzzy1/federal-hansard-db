/*
  Warnings:

  - A unique constraint covering the columns `[date,house,chamber]` on the table `SittingDay` will be added. If there are existing duplicate values, this will fail.
  - Added the required column `house` to the `SittingDay` table without a default value. This is not possible if the table is not empty.

*/
-- DropIndex
DROP INDEX "SittingDay_date_chamber_key";

-- AlterTable
ALTER TABLE "SittingDay" ADD COLUMN     "house" TEXT NOT NULL;

-- CreateIndex
CREATE UNIQUE INDEX "SittingDay_date_house_chamber_key" ON "SittingDay"("date", "house", "chamber");
