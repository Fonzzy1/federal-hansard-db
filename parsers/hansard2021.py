from parsers.hansard_base_model import (
    HansardExtractor,
    SpeechExtractor,
    ChamberSpeechExtractor,
    print_tag_tree,
)

from parsers.errors import *
import string

import re


class SpeechExtractor2021(SpeechExtractor):

    def __init__(self, element):
        super().__init__(element)
        self.name_to_href = {}

    def extract(self):
        author = self._extract_talker(self.root)
        interjections, text = self._extract_text(
            self.root,
            record_office_interjector=True,
            record_unrecored_interjector=True,
        )

        # Dirty fix for when the whole thing is an 'interjection'
        if interjections:
            # Check if the speech is owened by a office holder
            if (
                author == interjections[0]["author"]
                and interjections[0]["type"] == 3
            ):
                # If so, then the whole thing is actually an interjetion
                secs = re.split(r"\[INTERJECTION\d+\]", text)
                # The first element is going to be empty - so now lets allocate
                # the index = 1 element to the initial interjection
                first_section = secs[1]
                text = text.replace(first_section, "")
                interjections[0]["text"] += first_section

        return author, interjections, text

    def _get_speech_element_children(self, elem):
        # The tags that "contain" others
        elems = elem.find("talk.text").getchildren()
        return elems

    def _extract_talker(self, elem):
        # Case when we are looking at speeches
        # Case when we are looking at speeches
        result = elem.find("talk.start/talker/name.id")
        if result is not None:
            if result.text:
                return result.text
            else:
                return ""

        # case when we are getting a inline general inerjection
        if elem.tag.lower() == "a" and elem.get("href"):
            return elem.get("href")

        # Case when we are looking at interjections
        a_element = elem.find("./span/a")
        if a_element is not None and a_element.get("href"):
            href = a_element.get("href")
            name_text = "".join(
                char
                for char in elem.find("./span/a/span").text
                if char.isalnum()
            )
            self.name_to_href[name_text] = href
            return href
        elif a_element is None:
            name_text = elem.find("./span/span").text
            if name_text:
                name_text = "".join(
                    char for char in name_text if char.isalnum()
                )
                potential_id = self.name_to_href.get(name_text)
                if potential_id:
                    return potential_id
        # Finaly if we have an interjection element, and we dont know, give
        # 10000
        if self._interjection_flag(elem) == 3:
            return "10000"

        else:
            return ""

    def _is_interjection_element(self, et_elem):
        """
        Returns True if the element is an interjection, otherwise False.
        """
        # All elements are paras now
        for span in et_elem.findall(".//span"):
            class_attr = span.get("class", "")
            if class_attr in [
                "HPS-OfficeInterjecting",
                "HPS-OfficeContinuation",
                "HPS-OfficeSpeech",
                "HPS-MemberIInterjecting",
                "HPS-GeneralIInterjecting",
                "HPS-MemberInterjecting",
                "HPS-GeneralInterjecting",
            ]:
                if span.text and span.text.strip():
                    return True

            # Or a contiuation or speech by the speaker
            elif class_attr in {
                "HPS-MemberSpeech",
            }:
                member_continuation_text = span.text
                if member_continuation_text and any(
                    role in member_continuation_text
                    for role in ["SPEAKER", "CLERK", "PRESIDENT", "CHAIR"]
                ):
                    return True
        return False

    def _interjection_type(self, et_elem):

        try:
            a_element = et_elem.find("./span/a/span")
            if a_element is None and et_elem.tag.lower() == "a":
                a_element = et_elem.find("./p/span")
                a_elements = a_element.findall("span")
            elif a_element is None:
                a_elements = et_elem.find("span").findall("span")
            i = 0
            while not (
                a_element is not None
                and a_element.text
                and a_element.text.strip()
            ):
                a_element = a_elements[i]
                i += 1
        except:
            raise FailedInterjectionTypeAssingment(et_elem)

        t = a_element.get("class")

        # In this case we know it has to be the speaker becuase you wont
        # interject yourself
        if t == "HPS-MemberSpeech":
            return "office"
        if t == "HPS-OfficeInterjecting":
            return "office"
        if t == "HPS-OfficeContinuation":
            return "office"
        if t == "HPS-GeneralIInterjecting":
            if et_elem.attrib.get("href"):
                return "unrecorded"
            else:
                return "general"
        if t == "HPS-GeneralInterjecting":
            return "general"
        if t == "HPS-GeneralInterjecting":
            return "general"
        if t == "HPS-MemberInterjecting":
            member_text = ""
            name_spans = et_elem.xpath(
                ".//span[contains(@class, 'HPS-MemberInterjecting')]"
            )
            for span in name_spans:
                if span.text:
                    member_text += span.text.strip()
            member_text = member_text.strip().replace(" ", "")
            if any(
                role in member_text
                for role in ["SPEAKER", "CLERK", "PRESIDENT", "CHAIR"]
            ):
                return "office"
            else:
                return "speaker"
        return False

    def _clean_text(self, text):
        return text.lstrip(" -.,;:!?\t\n\r")


def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor2021
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results


if __name__ == "__main__":

    with open("tests/2022.xml") as r:
        text = r.read()
    t = parse(text)

    with open("tests/2023.xml") as r:
        text = r.read()
    t = parse(text)

    with open("tests/2024.xml") as r:
        text = r.read()
    t = parse(text)

    with open("tests/2025.xml") as r:
        text = r.read()
    t = parse(text)

    with open("tests/2025a.xml") as r:
        text = r.read()
    t = parse(text)

    with open("tests/2026.xml") as r:
        text = r.read()
    t = parse(text)

    # Should be empty
    [
        x
        for x in t[0]["documents"]
        if "members interjecting"
        in x.get("answer", {"text": ""})["text"] + x["text"]
    ]

    [
        type1
        for x in t[0]["documents"]
        for type1 in x["interjections"]
        + x.get("answer", {"interjections": []})["interjections"]
        if type1["type"] == 1
    ]

    # General interjections
    [
        type2
        for x in t[0]["documents"]
        for type2 in x["interjections"]
        + x.get("answer", {"interjections": []})["interjections"]
        if type2["type"] == 2
    ]

    # office inerections - check for 10000s
    [
        type3
        for x in t[0]["documents"]
        for type3 in x["interjections"]
        + x.get("answer", {"interjections": []})["interjections"]
        if type3["type"] == 3
    ]

    # Unrecorded
    [
        type4
        for x in t[0]["documents"]
        for type4 in x["interjections"]
        + x.get("answer", {"interjections": []})["interjections"]
        if type4["type"] == 4
    ]

    # Checking bad interjection types
    # Speaker not in a type 3 interjection
    [
        type3
        for x in t[0]["documents"]
        for type3 in x["interjections"]
        + x.get("answer", {"interjections": []})["interjections"]
        if type3["type"] != 3
        and any(p in type3["text"] for p in ["PRESIDENT", "CLERK", "SPEAKER"])
    ]

    # interjectiing only for 2 and 4
    [
        type3
        for x in t[0]["documents"]
        for type3 in x["interjections"]
        + x.get("answer", {"interjections": []})["interjections"]
        if type3["type"] not in [2, 4]
        and any(p in type3["text"] for p in ["interjecting"])
    ]

    # Check content in speeches
    [
        type3
        for x in t[0]["documents"]
        for type3 in x.get("answer", {"text": ""})["text"] + x["text"]
        if any(p in type3 for p in ["PRESIDENT", "CLERK", "SPEAKER"])
    ]

    # Check content in speeches
    [
        type3
        for x in t[0]["documents"]
        for type3 in x.get("answer", {"text": ""})["text"] + x["text"]
        if any(p in type3 for p in ["interjecting"])
    ]

elem = ET.fromstring("""
<p class="HPS-Normal" style="direction:ltr;unicode-
bidi:normal;">
                  <span class="HPS-Normal">
                    <span class="HPS-MemberInterjecting">The CHAIR:</span>  The question is that pa
rt 2 of schedule 1 stand as printed.</span>
                </p>
                     """)
