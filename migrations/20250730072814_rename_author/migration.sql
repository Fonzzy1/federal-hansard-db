-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
ALTER TABLE Author
RENAME COLUMN name to rawName; 
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
