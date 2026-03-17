from parsers.hansard_base_model import (
    HansardExtractor,
    SpeechExtractor,
    ChamberSpeechExtractor,
)

from parsers.errors import *
import re


class SpeechExtractor1901(SpeechExtractor):

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
        
        # If no talker found and element is a para with bold text, extract the bold content
        elif elem.tag.lower() == 'para' and self._is_interjection_element(elem):
            child = elem.find("./inline")
            if child is not None and child.attrib.get("font-weight", "") == "bold":
                return child.text
        
        else:
            return ""

    def _is_interjection_element(self, et_elem):
        """
        Returns True if the element is an interjection, otherwise False.
        """
        # Check element tag
        if et_elem.tag.lower() in {"interject", "interjection"}:
            return True
        if et_elem.tag.lower() in {"talk.start"}:
            author = et_elem.find("talker/name.id")
            if author is not None and author.text == "10000":
                return True
        if et_elem.tag.lower() in {"continue"}:
            author = et_elem.find("talk.start/talker/name.id")
            if author is not None and author.text == "10000":
                return True
        if et_elem.tag.lower() == 'para':
            child = et_elem.find("./inline")
            if child is not None and child.attrib.get("font-weight", "") == "bold":
                return True
        else:
            return False

    def _interjection_type(self, et_elem):
        if et_elem.tag.lower() in {"talk.start"}:
            author = et_elem.find("talker/name.id")
            if author is not None and author.text == "10000":
                return "office"
        elif et_elem.tag.lower() in {"continue"}:
            author = et_elem.find("talk.start/talker/name.id")
            if author is not None and author.text == "10000":
                return "office"
        elif et_elem.tag.lower() == 'para':
            child = et_elem.find("./inline")
            if child is not None and child.attrib.get("font-weight", "") == "bold":
                if (
                        "CHAIR" in child.text
                        or "PRESIDENT" in child.text
                        or "SPEAKER" in child.text
                        or "CLERK" in child.text
                    ):
                        return "office"
                else:
                        return "speaker"
        else:
            return "speaker"

    def _clean_text(self, text):
        # Strip leading whitespace/punctuation
        text = super()._clean_text(text)
        
        # If there's a " - " in the text, check if the part before it looks like a title
        if " - " in text:
            parts = text.split(" - ", 1)
            before = parts[0].strip()
            after = parts[1].strip()
            
            # Check if the part before " - " contains title-like elements
            title_indicators = ["Mr", "Mrs", "Ms", "Dr", "Senator", "Sir", "Madam", "Hon"]
            has_title = any(ti in before for ti in title_indicators)
            
            # If the part before " - " is short and has a title, remove it
            if has_title and len(before) < 60:
                text = after
        
        return text


def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor1901
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results

