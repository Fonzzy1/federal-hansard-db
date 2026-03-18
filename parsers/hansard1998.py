from parsers.hansard_base_model import (
    HansardExtractor,
    ChamberSpeechExtractor,
    print_tag_tree,
)
from parsers.eras import SpeechExtractorMassDigitisation

from parsers.errors import *
import string


class SpeechExtractor1998(SpeechExtractorMassDigitisation):
    pass



def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor1998
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results


