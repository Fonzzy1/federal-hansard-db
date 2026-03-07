from hansard_base_model import (
    HansardExtractor,
    SpeechExtractor,
    ChamberSpeechExtractor,
    print_tag_tree,
)

from errors import *
import string

import re


class SpeechExtractor2012(SpeechExtractor):

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
            return result.text

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
            return 10000

        raise FailedTalkerExtractionException(elem)

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
                return True

            # Or a contiuation or speech by the speaker
            elif class_attr in {
                "HPS-MemberSpeech",
            }:
                member_continuation_text = span.text
                if member_continuation_text and any(
                    role in member_continuation_text
                    for role in ["SPEAKER", "CLERK", "PRESIDENT"]
                ):
                    return True
        return False

    def _interjection_type(self, et_elem):
        try:
            a_element = et_elem.find("./span/a/span")
            if a_element is None:
                a_elements = et_elem.find("span").findall("span")
                i = 0
                while not (a_element is not None and a_element.text):
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
        if t == "HPS-OfficeSpeech":
            return "office"
        if t == "HPS-OfficeContinuation":
            return "office"
        if t == "HPS-MemberIInterjecting":
            return "unrecorded"
        if t == "HPS-GeneralIInterjecting":
            return "general"
        if t == "HPS-GeneralInterjecting":
            return "general"
        if t == "HPS-GeneralInterjecting":
            return "general"
        if t == "HPS-MemberInterjecting":
            member_text = a_element.text
            if member_text and any(
                role in member_text
                for role in ["SPEAKER", "CLERK", "PRESIDENT"]
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
            file_text, ChamberSpeechExtractor, SpeechExtractor2012
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results


if __name__ == "__main__":

    with open("../tests/2012.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2013.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2014.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2015.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2016.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2017.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2017.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2018.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2019.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2020.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2021.xml") as r:
        text = r.read()
    t = parse(text)
