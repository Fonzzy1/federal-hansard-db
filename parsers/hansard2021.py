from parsers.hansard_extractor import HansardExtractor, print_tag_tree
from parsers.chamber_speech_extractor import ChamberSpeechExtractor
from parsers.eras import SpeechExtractorModern

from parsers.errors import *



class SpeechExtractor2021(SpeechExtractorModern):


    def _get_a_element(self,et_elem):
        try:
            a_element = et_elem.find("./span/a/span")
            if a_element is None and et_elem.tag.lower() == "a":
                a_element = et_elem.find("./p/span")
                a_elements = a_element.findall("span")
            elif a_element is None:
                a_elements = et_elem.find("span").findall("span")
            i = 0
            while not (
                a_element is not None
                and a_element.text
                and a_element.text.strip()
            ):
                a_element = a_elements[i]
                i += 1
        except:
            raise FailedInterjectionTypeAssingment(et_elem)

        return a_element


    def _interjection_type_inline(self, et_elem):
        a_element = self._get_a_element(et_elem)
        if  a_element is None:
            return False

        t = a_element.get("class")
        # In this case we know it has to be the speaker becuase you wont
        # interject yourself
        if t == "HPS-MemberSpeech":
            return "office"
        if t == "HPS-OfficeInterjecting":
            return "office"
        if t == "HPS-OfficeContinuation":
            return "office"
        if t == "HPS-GeneralIInterjecting":
                return "general"
        if t == "HPS-MemberIInterjecting":
            return 'general'
        if t == "HPS-GeneralInterjecting":
            return "general"
        if t == "HPS-MemberInterjecting":
            member_text = ""
            name_spans = et_elem.xpath(
                ".//span[contains(@class, 'HPS-MemberInterjecting')]"
            )
            for span in name_spans:
                if span.text:
                    member_text += span.text.strip()
            member_text = member_text.strip().replace(" ", "")
            if any(
                role in member_text
                for role in ["SPEAKER", "CLERK", "PRESIDENT", "CHAIR"]
            ):
                return "office"
            else:
                return "speaker"



def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor2021
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results

