from prisma import Prisma

import asyncio
import os
import xml.etree.ElementTree as ET
from tqdm import tqdm
import lxml.etree as ET
from lxml import html
import re
import datetime


"""
Goal is to extract:

    Speeches
    Question and answer pairs
    Petitions

All with interjections removed, and continues sliced together

"""


class HansardNoElementsException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class EmptyDocumentError(Exception):
    def __init__(self):
        super().__init__()


class FailedTalkerExtractionException(Exception):
    def __init__(self, element):
        self.message = str(ET.tostring(element, encoding="unicode"))
        super().__init__(self.message)


class FailedTextExtractionException(Exception):
    def __init__(self, element):
        self.message = str(ET.tostring(element, encoding="unicode"))
        super().__init__(self.message)


class HansardSpeechExtractor:

    def _clean_hansard(self, string):
        # Step 1: Strip problematic declarations
        lines = string.split("\n")
        if lines and ("DOCTYPE" in lines[0] or "encoding" in lines[0]):
            string = "\n".join(lines[1:])

        # Step 2: Replace character entities
        char_map = {
            "&mdash;": "---",
            "&nbsp;": " ",  # optional: handles Word exports
        }
        for k, v in char_map.items():
            string = string.replace(k, v)

        # Step 3: Remove unbound namespace-prefixed tags (mc:, v:, o:, w10:, etc.)
        # This prevents XML parser from failing
        string = re.sub(r"<(/?)(mc|v|o|w10|w|o14|m):[^>]*>", "", string)
        string = re.sub(
            r'\s(xmlns:[a-zA-Z0-9]+)="[^"]+"', "", string
        )  # remove xmlns decls
        string = re.sub(
            r'\s[a-zA-Z0-9]+:[a-zA-Z0-9\-]+="[^"]*"', "", string
        )  # remove prefix:attr="..."

        # Step 4: Parse using forgiving HTML parser
        try:
            repaired = html.fromstring(string)
            ET.strip_tags(repaired, ET.Comment)
            fixed_xml = html.tostring(repaired, method="xml").decode()
        except etree.XMLSyntaxError:
            raise FailedTextExtractionException(
                "XML could not be parsed even after cleaning."
            )

        return fixed_xml

    def __init__(self, source, date=None, from_file=True):
        """
        :param source: XML filename or string, depending on from_file.
        :param from_file: If True, treat source as filename. If False, treat as string.
        """
        if from_file:
            hansard_string = open(source).read()
        else:
            hansard_string = source

        if len(hansard_string) == 0:
            raise EmptyDocumentError()

        cleaned_string = self._clean_hansard(hansard_string)
        self.tree = ET.fromstring(cleaned_string)
        self.root = self.tree

        if date:
            self.date = date
        else:
            self.date = self.root.attrib.get("DATE", None)
        full_date = datetime.datetime.strptime(self.date, "%Y-%m-%d")

    def _find_session_date(self):
        date_elem = self.root.find(".//session.header/date")
        return (
            date_elem.text.strip()
            if date_elem is not None and date_elem.text
            else None
        )

    def _extract_elements(self):
        check_elements = self.root.xpath(
            ".//speech | .//question | .//answer | .//petition"
        )

        # If no relevant elements found, raise an exception
        if not check_elements:
            raise EmptyDocumentError()

        self.elements = []
        # Iterate over document to get all the items
        raw_elements = list(self.tree.iter())
        i = 0
        while i < len(raw_elements):
            el = raw_elements[i]
            tag = el.tag.lower()
            if tag == "question":
                parent = el.getparent()
                answer_ls = [
                    child
                    for child in parent
                    if child is not el and child.tag.lower() == "answer"
                ]
                if len(answer_ls) != 0:
                    self.elements.append(
                        {
                            "type": "question",
                            "question": self._clean_element(el),
                            "answer": self._clean_element(answer_ls[0]),
                        }
                    )
                ## Exception weh threre is no answer
                else:
                    self.elements.append(
                        {
                            "type": "question",
                            "element": self._clean_element(el),
                        }
                    )

                i += 1
            elif tag == "speech":
                self.elements.append(
                    {"type": "speech", "element": self._clean_element(el)}
                )
            elif tag == "petition":
                self.elements.append(
                    {"type": "petition", "element": self._clean_element(el)}
                )

            i += 1

    def extract(self):
        self._extract_elements()
        results = []
        for elem in self.elements:
            if elem["type"] == "question" and "answer" in elem.keys():
                # If there is a valid question
                valid_question = self._extract_text(elem["question"])
                valid_answer = self._extract_text(elem["answer"])
                if valid_question and valid_answer:
                    entry = {
                        "type": "question",
                        "author": self._extract_talker(elem["question"]),
                        "text": self._extract_text(elem["question"]),
                        "date": self.date,
                        "answer": {
                            "type": "answer",
                            "author": self._extract_talker(elem["answer"]),
                            "text": self._extract_text(elem["answer"]),
                            "date": self.date,
                        },
                    }
                    results.append(entry)
                elif valid_answer and not valid_answer:
                    entry = {
                        "type": "answer",
                        "author": self._extract_talker(elem["answer"]),
                        "text": self._extract_text(elem["answer"]),
                        "date": self.date,
                    }
                    results.append(entry)
                elif valid_question and not valid_answer:
                    entry = {
                        "type": "question",
                        "author": self._extract_talker(elem["question"]),
                        "text": self._extract_text(elem["question"]),
                        "date": self.date,
                    }
                    results.append(entry)

            else:
                if self._extract_text(elem["element"]):
                    entry = {
                        "type": elem["type"],
                        "author": self._extract_talker(elem["element"]),
                        "text": self._extract_text(elem["element"]),
                        "date": self.date,
                    }
                    results.append(entry)

        return results

    def _clean_element(self, el):
        for interjection in el.xpath(".//interjection"):
            parent = interjection.getparent()
            if parent is not None:
                parent.remove(interjection)
        return el

    def _extract_talker(self, elem):
        try:
            names = elem.xpath(".//name.id/text()")
            unique_names = set(names)
            return list(unique_names)[0]
        except:
            pass
        try:
            nameids = elem.xpath(".//NAME/@NAMEID")
            unique_nameids = set(nameids)
            return list(unique_nameids)[0]
        except:
            pass
        try:
            nameids = elem.xpath(".//@nameid")
            unique_nameids = set(nameids)
            return list(unique_nameids)[0]
        except:
            pass

        # try:
        #     names = elem.xpath('.//name[@role="metadata"]/text()')
        #     unique_names = set(names)
        #     return list(unique_names)[0]
        # except:
        #     pass
        # try:
        #     names = elem.xpath('.//name[@role="display"]/text()')
        #     unique_names = set(names)
        #     return list(unique_names)[0]
        # except:
        #     pass
        # try:
        #     names = elem.xpath(".//name/text()")
        #     unique_names = set(names)
        #     return list(unique_names)[0]
        # except:
        #     pass

        # if "speaker" in elem.attrib:
        #     return elem.attrib.get("speaker", "")

        # if len([x for x in elem]) == 1:
        #     if [x for x in elem][0].tag in ["p", "para"]:
        #         return ""
        # if len([x for x in elem]) == 0:
        #     return ""
        # if all(
        #     x.tag
        #     in ["p", "para", "quote", "inline", "list", "item", "debateinfo"]
        #     for x in elem
        # ):
        #     return ""
        print(str(ET.tostring(elem, encoding="unicode")))
        return ""

        raise FailedTalkerExtractionException(elem)

    def _extract_text(self, elem):
        texts = []
        # Extract all <para> or <p>
        elements = elem.xpath(".//para | .//p")
        for p in elements:
            para_text = re.sub(r"\s+", " ", "".join(p.itertext())).strip()
            if para_text:
                texts.append(para_text)

        # If text was found in <para>/<p>, return it
        if texts:
            return "\n".join(texts)


def print_tag_tree(element, max_depth, indent=0):
    if indent >= max_depth:
        return
    print("  " * indent + f"{element.tag}")
    for child in element:
        print_tag_tree(child, max_depth, indent + 1)


async def main():
    db = Prisma()
    await db.connect()
    groups = {
        "House of Reps Hansard": None,
        "Senate Hansard": None,
        "Hansard": None,
    }
    for group_name in groups.keys():
        g = await db.sourcegroup.find_unique(where={"name": group_name})
        if not g:
            g = await db.sourcegroup.create({"name": group_name})
        groups[group_name] = g.id

    base_path = "./scrapers/raw_sources/hansard"
    folders = ["senate", "hofreps"]

    all_files = []
    for folder in folders:
        folder_path = os.path.join(base_path, folder)
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            # Optionally, join folder name for full paths:
            files = [os.path.join(folder_path, f) for f in files]
            all_files.extend(files)

    all_files = sorted(all_files)

    for filename in tqdm(all_files, total=len(all_files)):
        ## Generate the filenames
        names = filename.split("/")
        source_name = f'{"Senate" if names[-2] == "senate" else "House of Representatives"} {names[-1][:10]}'

        ## Either grab the source, or create the source
        ## We are going to assume if the source exists then we are done.
        source = await db.source.find_unique(where={"name": source_name})
        if not source:
            source = await db.source.create(
                data={
                    "name": source_name,
                    "script": "parser/hansard.py",
                    "file": filename,
                    "groups": {
                        "connect": [
                            {"id": groups["Hansard"]},
                            {
                                "id": (
                                    groups["Senate Hansard"]
                                    if "Senate" in source_name
                                    else groups["House of Reps Hansard"]
                                )
                            },
                        ]
                    },
                }
            )

            try:
                self = HansardSpeechExtractor(filename, date=names[-1][:10])
                results = self.extract()
                if len(results) == 0:
                    raise Exception(f"{filename} failed to parse")
                for document in results:
                    if (
                        document["type"] == "question"
                        and "answer" in document.keys()
                    ):
                        await db.document.create(
                            data={
                                "text": document["text"],
                                "date": datetime.datetime.strptime(
                                    document["date"], "%Y-%m-%d"
                                ),
                                "type": document["type"],
                                "author": {
                                    "connectOrCreate": {
                                        "where": {
                                            "rawName": document["author"],
                                        },
                                        "create": {
                                            "rawName": document["author"],
                                        },
                                    }
                                },
                                "source": {"connect": {"id": source.id}},
                                "citedBy": {
                                    "create": {
                                        "text": document["answer"]["text"],
                                        "date": datetime.datetime.strptime(
                                            document["answer"]["date"],
                                            "%Y-%m-%d",
                                        ),
                                        "type": document["answer"]["type"],
                                        "source": {
                                            "connect": {"id": source.id}
                                        },
                                        "author": {
                                            "connectOrCreate": {
                                                "where": {
                                                    "rawName": document[
                                                        "answer"
                                                    ]["author"],
                                                },
                                                "create": {
                                                    "rawName": document[
                                                        "answer"
                                                    ]["author"],
                                                },
                                            },
                                        },
                                    },
                                },
                            }
                        )
                    else:
                        await db.document.create(
                            data={
                                "text": document["text"],
                                "date": datetime.datetime.strptime(
                                    document["date"], "%Y-%m-%d"
                                ),
                                "type": document["type"],
                                "author": {
                                    "connectOrCreate": {
                                        "where": {
                                            "rawName": document["author"],
                                        },
                                        "create": {
                                            "rawName": document["author"],
                                        },
                                    }
                                },
                                "source": {"connect": {"id": source.id}},
                            }
                        )

            except EmptyDocumentError:
                pass


if __name__ == "__main__":
    asyncio.run(main())
