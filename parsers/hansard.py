from prisma import Prisma
import argparse
import asyncio
import os
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
import datetime
import re
from lxml import html
import lxml.etree as ET


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

    def __init__(self, source, date=None, from_file=False):
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
            self.date = self._find_session_date()
            print(self.date)

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
        # print(str(ET.tostring(elem, encoding="unicode")))
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


def parse(file_text):
    extractor = HansardSpeechExtractor(file_text)
    results = extractor.extract()
    return results
