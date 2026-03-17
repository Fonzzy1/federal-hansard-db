from parsers.hansard_base_model import (
    HansardExtractor,
    ChamberSpeechExtractor,
    print_tag_tree,
)
from parsers.hansard2012 import SpeechExtractor2012
from parsers.errors import *
import string

import re


class SpeechExtractor2021(SpeechExtractor2012):

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

        if interjections:
            interjections, text = self._interjection_fix(interjections, text, author)

        return author, interjections, text

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

    def _get_a_element(self,et_elem):
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


    def _interjection_type(self, et_elem):
        a_element = self._get_a_element(et_elem)
        if  a_element is None:
            return False


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



def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor2021
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results
