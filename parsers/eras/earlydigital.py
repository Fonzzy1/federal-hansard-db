"""
Early Digital Era (1981-1997) base classes.

This era covers the transition to digital formats with varying XML structures.
Common characteristics:
- Uses nameid attribute for speaker identification
- Has interject/interjection elements
- Uses para elements with emphasis for formatting
"""

from parsers.speech_extractor import SpeechExtractor

import string


class SpeechExtractorEarlyDigital(SpeechExtractor):
    """
    Base class for the early digital era (1981-1997).
    Contains common logic shared by parsers in this period.
    """

    def _get_speech_element_children(self, elem):
        """
        Extract children with special handling for embedded para interjections.
        
        See 1994 line 1087 for why this is needed.
        """
        out = []
        children = elem.getchildren()
        for child in children:
            if child.tag.lower() in ["interject", "interjection"]:
                # Check for inline para interjections within this interjection block
                subchildren = child.getchildren()
                for sub in subchildren:
                    # Only move para elements that are interjections with content
                    if sub.tag.lower() == "para" and self._is_interjection_element(sub) and self._interjection_flag != 3:
                        # Check that the para has meaningful text content
                        sub_text = "".join(sub.itertext()).strip()
                        if sub_text:  # Only move if there's actual content
                            child.remove(sub)
                            out.append(sub)
                out.append(child)
            elif child.tag.lower() == "division":
                pass
            else:
                out.append(child)
        return out

    def _is_interjection_element(self, et_elem):
        """
        Returns True if the element is an interjection, otherwise False.
        """
        if et_elem.tag.lower() in {"interject", "interjection"}:
            return True, False
        # 2. Tag is PARA and has a bold EMPHASIS with procedural keywords in
        # uppercase
        if et_elem.tag.lower() == "para":
            child = et_elem.find(".//emphasis")
            ## TODO bring out to later elements
            if child is not None:
                if (
                    child.attrib.get("font-weight", "") == "BOLD"
                    and child.text is not None
                ):
                    if (
                        "CHAIR" in child.text
                        or "PRESIDENT" in child.text
                        or "SPEAKER" in child.text
                        or "CLERK" in child.text
                    ):
                        return True, True
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
                        return True, True

        return False, False


    def _extract_talker(self, elem):
        result = elem.get("nameid", None)
        if result:
            return result
        return ""

    def _extract_inline_talker(self, elem):
        result = elem.get("nameid", None)
        if result:
            return result
        return ""


    def _interjection_type(self, et_elem):
        # If the usual attribute is present, use it
        if et_elem.tag.lower() in {"interject", "interjection"}:
            if et_elem.get("chair") == "1":
                return "office"
            else:
                return "speaker"

    def _interjection_type_inline(self,et_elem):

        # Else, check if this is a PARA with a bold procedural keyword
        if et_elem.tag.lower() == "para":
            child = et_elem.find(".//emphasis")
            ## TODO again check the bolding thingo
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
        return "general"


    def _clean_text(self, text):

        # Check if there's a title in brackets or parentheses at the start and remove it
        import re
        bracket_title_pattern = r'^(?:\[|\()([^\]\)]+)(?:\]|\))\s*'
        match = re.match(bracket_title_pattern, text)
        if match:
            bracket_content = match.group(1)
            # Check if the bracketed content looks like a title
            title_indicators = ["Mr", "Mrs", "Ms", "Dr", "Senator", "Sir", "Madam", "Hon"]
            if any(ti in bracket_content for ti in title_indicators):
                text = text[match.end():]
        
        # If there's a " - " in the text, check if the part before it looks like a title
        if "---" in text:
            parts = text.split("---", 1)
            before = parts[0].strip()
            after = parts[1].strip()
            
            # Check if the part before " - " contains title-like elements
            title_indicators = ["Mr", "Mrs", "Ms", "Dr", "Senator", "Sir", "Madam", "Hon"]
            has_title = any(ti in before for ti in title_indicators)
            
            # If the part before " - " is short and has a title, remove it
            if has_title and len(before) < 60:
                text = after
        

        
        # Strip leading whitespace/punctuation
        text = super()._clean_text(text)
        
        return text



