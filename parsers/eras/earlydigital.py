"""
Early Digital Era (1981-1997) base classes.

This era covers the transition to digital formats with varying XML structures.
Common characteristics:
- Uses nameid attribute for speaker identification
- Has interject/interjection elements
- Uses para elements with emphasis for formatting
"""

from parsers.hansard_base_model import SpeechExtractor

import string


class SpeechExtractorEarlyDigital(SpeechExtractor):
    """
    Base class for the early digital era (1981-1997).
    Contains common logic shared by parsers in this period.
    """

    def _get_speech_element_children(self, elem):
        """Default implementation returns all children."""
        return elem.getchildren()

    def _is_interjection_element(self, et_elem):
        """
        Returns True if the element is an interjection, otherwise False.
        """
        # Check element tag
        if et_elem.tag.lower() in {"interject", "interjection"}:
            return True
        return False

    def _interjection_type(self, et_elem):
        """Determine the type of interjection."""
        if et_elem.get("chair") == "1":
            return "office"
        return "speaker"

    def _interjection_type_with_general(self, et_elem):
        """Determine the type of interjection including general type."""
        if et_elem.get("chair") == "1":
            return "office"
        return "speaker"

    def _extract_talker(self, elem):
        """Extract talker from nameid attribute."""
        result = elem.get("nameid")
        if result:
            return result
        return ""

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
