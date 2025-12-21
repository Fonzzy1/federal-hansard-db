-- CreateTable
CREATE TABLE "Minister" (
    "id" SERIAL NOT NULL,
    "firstDate" TIMESTAMP(3) NOT NULL,
    "LastDate" TIMESTAMP(3),
    "role" TEXT NOT NULL,
    "portfolio" TEXT NOT NULL,
    "displayString" TEXT NOT NULL,
    "parliamentarianId" TEXT NOT NULL,
    "ministryId" INTEGER,

    CONSTRAINT "Minister_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Ministry" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "firstDate" TIMESTAMP(3) NOT NULL,
    "lastDate" TIMESTAMP(3) NOT NULL,
    "isShadow" BOOLEAN NOT NULL,
    "parliamentarianId" TEXT NOT NULL,

    CONSTRAINT "Ministry_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CommitteeMembers" (
    "id" SERIAL NOT NULL,
    "type" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "firstDate" TIMESTAMP(3) NOT NULL,
    "lastDate" TIMESTAMP(3) NOT NULL,
    "parliamentarianId" TEXT NOT NULL,

    CONSTRAINT "CommitteeMembers_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "Minister" ADD CONSTRAINT "Minister_parliamentarianId_fkey" FOREIGN KEY ("parliamentarianId") REFERENCES "Parliamentarian"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Minister" ADD CONSTRAINT "Minister_ministryId_fkey" FOREIGN KEY ("ministryId") REFERENCES "Ministry"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Ministry" ADD CONSTRAINT "Ministry_parliamentarianId_fkey" FOREIGN KEY ("parliamentarianId") REFERENCES "Parliamentarian"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CommitteeMembers" ADD CONSTRAINT "CommitteeMembers_parliamentarianId_fkey" FOREIGN KEY ("parliamentarianId") REFERENCES "Parliamentarian"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
