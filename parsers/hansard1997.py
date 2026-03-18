from parsers.hansard_base_model import (
    HansardExtractor,
    ChamberSpeechExtractor,
)
from parsers.eras import SpeechExtractorEarlyDigital
from parsers.hansard1992 import SpeechExtractor1992

from parsers.errors import *
import string


class SpeechExtractor1997(SpeechExtractorEarlyDigital):

    def _interjection_type(self, et_elem):
        # If the usual attribute is present, use it
        if et_elem.tag.lower() in {"interject", "interjection"}:
            if self._extract_talker(et_elem) == "10000":
                return "office"
            else:
                return "speaker"

        # Else, check if this is a PARA with a bold procedural keyword
        if et_elem.tag.lower() == "para":
            child = et_elem.find(".//emphasis")
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
            file_text, ChamberSpeechExtractor, SpeechExtractor1997
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results
