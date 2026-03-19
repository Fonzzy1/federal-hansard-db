from parsers.hansard_extractor import HansardExtractor, print_tag_tree
from parsers.chamber_speech_extractor import ChamberSpeechExtractor
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


