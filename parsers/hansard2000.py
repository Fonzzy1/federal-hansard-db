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
            
            # If the only content is in an italic inline block, it's unrecorded
            # e.g., <para><inline font-style="italic">Senator Abetz interjecting—</inline></para>
            inline_italic = para.find("inline[@font-style='italic']")
            if inline_italic is not None:
                # Check if this is the only content (no other text)
                para_text = "".join(para.itertext()).strip()
                italic_text = "".join(inline_italic.itertext()).strip()
                if para_text == italic_text:
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

