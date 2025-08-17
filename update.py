from prisma import Client
import subprocess

db = Client()
await db.connect()

sources = await db.source.find_many()
