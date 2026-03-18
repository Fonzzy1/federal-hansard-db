from parsers.hansard_base_model import (
    HansardExtractor,
    ChamberSpeechExtractor,
)

from parsers.eras import SpeechExtractorMassDigitisation
from parsers.errors import *

import string


class SpeechExtractor2000(SpeechExtractorMassDigitisation):
    """
    For years 2000 onwards.
    Difference from 1998: if interjection has no text, it's an unrecorded interjection.
    """

    def extract(self):
        author = self._extract_talker(self.root)
        interjections, text = self._extract_text(
            self.root, record_office_interjector=True,
            record_unrecored_interjector=True
        )
        return author, interjections, text

    def _interjection_type(self, et_elem):
        # Check if this is an unrecorded interjection:
        # Has a talk.start element but no para (actual text) within it
        talk_start = et_elem.find(".//talk.start")
        if talk_start is not None:
            # If there's no para element within talk.start, it's unrecorded
            para = talk_start.find("para")
            if para is None:
                return "unrecorded"
            text, desc = self._extract_text_and_description(et_elem)
            text_clean = self._clean_text(text)
            desc_clean = self._clean_text(desc)
            if text_clean:
                return 'speaker'
            elif desc_clean:
                return 'unrecorded'
           
        if et_elem.tag.lower() == 'para':
            text, desc = self._extract_text_and_description(et_elem)

            # Remove punctuation and whitespace before checking
            text_clean = self._clean_text(text)
            desc_clean = self._clean_text(desc)
            if text_clean and desc_clean:
                return 'unattributed'
            elif desc_clean:
                return 'general'
            
        # Otherwise, use the 1998 logic
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


