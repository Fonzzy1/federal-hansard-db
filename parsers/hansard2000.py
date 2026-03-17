from parsers.hansard_base_model import (
    HansardExtractor,
    ChamberSpeechExtractor,
)

from parsers.hansard1998 import SpeechExtractor1998
from parsers.errors import *


class SpeechExtractor2000(SpeechExtractor1998):
    """
    For years 2000 onwards.
    Difference from 1998: if interjection has no text, it's an unrecorded interjection.
    """

    def _interjection_type(self, et_elem):
        # Check if interjection has no text content
        text_content = self._pull_paras(et_elem)
        if not text_content or not text_content.strip():
            return "unrecorded"
        
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
