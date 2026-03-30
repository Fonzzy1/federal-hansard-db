from parsers.errors import *
import re
from typing import Literal, Tuple, List


class SpeechExtractor:
    def __init__(self, element, parliament = None):
        self.root = element
        self.parliament = parliament

    def extract(self):
        author = self._extract_talker(self.root)
        interjections, text = self._extract_text(self.root)
        return author, interjections, text

    def _extract_talker(self, elem) -> str:
        # Should always be overwritten
        raise FailedTalkerExtractionException(elem)
        return ""

    def _pull_paras(self, elem) -> str:
        text = "".join(elem.itertext())
        return text

    def _extract_inline_talker(self, elem) -> str:
        # Should always be overwritten
        raise FailedTalkerExtractionException(elem)
        return ""

    def _pull_inline_paras(self, elem) -> str:
        text = "".join(elem.itertext())
        return text

    def _is_interjection_element(self, et_elem) -> Tuple[bool, bool]:
        """
        Returns True if the element is an interjection, otherwise False.
        The second element tells us if ther interjection is inline - or has a
        lot of information that can be parsed similarly to a speech
        """
        return False, False


    def _interjection_type(self, et_elem) -> Literal['speaker', 'office', 'general'] | None:
        """
        speaker - there is a member of parliament who said the interjection
        office - the speaker, president, or clerk, made the interjection
        general - the interjection is not complete and is more of a description
        of an interjection rather than a recorded one. 
        """

        raise FailedInterjectionTypeAssingment(et_elem)

    def _interjection_type_inline(self, et_elem) -> Literal['speaker', 'office', 'general'] | None:

        """
        speaker - there is a member of parliament who said the interjection
        office - the speaker, president, or clerk, made the interjection
        general - the interjection is not complete and is more of a description
        of an interjection rather than a recorded one. 
        """

        raise FailedInterjectionTypeAssingment(et_elem)


    def _interjection_flag(self, et_elem) -> Tuple[Literal[0,1,2,3,4], bool]:
        """
        Returns:
          0 - not an interjection
             1 - speaker - there is a member of parliament who said the interjection
             2 - general - the interjection is not complete - either attributed
             but we don't know what is said, or not atributed. These
             interjections often include stage directions within the text
             3 - office - the speaker, president, or clerk, made the interjection
            4 - error in interjection type assignement
        """
        is_element, is_inline = self._is_interjection_element(et_elem)
        if not is_element:
            return 0, False
        else:
            if is_inline:
                t = self._interjection_type_inline(et_elem)
            else: 
                t = self._interjection_type(et_elem)
            if t == "speaker":
                return 1, is_inline
            elif t == "general":
                return 2, is_inline
            elif t == "office":
                return 3, is_inline
            else:
                return 4, is_inline

    def _get_speech_element_children(self, elem) -> list:
        """
        Default implementation: filter out division elements and return remaining children.
        Subclasses can override for more specific handling.
        """
        out = []
        children = elem.getchildren()
        for child in children:
            if child.tag.lower() == "division":
                pass
            else:
                out.append(child)
        return out

    def _extract_text ( self, elem) -> Tuple[List, str]:
        # Simplest format
        children = self._get_speech_element_children(elem)
        interjections = []
        out_text = []
        interj_count = 1
        for i, child in enumerate(children):
            interject_type, is_inline = self._interjection_flag(child)
            # Collect all consecutive interjections
            if interject_type:
                key = f"INTERJECTION{interj_count:02d}"
                if is_inline:
                    text = self._pull_inline_paras(child)
                    author = self._extract_inline_talker(child)
                else:
                    text = self._pull_paras(child)
                    author = self._extract_talker(child)
                if interject_type == 3 and author == "":
                    author = "10000"
                interjections.append(
                    {
                        "text": self._clean_text(text),
                        "author": author,
                        "sequence": interj_count,
                        "type": interject_type,
                    }
                )
                out_text.append(f"[{key}]")
                interj_count += 1
            # If it's a continues, append its text
            else:
                out_text.append(self._pull_paras(child))
        final_main_text = self._clean_text(" ".join(out_text))

        return interjections, final_main_text

    def _clean_text(self, text) -> str:
        # Remove all leading non-alphanumeric characters except [ 
        text = re.sub(r"^[^a-zA-Z0-9[]+", "", text)
        return text.strip()
