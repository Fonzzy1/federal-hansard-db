from parsers.hansard_base_model import (
    HansardExtractor,
    ChamberSpeechExtractor,
    print_tag_tree,
)
from parsers.eras import SpeechExtractorModern

from parsers.errors import *
import string

import re


class SpeechExtractor2011(SpeechExtractorModern):

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
                "HPS-MemberIInterjecting",
                "HPS-GeneralIInterjecting",
                "HPS-MemberInterjecting",
                "HPS-GeneralInterjecting",
                "HPS-OfficeInterjecting"
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
        a_element = self._get_a_element(et_elem)
        if  a_element is None:
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

def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor2011
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results

