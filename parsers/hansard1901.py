from parsers.hansard_extractor import HansardExtractor
from parsers.chamber_speech_extractor import ChamberSpeechExtractor
from parsers.eras import SpeechExtractorMassDigitisation

from parsers.errors import *
import re
import string


class SpeechExtractor1901(SpeechExtractorMassDigitisation):

    def _get_speech_element_children(self, elem):
        # The tags that "contain" others
        container_tags = {"talk.start", "continue", "interjection"}
        # The tags to nest inside the most recent container
        nest_tags = {"quote", "list"}

        # Make a list to hold the processed children
        result = []
        # Pointer to the most recent container element
        current_container = None

        for child in elem.getchildren():
            tag = child.tag.lower()
            if tag in container_tags:
                result.append(child)
                current_container = child
            elif tag in nest_tags:
                # If we've seen a container, make this a child
                if current_container is not None:
                    current_container.append(child)
                else:
                    # Optionally: handle or skip orphaned nest tags
                    # Uncomment next line if you want to keep them at top level
                    # result.append(child)
                    pass
            else:
                # Other elements, keep as is or handle as needed
                result.append(child)

        return result

    def _extract_talker(self, elem):
        result = elem.find("talk.start/talker/name.id")
        if result is None:
            result = elem.find("talker/name.id")
        continues = elem.findall("continue/talk.start/talker/name.id")
        alt_name_ids = [x.text for x in continues if x.text != "10000"]

        ## Special case where speaker interjects before the main speaker of the speech
        # In this case, take the first available alt_name_id
        if result is not None:
            if result.text == "10000" and alt_name_ids:
                return alt_name_ids[0]
            else:
                return result.text

        elif len(set(alt_name_ids)) == 1:
            return alt_name_ids[0]
        
        else:
            return ""


    def _interjection_type(self, et_elem):
        if et_elem.tag.lower() in {"talk.start"}:
            author = et_elem.find("talker/name.id")
            if author is not None and author.text == "10000":
                return "office"
        elif et_elem.tag.lower() in {"continue"}:
            author = et_elem.find("talk.start/talker/name.id")
            if author is not None and author.text == "10000":
                return "office"
        return "speaker"



def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor1901
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results


