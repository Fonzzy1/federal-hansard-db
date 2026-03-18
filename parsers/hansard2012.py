from parsers.hansard_base_model import (
    HansardExtractor,
    ChamberSpeechExtractor,
    print_tag_tree,
)
from parsers.eras import SpeechExtractorModern

from parsers.errors import *
import string

import re


class SpeechExtractor2012(SpeechExtractorModern):

    def __init__(self, element):
        super().__init__(element)
        self.name_to_href = {}





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

