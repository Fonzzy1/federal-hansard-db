from parsers.hansard_base_model import (
    HansardExtractor,
    SpeechExtractor,
    ChamberSpeechExtractor,
)

from parsers.errors import *


class SpeechExtractor1981(SpeechExtractor):

    def _get_speech_element_children(self, elem):
        return elem.getchildren()

    def _extract_talker(self, elem):
        result = elem.get("nameid")
        if result:
            return result
        else:
            return ""

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

    def _interjection_type(self, et_elem):
        if et_elem.get("chair") == "1":
            return "office"
        
        # Para elements with "interjecting" are always general interjections
        if et_elem.tag.lower() == "para":
            para_text = "".join(t.strip() for t in et_elem.itertext())
            para_text = para_text.translate(str.maketrans("", "", "—\"':,.!?"))
            words = para_text.split()
            if len(words) < 5 and any("interject" in w.lower() for w in words):
                return "general"
        
        return "speaker"


def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor1981
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results
