from parsers.hansard_base_model import (
    HansardExtractor,
    SpeechExtractor,
    ChamberSpeechExtractor,
    print_tag_tree,
)

from parsers.errors import *
import string


class SpeechExtractor1998(SpeechExtractor):

    def _get_speech_element_children(self, elem):
        # The tags that "contain" others
        return elem.getchildren()

    def _extract_talker(self, elem):
        result = elem.find("talk.start/talker/name.id")
        if result is not None and result.text is not None:
            return result.text
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

        ## added 90s style check for inline general interjections
        if et_elem.tag.lower() == "para":
            child = et_elem.find("./inline")
            if child is not None:
                if (
                    child.attrib.get("font-style", "") == "italic"
                    and child.text is not None
                ):
                    para_text = "".join(t.strip() for t in et_elem.itertext())
                    para_text = para_text.translate(
                        str.maketrans("", "", string.punctuation + "—")
                    )

                    emph_text = "".join(t.strip() for t in child.itertext())
                    emph_text = emph_text.translate(
                        str.maketrans("", "", string.punctuation + "—")
                    )
                    # If all text is inside the emphasis element, the texts should match
                    if (
                        para_text == emph_text
                        and para_text != ""
                        and "interject" in para_text.lower()
                    ):
                        return True
            elif (
                et_elem.attrib.get("class") == "italic"
                and et_elem.text
                and "interject" in et_elem.text
            ):
                return True

        else:
            return False

    def _interjection_type(self, et_elem):
        if et_elem.tag.lower() in {"talk.start"}:
            author = et_elem.find("talker/name.id")
            if author is not None and author.text == "10000":
                return "office"
            else:
                return "speaker"
        elif et_elem.tag.lower() in {"continue", "interjection"}:
            author = et_elem.find("talk.start/talker/name.id")
            if author is not None and author.text == "10000":
                return "office"
            else:
                return "speaker"
        elif et_elem.tag.lower() == "para":
            # This will always be a general interjection
            return "general"
        else:
            return "speaker"

    def _clean_text(self, text):
        return text.lstrip(" -.,;:!?\t\n\r")


def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor1998
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results
