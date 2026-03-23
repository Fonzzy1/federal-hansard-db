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

import copy
import re

from parsers.speech_extractor import SpeechExtractor

import re
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
        return ""

    def _pull_paras(self,elem):


        texts = []
        if elem.tag.lower() ==  'para':
            return "".join(elem.itertext())
        else:
            for child in elem.getchildren():
                texts.append(self._pull_paras(child))
            return "".join(texts)

    def _pull_inline_paras(self,elem):
        # Make a copy so modifications don't affect the original element
        elem = copy.deepcopy(elem)

        # Most of the time we grab everything, with the exception of speaker
        # interjections, where we dont grab the speaker name info which sits
        # within the inline element
        if self._interjection_type_inline(elem) != 'general':
            while True:
                bold_inline = elem.find('inline[@font-weight="bold"]')
                if bold_inline is None:
                    break
                # Preserve the tail before removing
                if bold_inline.tail:
                    if elem.text:
                        elem.text += bold_inline.tail
                    else:
                        elem.text = bold_inline.tail
                elem.remove(bold_inline)
                # Stop removing once there's actual para text
                if elem.text and elem.text.strip():
                    break

        return "".join(elem.itertext())
            

    def _is_interjection_element(self, et_elem):
        """
        Returns True if the element is an interjection, otherwise False.
        """
        # Check element tag
        if et_elem.tag.lower() in {"interject", "interjection"}:
            return True, False
        if et_elem.tag.lower() in {"talk.start"}:
            author = et_elem.find("talker/name.id")
            if author is not None and author.text == "10000":
                return True, False
        if et_elem.tag.lower() in {"continue"}:
            author = et_elem.find("talk.start/talker/name.id")
            if author is not None and author.text == "10000":
                return True, False

        # And all the inline interjcetions
        if et_elem.tag.lower() == 'para':


                # The bolding indicates a  change of speaker
                if et_elem.find("inline") is not None and (not et_elem.text or (et_elem.text and not et_elem.text.strip())):
                    inline = et_elem.find('inline')

                    # Boldiing inicates either a reference to another speaker
                    # a change of speaker, check for capitalisation
                    if inline.text and inline.attrib.get("font-weight", "") == "bold" and re.search(r'\b[A-Z]+\b', inline.text):
                        return True, True

                    # Italics are more general 
                    if inline.text and inline.attrib.get('font-style', "") == 'italic':
                        return True, True

                if (
                    et_elem.attrib.get("class") == "italic"
                    and et_elem.text
                    and "interject" in et_elem.text
                ):
                    return True, True

        return False, False


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

    def _interjection_type_inline(self, et_elem):
        # Only consider inlines at the start (before any non-inline text)
        # Stop as soon as we hit text in the tail (after an inline)


        inlines = et_elem.findall('inline[@font-weight="bold"]')
        if not inlines:
            return "general"
        
        # Check inlines in order
        for inline in inlines:
            # Check bold inline for office roles
            if inline.text:
                for role in ["SPEAKER", "CLERK", "PRESIDENT", "CHAIR", "DEPUTY"]:
                    if role in inline.text:
                        return "office"
        
            # If there's meaningful text in the tail, we've hit speech content - stop
            if inline.tail and inline.tail.strip():
                break
            
        # Has bold inlines but no office roles found
        return "speaker"

    def _extract_inline_talker(self, elem):
        # Find the elements in the inlines
        # if its a type 3, then just let it happen
        if self._interjection_type_inline(elem) == "office" :
            return ""


        inline_texts = []
        inlines = elem.findall('inline[@font-weight="bold"]')
        if not inlines:
            return ""
        for inline in inlines:
            if inline.text:
                inline_texts.append(re.sub(r'[^a-zA-Z0-9]', '', inline.text.strip().upper()))
            if inline.tail and inline.tail.strip():
                break
        # Because these are going to be a mess, add the parliament year to them
        inline_texts.append(str(self.parliament))

        return "".join(inline_texts)





    def _clean_text(self, text):

        #Strip leading whitespace/punctuation
        text = super()._clean_text(text)

        text = text.lstrip()

        title_indicators = ["Mr", "Mrs", "Ms", "Dr", "Senator", "Sir", "Madam", "Hon"]

        # Check if there's a title in brackets or parentheses at the start and remove it
        bracket_title_pattern = r'^(?:\[|\()([^\]\)]+)(?:\]|\))'
        match = re.match(bracket_title_pattern, text)
        if match:
            bracket_content = match.group(1)
            # Check if the bracketed content looks like a title
            if any(ti in bracket_content for ti in title_indicators):
                text = text[match.end():]
        
        # If there's a " - " in the text, check if the part before it looks like a title
        for dash in ['-','—']:
            if dash in text:
                parts = text.split(dash, 1)
                before = parts[0].strip()
                after = parts[1].strip()
            
                # Check if the part before " - " contains title-like elements
                has_title = any(ti in before for ti in title_indicators)
            
                # If the part before " - " is short and has a title, remove it
                if has_title and len(re.sub(r'[^a-zA-Z0-9]', '', before)) < 25 and len(re.sub(r'[^a-zA-Z0-9]', '', after)) > 5  and "INTERJECTION" not in before:
                    text = after
                    break
        
        
        #Strip leading whitespace/punctuation
        text = super()._clean_text(text)
        
        return text



