from parsers.hansard_base_model import (
    HansardExtractor,
    SpeechExtractor,
    ChamberSpeechExtractor,
)

from parsers.errors import *


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
                if not (
                        "CHAIR" in child.text
                        or "PRESIDENT" in child.text
                        or "SPEAKER" in child.text
                        or "CLERK" in child.text
                    ):
                        return "unconfirmed_speaker"
        else:
            return "speaker"

    def _clean_text(self, text):
        return text.lstrip(" -.,;:!?\t\n\r")


def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor1901
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results


if __name__ == "__main__":
    with open("./tests/1901.xml") as r:
        text = r.read()
    t = parse(text)

        with open("../tests/1902.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1903.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1904.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1905.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1906.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1907.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1908.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1909.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1910.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1911.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1911.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1912.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1913.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1914.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1915.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1916.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1917.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1918.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1919.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1920.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1921.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1925.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1930.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1940.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1950.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1960.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/1970.xml") as r:
        text = r.read()
    t = parse(text)

    with open("./tests/1980.xml") as r:
        text = r.read()
    t = parse(text)


