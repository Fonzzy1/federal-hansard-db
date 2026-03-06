from hansard_base_model import (
    HansardExtractor,
    SpeechExtractor,
    ChamberSpeechExtractor,
    print_tag_tree,
)

from errors import *
import string


class SpeechExtractor1998(SpeechExtractor):

    def _get_speech_element_children(self, elem):
        # The tags that "contain" others
        return elem.getchildren()

    def _extract_talker(self, elem):
        result = elem.find("talk.start/talker/name.id")
        if result is not None:
            return result.text
        else:
            raise FailedTalkerExtractionException(elem)

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


if __name__ == "__main__":

    with open("../tests/1998.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1999.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2000.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2001.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2005.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2006.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2007.xml") as r:
        text = r.read()
    t = parse(text)

    # Should be empty
    [
        x
        for x in t[0]["documents"]
        if "members interjecting"
        in x.get("answer", {"text": ""})["text"] + x["text"]
    ]

    # Test to see if we get type 2 interjections
    [
        x
        for x in t[0]["documents"]
        if any(
            [
                y["type"] == 2
                for y in x["interjections"]
                + x.get("answer", {"interjections": []})["interjections"]
            ]
        )
    ]

    # Test to see if we get type 3 interjections
    [
        x
        for x in t[0]["documents"]
        if any(
            [
                y["type"] == 3
                for y in x["interjections"]
                + x.get("answer", {"interjections": []})["interjections"]
            ]
        )
    ]
    # Test to see if there are Order where there shouldn't be.
    # Should be emptyish
    [
        x
        for x in t[0]["documents"]
        if "Order" in x.get("answer", {"text": ""})["text"] + x["text"]
    ]

    # Test to see if we get type bad orders
    [
        x
        for x in t[0]["documents"]
        if any(
            [
                y["type"] != 3 and "Order" in y["text"]
                for y in x["interjections"]
                + x.get("answer", {"interjections": []})["interjections"]
            ]
        )
    ]
