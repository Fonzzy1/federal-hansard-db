from prisma import Client
import subprocess

db = Client()
await db.connect()
sources = await db.source.find_many()

for source in sources:
    if source.inFile:
        subprocess.run(['python3', source.scrape, source.inFile, source.outFile])
    else:
        subprocess.run(['python3', source.scrape, source.outFile])
    subprocess.run(['python3', source.script, source.outFile])


