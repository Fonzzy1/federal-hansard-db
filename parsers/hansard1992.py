from hansard_base_model import (
    HansardExtractor,
    SpeechExtractor,
    ChamberSpeechExtractor,
)

from errors import *
import string


class SpeechExtractor1992(SpeechExtractor):

    def _get_speech_element_children(self, elem):

        # See 1994 line 1087 for why I have to do this
        out = []
        children = elem.getchildren()
        for child in children:
            if child.tag.lower() == "interject":
                out.append(child)
                subchildren = child.getchildren()
                for sub in subchildren:
                    print(str(ET.tostring(sub, encoding="unicode")))
                    print("---")
                    if self._interjection_flag(sub) > 1:
                        child.remove(sub)
                        out.append(sub)
            elif child.tag.lower() == "division":
                pass
            else:
                out.append(child)
        return out

    def _extract_talker(self, elem):
        result = elem.get("nameid")
        if result:
            return result
        raise FailedTalkerExtractionException(elem)

    def _is_interjection_element(self, et_elem):
        """
        Returns True if the element is an interjection, otherwise False.
        """
        # 1. Tag is explicitly an interjection
        if et_elem.tag.lower() in {"interject", "interjection"}:
            return True

        # 2. Tag is PARA and has a bold EMPHASIS with procedural keywords in
        # uppercase
        if et_elem.tag.lower() == "para":
            child = et_elem.find(".//emphasis")
            if child is not None:
                if (
                    child.attrib.get("font-weight", "") == "BOLD"
                    and child.text is not None
                ):
                    if (
                        "CHAIR" in child.text
                        or "PRESIDENT" in child.text
                        or "SPEAKER" in child.text
                    ):
                        return True
                elif (
                    child.attrib.get("font-slant", "") == "ITAL"
                    and child.text is not None
                ):
                    # Check if the whole thing is in italics - indicates general
                    # interjection

                    para_text = "".join(t.strip() for t in et_elem.itertext())
                    para_text = para_text.translate(
                        str.maketrans("", "", string.punctuation)
                    )

                    emph_text = "".join(t.strip() for t in child.itertext())
                    emph_text = emph_text.translate(
                        str.maketrans("", "", string.punctuation)
                    )
                    # If all text is inside the emphasis element, the texts should match
                    if (
                        para_text == emph_text
                        and para_text != ""
                        and "interject" in para_text.lower()
                    ):
                        return True

        return False

    def _interjection_type(self, et_elem):
        # If the usual attribute is present, use it
        if et_elem.tag.lower() in {"interject", "interjection"}:
            if et_elem.get("chair") == "1":
                return "office"
            else:
                return "speaker"

        # Else, check if this is a PARA with a bold procedural keyword
        if et_elem.tag.lower() == "para":
            child = et_elem.find(".//emphasis")
            if child is not None:
                if (
                    child.attrib.get("font-weight", "") == "BOLD"
                    and child.text is not None
                ):
                    return "office"
                elif (
                    child.attrib.get("font-slant", "") == "ITAL"
                    and child.text is not None
                ):
                    return "general"

    def _clean_text(self, text):
        return text.lstrip(" -.,;:!?\t\n\r")


def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor1992
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results


if __name__ == "__main__":
    with open("../tests/1992.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1993.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1994.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1995.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1996.xml") as r:
        text = r.read()
    t = parse(text)
