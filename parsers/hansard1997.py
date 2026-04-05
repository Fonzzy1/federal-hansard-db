from parsers.hansard_extractor import HansardExtractor
from parsers.chamber_speech_extractor import ChamberSpeechExtractor
from parsers.eras import SpeechExtractorEarlyDigital
from parsers.hansard1992 import SpeechExtractor1992

from parsers.errors import *
import string


class SpeechExtractor1997(SpeechExtractorEarlyDigital):

    def _interjection_type(self, et_elem):
        if self._extract_talker(et_elem) == "10000":
            return "office"
        else:
            return "speaker"



def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor1997
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results
