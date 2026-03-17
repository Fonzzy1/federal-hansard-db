from parsers.hansard_base_model import (
    HansardExtractor,
    ChamberSpeechExtractor,
    print_tag_tree,
)

from parsers.hansard1997 import SpeechExtractor1997
from parsers.errors import *
import string


class SpeechExtractor1998(SpeechExtractor1997):

    
    def _extract_talker(self, elem):
        result = elem.find("talk.start/talker/name.id")
        if result is not None and result.text is not None:
            return result.text
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
                and et_elem.text
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



def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor1998
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results

with open('./tests/2001.xml') as r:
    text = r.read()
parse(text)

elem = ET.fromstring("""<answer> <talk.start> <talker> <page.no>28886</page.no> <name role="metadata">Howard, John, MP</name> <name role="display">Mr HOWARD</name> <name.id>ZD4</name.id> <electorate>Bennelong</electorate> <party>LP</party> <role>Prime Minister</role> <in.gov>1</in.gov> <first.speech>0</first.speech> </talker> <para>—I thank the Leader of the Opposition for asking me that question. I would say to the Leader of the Opposition: you have it within your power to make Australian families $36 million better off by paying—</para> </talk.start> <interjection> <talk.start> <talker> <name.id>PE4</name.id> <name role="metadata">Beazley, Kim, MP</name> <name role="display"></name> </talker> </talk.start> </interjection> <continue> <talk.start> <talker> <name.id>ZD4</name.id> <name role="display">Mr HOWARD</name> </talker> <para>—That was a rotten deal and you know it. That money is going—</para> </talk.start> </continue> <interjection> <talk.start> <talker> <name.id>PE4</name.id> <name role="metadata">Beazley, Kim, MP</name> <name role="display"></name> </talker> </talk.start> </interjection> <interjection> <talk.start> <talker> <name.id>10000</name.id> <name role="metadata">SPEAKER, Mr</name> <name role="display">Mr SPEAKER</name> </talker> <para>—The Prime Minister and Leader of the Opposition!</para> </talk.start> </interjection> <continue> <talk.start> <talker> <name.id>ZD4</name.id> <name role="display">Mr HOWARD</name> </talker> <para>—You established a pipeline from the federal Treasury to the headquarters of the Australian Labor Party. You ought to be ashamed of yourself for that.</para> </talk.start> </continue> <interjection> <talk.start> <talker> <name.id>10000</name.id> <name role="metadata">SPEAKER, Mr</name> <name role="display">Mr SPEAKER</name> </talker> <para>—The Prime Minister!</para> </talk.start> </interjection> <continue> <talk.start> <talker> <name.id>ZD4</name.id> <name role="display">Mr HOWARD</name> </talker> <para>—You ought to be ashamed of yourself—</para> </talk.start> </continue> <interjection> <talk.start> <talker> <name.id>PE4</name.id> <name role="metadata">Beazley, Kim, MP</name> <name role="display"></name> </talker> </talk.start> </interjection> <interjection> <talk.start> <talker> <name.id>10000</name.id> <name role="metadata">SPEAKER, Mr</name> <name role="display">Mr SPEAKER</name> </talker> <para>—I am tired of the Leader of the Opposition and I am tired of the Prime Minister defying the chair!</para> </talk.start> <para> <inline font-style="italic">Opposition members interjecting—</inline> </para> </interjection> <interjection> <talk.start> <talker> <name.id>10000</name.id> <name role="metadata">SPEAKER, Mr</name> <name role="display">Mr SPEAKER</name> </talker> <para>—I issue a general warning. The Prime Minister had, unwittingly, not been responding to the question. It is in that context that I draw his attention to the fact that he was not responding to the immediate question asked. Furthermore, I would point out to both the Prime Minister and the Leader of the Opposition that neither of them has a licence to deal with each other across the table. All comments are addressed through the chair.</para> </talk.start> </interjection> <continue> <talk.start> <talker> <name.id>ZD4</name.id> <name role="display">Mr HOWARD</name> </talker> <para>—Mr Speaker, I repeat, through the chair: the Leader of the Opposition could help Australians families by paying back that $36 million out of the coffers of the Australian Labor Party. </para> </talk.start> </continue> <para> <inline font-style="italic">Honourable members interjecting</inline>— </para> <continue> <talk.start> <talker> <name.id>ZD4</name.id> <name role="display">Mr HOWARD</name> </talker> <para>—The former national secretary—</para> </talk.start> </continue> <interjection> <talk.start> <talker> <name.id>10000</name.id> <name role="metadata">SPEAKER, Mr</name> <name role="display">Mr SPEAKER</name> </talker> <para>—Prime Minister!</para> </talk.start> <para> <inline font-style="italic">Honourable members interjecting</inline>— </para> </interjection> <interjection> <talk.start> <talker> <name.id>10000</name.id> <name role="metadata">SPEAKER, Mr</name> <name role="display">Mr SPEAKER</name> </talker> <para>—It is probably inevitable that this winter session will end with someone being obliged to remove themself from the House. I hope I am wrong.</para> </talk.start> </interjection> <interjection> <talk.start> <talker> <name.id>5I4</name.id> <name role="metadata">McMullan, Bob, MP</name> <name role="display">Mr McMullan</name> </talker> <para>—Mr Speaker, I raise a point of order. In light of your general warning, I draw your attention to the fact that the Prime Minister is defying your ruling and not dealing with the specific question, exactly as you warned him not to do. </para> </talk.start> </interjection> <interjection> <talk.start> <talker> <name.id>10000</name.id> <name role="metadata">SPEAKER, Mr</name> <name role="display">Mr SPEAKER</name> </talker> <para>—In the 18 years that I have been a member of this place the chair has always extended a good deal more licence to the Prime Minister and to the Leader of the Opposition. I invite the Prime Minister to come back to the issue of the GST and its impact on the Australian economy.</para> </talk.start> </interjection> <continue> <talk.start> <talker> <name.id>ZD4</name.id> <name role="display">Mr HOWARD</name> </talker> <para>—I was asked about the impact of policy on the families of Australia and the taxpayers of Australia. What I said was utterly relevant to that, and it remains utterly relevant. In relation to the other part of the question asked by the Leader of the Opposition in which he listed a litany of alleged broken promises, we made a commitment to the Australian people when we went to the electorate in 1998 that, if re-elected, we would deliver to them an improved taxation system. We promised that we would deliver them a taxation system that would make Australian families better off, and we did. We promised that we would deliver a taxation system that would give the states a growth tax, and we did. We promised that we would deliver a taxation system that would take $3½ billion off the back of the exporters, and we did. We promised to deliver them a taxation system that would have for the short term only a stated impact on the consumer price index. In fact, we overdelivered on that promise because the impact on the CPI was less.</para> </talk.start> </continue> <para>Above all, in bringing forward this taxation system, we promised that we would take into account the long-term economic and social interests of the Australian community. This country has needed tax reform for a generation and over the last 25 years it has been in the long-term interests of Australia that we have tax reform. Every person who has held a position of leadership on either side of politics in this House over that 25-year period has known in their heart that we have needed taxation reform. But the only person who has held that position, who is still in this parliament and who has been prepared to undertake the political heavy lifting to bring about that reform is me, along with the assistance of the Treasurer, the Minister for Finance and Administration and everybody else. In the end, you are judged on what you are prepared to do in the long term. I will always be prepared to have what I have done in relation to tax reform compared with the action of the Leader of the Opposition as a member of a party that has taken the Australian taxpayer for a $36 million ride via the lease on Centenary House.</para> </answer> """)
self = SpeechExtractor1998(elem)

q = self._get_speech_element_children(elem)
[self._pull_paras(a) for a in q]

