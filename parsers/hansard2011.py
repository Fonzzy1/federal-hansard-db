from parsers.hansard_base_model import (
    HansardExtractor,
    SpeechExtractor,
    ChamberSpeechExtractor,
    print_tag_tree,
)

from parsers.errors import *
import string

import re


class SpeechExtractor2011(SpeechExtractor):

    def __init__(self, element):
        super().__init__(element)
        self.name_to_href = {}

    def extract(self):
        author = self._extract_talker(self.root)
        interjections, text = self._extract_text(
            self.root, record_office_interjector=True
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
        result = elem.find("talk.start/talker/name.id")
        if result is not None:
            if result.text:
                return result.text
            else:
                return ""

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

        return ""

    def _is_interjection_element(self, et_elem):
        """
        Returns True if the element is an interjection, otherwise False.
        """
        # All elements are paras now
        for span in et_elem.findall(".//span"):
            class_attr = span.get("class", "")
            if class_attr in [
                "HPS-MemberIInterjecting",
                "HPS-GeneralIInterjecting",
                "HPS-MemberInterjecting",
                "HPS-GeneralInterjecting",
            ]:
                return True

            # Or a contiuation or speech by the speaker
            elif class_attr in {
                "HPS-MemberContinuation",
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
        a_element = et_elem.find("./span/a/span")
        if a_element is None:
            a_elements = et_elem.find("span").findall("span")
            i = 0
            while i < len(a_elements) and not (a_element is not None and a_element.text):
                a_element = a_elements[i]
                i += 1
            if a_element is None or not a_element.text:
                return False

        t = a_element.get("class")

        # In this case we know it has to be the speaker becuase you wont
        # interject yourself
        if t == "HPS-MemberContinuation":
            return "office"
        # In this case we know it has to be the speaker becuase you wont
        # interject yourself
        if t == "HPS-MemberSpeech":
            return "office"
        if t == "HPS-MemberIInterjecting":
            return "unrecorded"
        if t == "HPS-GeneralIInterjecting":
            return "general"
        if t == "HPS-GeneralInterjecting":
            return "general"
        if t == "HPS-MemberInterjecting":
            if a_element.getparent().get("href"):
                return "speaker"
            else:
                return "general"

        if t == "HPS-GeneralInterjecting":
            return "general"

    def _clean_text(self, text):
        return text.lstrip(" -.,;:!?\t\n\r")


def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor2011
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results


if __name__ == "__main__":

    with open("../tests/2011.xml") as r:
        text = r.read()
    t = parse(text)

    # Should be empty
    [
        x
        for x in t[0]["documents"]
        if "members interjecting"
        in x.get("answer", {"text": ""})["text"] + x["text"]
    ]

    # Test to see if we get type 2 interjections
    [
        x
        for x in t[0]["documents"]
        if any(
            [
                y["type"] == 2
                for y in x["interjections"]
                + x.get("answer", {"interjections": []})["interjections"]
            ]
        )
    ]

    # Test to see if we get type 4 interjections
    [
        x
        for x in t[0]["documents"]
        if any(
            [
                y["type"] == 4
                for y in x["interjections"]
                + x.get("answer", {"interjections": []})["interjections"]
            ]
        )
    ]

    # Test to see if we get type 3 interjections
    [
        x
        for x in t[0]["documents"]
        if any(
            [
                y["type"] == 3
                for y in x["interjections"]
                + x.get("answer", {"interjections": []})["interjections"]
            ]
        )
    ]
    # Test to see if there are Order where there shouldn't be.
    # Should be emptyish
    [
        x
        for x in t[0]["documents"]
        if "Order" in x.get("answer", {"text": ""})["text"] + x["text"]
    ]

    # Test to see if we get type bad orders
    [
        x
        for x in t[0]["documents"]
        if any(
            [
                y["type"] != 3 and "Order" in y["text"]
                for y in x["interjections"]
                + x.get("answer", {"interjections": []})["interjections"]
            ]
        )
    ]
