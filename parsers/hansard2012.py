from parsers.hansard_extractor import HansardExtractor, print_tag_tree
from parsers.chamber_speech_extractor import ChamberSpeechExtractor
from parsers.eras import SpeechExtractorModern

from parsers.errors import *



class SpeechExtractor2012(SpeechExtractorModern):

    def _interjection_type_inline(self, et_elem):
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
            return "general"
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
                for role in ["SPEAKER", "DEPUTY", "CLERK", "PRESIDENT", "CHAIR"]
            ):
                return "office"
            else:
                return "speaker"
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
            return "general"
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
            file_text, ChamberSpeechExtractor, SpeechExtractor2012
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results

