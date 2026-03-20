from parsers.hansard_extractor import HansardExtractor
from parsers.chamber_speech_extractor import ChamberSpeechExtractor

from parsers.eras import SpeechExtractorMassDigitisation
from parsers.errors import *

import string


class SpeechExtractor2000(SpeechExtractorMassDigitisation):
    def _interjection_type(self, et_elem):
        # Check if this is an unrecorded interjection:
        # Has a talk.start element but no para (actual text) within it
        talk_start = et_elem.find(".//talk.start")
        if talk_start is not None:
            # If there's no para element within talk.start, it's a general
            # without a description
            para = talk_start.find("para")
            if para is None:
                return "general"
            # There might be an description only element here for a unrecored
            # intejection that needs to be caught
            else:
                # See if there is an inline. If there is no text before the
                # inline then it is a description and needs to be parsed as a
                # general interjection
                if para.find("inline") is not None and (not para.text or (para.text and not para.text.strip())):
                        return 'general'
            
        # Otherwise, use the unversal logic
        return super()._interjection_type(et_elem)


def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor2000
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results


