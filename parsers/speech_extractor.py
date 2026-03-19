import re


class SpeechExtractor:
    def __init__(self, element, parliament = None):
        self.root = element
        self.parliament = parliament

    def extract(self):
        author = self._extract_talker(self.root)
        interjections, text = self._extract_text(self.root)
        return author, interjections, text

    def _extract_talker(self, elem):
        raise FailedTalkerExtractionException(elem)


    def _pull_paras(self, elem):
        text = "".join(elem.itertext())
        return text

    def _is_interjection_element(self, et_elem):
        """
        Returns True if the element is an interjection, otherwise False.
        """
        return False

    def _interjection_type(self, et_elem):
        """
        speaker - there is a member of parliament who said the interjection
        office - the speaker, president, or clerk, made the interjection
        general - the interjection is not complete and is more of a description
        of an interjection rather than a recorded one. 
        """

        raise FailedInterjectionTypeAssingment(et_elem)

    def _interjection_flag(self, et_elem):
        """
        Returns:
          0 - not an interjection
             1 - speaker - there is a member of parliament who said the interjection
             2 - general - the interjection is not complete - either attributed
             but we don't know what is said, or not atributed. These
             interjections often include stage directions within the text
             3 - office - the speaker, president, or clerk, made the interjection
        """
        if not self._is_interjection_element(et_elem):
            return 0
        else:
            t = self._interjection_type(et_elem)
            if t == "speaker":
                return 1
            elif t == "general":
                return 2
            elif t == "office":
                return 3
            else:
                raise FailedInterjectionTypeAssingment(et_elem)

    def _get_speech_element_children(self, elem):
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

    def _extract_text(
        self,
        elem,
    ):
        # Simplest format
        children = self._get_speech_element_children(elem)
        interjections = []
        out_text = []
        interj_count = 1
        for i, child in enumerate(children):
            interject_type = self._interjection_flag(child)
            # Collect all consecutive interjections
            if interject_type:
                key = f"INTERJECTION{interj_count:02d}"
                author = self._extract_talker(child)
                if interject_type == 3 and author == "":
                    author = "10000"
                interjections.append(
                    {
                        "text": self._clean_text(self._pull_paras(child)),
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

    def _clean_text(self, text):
        # Remove all leading non-alphanumeric characters except [ 
        text = re.sub(r"^[^a-zA-Z0-9[]+", "", text)
        return text.strip()
