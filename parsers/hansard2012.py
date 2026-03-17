from parsers.hansard_base_model import (
    HansardExtractor,
    ChamberSpeechExtractor,
    print_tag_tree,
)
from parsers.hansard2011 import SpeechExtractor2011
from parsers.errors import *
import string

import re


class SpeechExtractor2012(SpeechExtractor2011):

    def __init__(self, element):
        super().__init__(element)
        self.name_to_href = {}

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
                for role in ["SPEAKER", "CLERK", "PRESIDENT", "CHAIR"]
            ):
                return "office"
            else:
                return "speaker"
        return False

def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor2012
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results
