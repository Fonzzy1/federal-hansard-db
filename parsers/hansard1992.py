from parsers.hansard_extractor import HansardExtractor
from parsers.chamber_speech_extractor import ChamberSpeechExtractor
from parsers.eras import SpeechExtractorEarlyDigital

from parsers.errors import *
import string


class SpeechExtractor1992(SpeechExtractorEarlyDigital):


    def _extract_talker(self, elem):
        result = elem.get("nameid")
        if result:
            return result
        return ""

    def _interjection_type(self, et_elem):
        # If the usual attribute is present, use it
        if et_elem.tag.lower() in {"interject", "interjection"}:
            if et_elem.get("chair") == "1":
                return "office"
            else:
                return "speaker"

        # Else, check if this is a PARA with a bold procedural keyword
        if et_elem.tag.lower() == "para":
            child = et_elem.find(".//emphasis")
            ## TODO again check the bolding thingo
            if child is not None:
                if (
                    child.attrib.get("font-weight", "") == "BOLD"
                    and child.text is not None
                ):
                    return "office"
                elif (
                    child.attrib.get("font-slant", "") == "ITAL"
                    and child.text is not None
                ):
                    return "general"



def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor1992
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results

