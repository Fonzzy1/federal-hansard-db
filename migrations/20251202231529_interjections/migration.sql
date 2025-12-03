-- CreateTable
CREATE TABLE "Interjection" (
    "id" SERIAL NOT NULL,
    "text" TEXT NOT NULL,
    "documentId" INTEGER,
    "rawAuthorId" INTEGER NOT NULL,

    CONSTRAINT "Interjection_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "Interjection" ADD CONSTRAINT "Interjection_rawAuthorId_fkey" FOREIGN KEY ("rawAuthorId") REFERENCES "rawAuthor"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Interjection" ADD CONSTRAINT "Interjection_documentId_fkey" FOREIGN KEY ("documentId") REFERENCES "Document"("id") ON DELETE SET NULL ON UPDATE CASCADE;
