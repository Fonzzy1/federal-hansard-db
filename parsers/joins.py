import re
from primsa import Prisma as Client
import string
import re
import re
import string


def normalize(text):
    if not text:
        return ""
    return re.sub(rf"[{re.escape(string.punctuation)}\s]", "", text).lower()


async def join_politicians_to_raw_authors(db):
    all_services = await db.parliamentarian.find_many()
    politicians = {normalize(p.id): p for p in all_services}
    politicians.update(
        {normalize(p.altId): p for p in all_services if hasattr(p, "altId")}
    )

    authors = {
        k.id: k
        for k in await db.author.find_many(
            where={"parliamentarian": None},
        )
    }

    for auth in authors.values():
        auth_name_clean = normalize(auth.rawName)

        # Skip if cleaned rawName is empty
        if auth_name_clean == "":
            continue
        elif auth_name_clean in politicians.keys():
            matched_id = politicians[auth_name_clean].id
            await db.author.update(
                where={"id": auth.id},
                data={"parliamentarian": {"connect": {"id": matched_id}}},
            )
        else:
            print(f"{auth.rawName} is an alt_name")
