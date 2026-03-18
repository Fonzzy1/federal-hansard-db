"""
Mass Digitisation Era (1901-1980, 1998-2010) base classes.

This era covers two periods:
- 1901-1980: Early mass digitisation with talk.start structure
- 1998-2010: Later mass digitisation with refined XML structure

Common characteristics:
- Uses talk.start/talker/name.id for speaker identification
- Has talk.text container elements
- Uses inline elements for interjections
- Complex element hierarchy with quote and list nesting
"""

from parsers.hansard_base_model import SpeechExtractor

import string


class SpeechExtractorMassDigitisation(SpeechExtractor):
    """
    Base class for the mass digitisation era (1901-1980, 1998-2010).
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
                    if sub.tag.lower() == "para" and self._is_interjection_element(sub):
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

    def _extract_talker(self, elem):
        """Extract talker from talk.start/talker/name.id path."""
        result = elem.find("talk.start/talker/name.id")
        if result is not None and result.text is not None:
            return result.text
        if self._interjection_flag(elem) == 3:
            return "10000"
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
            if child is not None:
                if child.attrib.get("font-weight", "") == "bold":
                    has_text_before = et_elem.text and et_elem.text.strip()
                    has_text_after = child.tail and child.tail.strip()
                    if not has_text_before and has_text_after:
                        return True
                elif (
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
        """Determine the type of interjection."""
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
            # This will generally be a general interjection
            return "general"
        else:
            return "speaker"



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
        if "-" in text:
            parts = text.split("-", 1)
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



    
