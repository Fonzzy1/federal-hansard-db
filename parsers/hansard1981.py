from parsers.hansard_base_model import (
    HansardExtractor,
    ChamberSpeechExtractor,
)
from parsers.eras import SpeechExtractorEarlyDigital

from parsers.errors import *


class SpeechExtractor1981(SpeechExtractorEarlyDigital):

    def _get_speech_element_children(self, elem):
        return elem.getchildren()



    def _is_interjection_element(self, et_elem):
        """
        Returns True if the element is an interjection, otherwise False.
        """
        # Check element tag
        if et_elem.tag.lower() in {"interject", "interjection"}:
            return True
        
        # Check for para elements with "interjecting" in them (less than 5 words = general interjection)
        if et_elem.tag.lower() == "para":
            para_text = "".join(t.strip() for t in et_elem.itertext())
            # Remove punctuation
            para_text = para_text.translate(str.maketrans("", "", "—\"':,.!?"))
            words = para_text.split()
            if len(words) < 5 and any("interject" in w.lower() for w in words):
                return True
        
        return False



def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor1981
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results
