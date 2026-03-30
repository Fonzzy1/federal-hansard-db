"""196
Modern Era (2011-present) base classes.

This era uses structured HTML-like span elements with specific class attributes.
Common characteristics:
- Uses talk.start/talker/name.id for speaker identification
- Uses span elements with class attributes (HPS-*)
- Has talk.text container elements
- Complex interjection detection via CSS class names
"""

from parsers.speech_extractor import SpeechExtractor

import re


class SpeechExtractorModern(SpeechExtractor):
    """
    Base class for the modern era (2011-present).
    Contains common logic shared by parsers in this period.
    """

    def __init__(self, element, parliament=None):
        super().__init__(element)
        self.name_to_href = {}
        self.parliament = parliament

    def _is_interjection_element(self, et_elem):
        """
        Returns True if the element is an interjection, otherwise False.
        All interejctions are inline because they are all paras
        """
        # All elements are paras - therefor all interjections are inline

        # Start with the 
        for span in et_elem.findall(".//span"):
            class_attr = span.get("class", "")
            if class_attr in [
                "HPS-OfficeInterjecting",
                "HPS-OfficeContinuation",
                "HPS-OfficeSpeech",
                "HPS-MemberIInterjecting",
                "HPS-GeneralIInterjecting",
                "HPS-MemberInterjecting",
                "HPS-GeneralInterjecting",
            ]:
                if span.text and span.text.strip():
                    return True, True


            # Or a contiuation or speech by the speaker
            elif class_attr in {
                "HPS-MemberSpeech",
            }:
                member_continuation_text = span.text
                if member_continuation_text and any(
                    role in member_continuation_text
                    for role in ["SPEAKER", "DEPUTY", "CLERK", "PRESIDENT", "CHAIR"]
                ):
                    return True, True
        return False, False

    def _pull_paras(self, elem):
        """Pull text from span elements with specific HPS classes."""
        texts = []
        # Only grab text from HPS-Normal spans.
        if elem.tag.lower() == "span" and elem.get("class") in (
            "HPS-Normal",
            "HPS-Small"
        ):
            parts = [elem.text] + [c.tail for c in elem]
            return "".join(p for p in parts if p).strip()
        for p in elem.getchildren():
            para_text = self._pull_paras(p)
            if para_text:
                texts.append(para_text)
        return "\n".join(texts)


    def _pull_inline_paras(self, elem):

        """Pull text from span elements with specific HPS classes."""
        # Try for a Memberinterjecting - just desc needed
        spans = elem.findall('.//span[@class="HPS-MemberIInterjecting"]') + elem.findall(".//span[@class='HPS-GeneralIInterjecting']")
        for span in spans:
            if span.text:
                return span.text
        # Try for a generalinterjecting
        spans = elem.findall('.//span[@class="HPS-GeneralInterjecting"]')
        for span in spans:
            if span.text:
                return span.text + (span.tail or '')
        
        # All other cases are simple
        return self._pull_paras(elem)




    def _interjection_fix(self, interjections, text, author):
        """Fix for when the whole speech is actually an interjection."""
        # Check if the speech is owned by an office holder
        if (
            author == interjections[0]["author"]
            and interjections[0]["type"] == 3
        ):
            # If so, then the whole thing is actually an interjection
            secs = re.split(r"\[INTERJECTION\d+\]", text)
            # The first element is going to be empty - so now lets allocate
            # the index = 1 element to the initial interjection
            first_section = secs[1]
            text = text.replace(first_section, "")
            interjections[0]["text"] += first_section

        return interjections, text

    def extract(self):
        """Extract author, interjections, and text."""
        author = self._extract_talker(self.root)
        interjections, text = self._extract_text(
            self.root,
        )

        # Dirty fix for when the whole thing is an 'interjection'
        if interjections:
            interjections, text = self._interjection_fix(
                interjections, text, author
            )

        return author, interjections, text

    def _get_speech_element_children(self, elem):
        """Get children from talk.text element."""
        elems = elem.find("talk.text").getchildren()
        return elems

    def _extract_talker(self, elem):
        """Extract talker from talk.start or anchor elements."""
        # Case when we are looking at speeches
        result = elem.find("talk.start/talker/name.id")
        if result is not None:
            if result.text:
                return result.text

    def _extract_inline_talker(self, elem):

        # case when we are getting a inline general inerjection
        if elem.tag.lower() == "a" and elem.get("href"):
            return elem.get("href")

       # Case when we are looking at interjections that are not given a href
       # because because they have already interjected
        a_element = elem.find("./span/a")
        if a_element is not None and a_element.get("href"):
            href = a_element.get("href")
            name_text = "".join(
                char
                for char in elem.find("./span/a/span").text
                if char.isalnum()
            )
            self.name_to_href[name_text] = href
            return href
        elif a_element is None:
            name_text = elem.find("./span/span").text
            if name_text:
                name_text = "".join(
                    char for char in name_text if char.isalnum()
                )
                potential_id = self.name_to_href.get(name_text)
                if potential_id:
                    return potential_id

        return ""

    def _get_a_element(self, et_elem):
        """Get the anchor element for interjection type detection."""
        a_element = et_elem.find("./span/a/span")
        if a_element is None:
            a_elements = et_elem.find("span").findall("span")
            i = 0
            while i < len(a_elements) and not (
                a_element is not None and a_element.text
            ):
                a_element = a_elements[i]
                i += 1
            if a_element is None or not a_element.text:
                return None
        return a_element



