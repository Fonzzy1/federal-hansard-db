from hansard_base_model import (
    HansardExtractor,
    SpeechExtractor,
    ChamberSpeechExtractor,
    print_tag_tree,
)

from errors import *
import string

import re


class SpeechExtractor2011(SpeechExtractor):

    def __init__(self, element):
        super().__init__(element)
        self.name_to_href = {}

    def extract(self):
        author = self._extract_talker(self.root)
        interjections, text = self._extract_text(self.root, record_office_interjector=True)

        # Dirty fix for when the whole thing is an 'interjection'
        if interjections:
            # Check if the speech is owened by a office holder
            if author == interjections[0]['author'] and interjections[0]['type'] == 3:
                # If so, then the whole thing is actually an interjetion
                secs = re.split(r'\[INTERJECTION\d+\]', text)
                # The first element is going to be empty - so now lets allocate
                # the index = 1 element to the initial interjection
                first_section = secs[1]
                text = text.replace(first_section, "")
                interjections[0]['text'] += first_section

        return author, interjections, text


    def _get_speech_element_children(self, elem):
        # The tags that "contain" others
        elems = elem.find("talk.text").getchildren()
        return elems

    def _extract_talker(self, elem):
        # Case when we are looking at speeches
        result = elem.find("talk.start/talker/name.id")
        if result is not None:
            return result.text

        # Case when we are looking at interjections
        a_element = elem.find("./span/a")
        if a_element is not None and a_element.get("href"):
            href = a_element.get("href")
            name_text = elem.find("./span/a/span").text.rstrip(" -.,;:!?\t\n\r")
            self.name_to_href[name_text] = href
            return href
        elif a_element is None:
            name_text = elem.find("./span/span").text.rstrip(" -.,;:!?\t\n\r")
            potential_id = self.name_to_href.get(name_text)
            if potential_id:
                return potential_id
        # Finaly if we have an interjection element, and we dont know, give
        # 10000
        if self._interjection_flag(elem) == 3:
            return 10000

        raise FailedTalkerExtractionException(elem)

    def _is_interjection_element(self, et_elem):
        """
        Returns True if the element is an interjection, otherwise False.
        """
        # All elements are paras now
        for span in et_elem.findall(".//span"):
            class_attr = span.get("class", "")
            if class_attr in [
                "HPS-OfficeInterjecting",
                "HPS-OfficeContinuation",
                "HPS-MemberIInterjecting",
                "HPS-GeneralIInterjecting",
                "HPS-MemberInterjecting",
                "HPS-GeneralInterjecting",
            ]:
                return True

            # Or a contiuation by the speaker
            elif class_attr in {
                "HPS-MemberContinuation",
                "HPS-MemberSpeech",
            }:
                member_continuation_text = span.text
                if member_continuation_text and any(
                    role in member_continuation_text
                    for role in ["SPEAKER", "CLERK", "PRESIDENT"]
                ):
                    return True
        return False

    def _interjection_type(self, et_elem):
        a_element = et_elem.find("./span/a/span")
        if a_element is None:
            a_element = et_elem.find("./span/span")
        t = a_element.get("class") if a_element is not None else None

        if t == "HPS-MemberContinuation":
            return "office"
        # In this case we know it has to be the speaker becuase you wont
        # interject yourself
        if t == "HPS-MemberSpeech":
            return "office"
        if t == "HPS-OfficeInterjecting":
            return "office"
        if t == "HPS-OfficeContinuation":
            return "office"
        if t == "HPS-MemberIInterjecting":
            return "general"
        if t == "HPS-GeneralIInterjecting":
            return "general"
        if t == "HPS-GeneralInterjecting":
            return "unrecorded"
        if t == "HPS-MemberInterjecting":
            if a_element.getparent().get("href"):
                return "speaker"
            else:
                return "unrecorded"

        if t == "HPS-GeneralInterjecting":
            return "general"

    def _clean_text(self, text):
        return text.lstrip(" -.,;:!?\t\n\r")


def parse(file_text):
    try:
        extractor = HansardExtractor(
            file_text, ChamberSpeechExtractor, SpeechExtractor2011
        )
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    return results


if __name__ == "__main__":

    with open("../tests/2011.xml") as r:
        text = r.read()
    t = parse(text)

    with open("../tests/2012.xml") as r:
        text = r.read()
    t = parse(text)

    # Should be empty
    [
        x
        for x in t[0]["documents"]
        if "members interjecting"
        in x.get("answer", {"text": ""})["text"] + x["text"]
    ]

    # Test to see if we get type 2 interjections
    [
        x
        for x in t[0]["documents"]
        if any(
            [
                y["type"] == 2
                for y in x["interjections"]
                + x.get("answer", {"interjections": []})["interjections"]
            ]
        )
    ]

    # Test to see if we get type 4 interjections
    [
        x
        for x in t[0]["documents"]
        if any(
            [
                y["type"] == 4
                for y in x["interjections"]
                + x.get("answer", {"interjections": []})["interjections"]
            ]
        )
    ]

    # Test to see if we get type 3 interjections
    [
        x
        for x in t[0]["documents"]
        if any(
            [
                y["type"] == 3
                for y in x["interjections"]
                + x.get("answer", {"interjections": []})["interjections"]
            ]
        )
    ]
    # Test to see if there are Order where there shouldn't be.
    # Should be emptyish
    [
        x
        for x in t[0]["documents"]
        if "Order"
        in x.get("answer", {"text": ""})["text"] + x["text"]
    ]

    # Test to see if we get type bad orders
    [
        x
        for x in t[0]["documents"]
        if any(
            [
                y["type"] != 3 and "Order" in y["text"]
                for y in x["interjections"]
                + x.get("answer", {"interjections": []})["interjections"]
            ]
        )
    ]

text = """[INTERJECTION01] The report read as follows— Report relating to the consideration of committee and delegation business and of private Members’ business 1.The committee met in private session on Tuesday,
 9 October 2012. 2.The committee determined the order of precedence and times to be allotted for consideration of committee and delegation business and private Members’ business on Monday, 29 October 2012, as foll
ows: Items for House of Representatives Chamber (10:10 am to 12 noon) COMMITTEE AND DELEGATION BUSINESS Presentation and statements 1 Standing Committee on Regional Australia Report of the Delegation to Canada and
 Mongolia The Committee determined that statements on the report may be made — all statements to conclude by 10:15 am. Speech time limits — Mr Windsor — 5 minutes. [Minimum number of proposed Members speaking = 1 
x 5 mins] 2 Joint Standing Committee on Foreign Affairs, Defence and Trade Report on Inquiry into Australia’s Overseas Representation The Committee determined that statements on the report may be made — all statem
ents to conclude by 10:25 am. Speech time limits — Mr Champion — 5 minutes. Next Member speaking — 5 minutes. [Minimum number of proposed Members speaking = 2 x 5 mins] 3 Standing Committee on Infrastructure and C
ommunications Update on the progress of the Committee’s current inquiry into IT Pricing in Australia The Committee determined that statements on the inquiry may be made — all statements to conclude by 10:35 am. Sp
eech time limits — Mr Champion — 5 minutes. Next Member speaking — 5 minutes. [Minimum number of proposed Members speaking = 2 x 5 mins] 4 Joint Select Committee on Gambling Reform Inquiry into the prevention and 
treatment of problem gambling The Committee determined that statements on the report may be made — all statements to conclude by 10:45 am. Speech time limits — Mr Wilkie — 5 minutes. Next Member speaking — 5 minut
es. [Minimum number of proposed Members speaking = 2 x 5 mins] PRIVATE MEMBERS’ BUSINESS Notices 1 MR KATTER: To present a Bill for an Act to require fair indexation of military pensions, and for related purposes.
 (Fair Indexation of Military Pensions Bill 2012) (Notice given 13 September 2012. Notice will be removed from the Notice Paper unless called on any of the next 8 sitting Mondays including 29 October 2012.) Presen
ter may speak for a period not exceeding 10 minutes — pursuant to standing order 41. 2 MR OAKESHOTT: To present a Bill for an Act to continue the National Electricity Law as a Commonwealth law, and for other purpo
ses. (National Electricity Bill 2012) (Notice given 20 September 2012.) Presenter may speak for a period not exceeding 10 minutes — pursuant to standing order 41. 3 MR WILKIE: To present a Bill for an Act to stren
gthen public integrity by encouraging and facilitating the disclosure of corruption, maladministration and other wrongdoing in the Commonwealth public sector, by protecting public officials who make disclosures, a
nd for related purposes. (Public Interest Disclosure (Whistleblower Protection) Bill 2012) (Notice given 9 October 2012.) Presenter may speak for a period not exceeding 10 minutes — pursuant to standing order 41. 
4 MR WILKIE: To present a Bill for an Act to deal with consequential matters in connection with the Public Interest Disclosure (Whistleblower Protection) Act 2012, and for related purposes. (Public Interest Disclo
sure (Whistleblower Protection) (Consequential Amendments) Bill 2012) (Notice given 9 October 2012.) Presenter may speak for a period not exceeding 10 minutes — pursuant to standing order 41. 5 MR NEUMANN: To move
: That this House: (1) recognises that the rates of employment for people with disability in Australia is significantly less than people without disability; (2) commends the efforts taken so far by disability advo
cates and a number of big and small businesses that are working to remedy this concerning trend; (3) acknowledges the significant economic and productivity benefits of having in work, more Australians with disabil
ity; and (4) calls on the Government to: (a) engage with the Australian Securities Exchange (ASX) about the merits of the ASX extending its Corporate Governance Principles and Recommendations to require reporting 
on the employment of people with disability; and (b) explore ways to ensure companies employing more than 100 employees report on their efforts to employ more people with disability. (Notice given 11 September 201
2.) Time allotted — remaining private Members’ business time prior to 12 noon. Speech time limits — Mr Neumann — 10 minutes. Next Member speaking — 10 minutes. Other Members — 5 minutes each. [Minimum number of pr
oposed Members speaking = 2 x 10 mins + 3 x 5 mins] The Committee determined that consideration of this matter should continue on a future day. Items for House of Representatives Chamber (8 to 9:30 pm) PRIVATE MEM
BERS’ BUSINESS — continued Notices — continued 6 MR ABBOTT: To move: That this House: (1) notes that: (a) since the devastating terrorist attacks in the United States on 11 September 2001, over 100 Australians hav
e died and many others have suffered injury as a result of terrorist attacks overseas; (b) the victims of ‘September 11’, the two Bali bombings, the London and Jakarta bombings and the Mumbai terrorist attacks, we
re targeted because they were citizens of countries where people could choose how they lived and what faith they might follow; and (c) 12 October 2012 will mark the tenth anniversary of the 2002 Bali bombings; (2)
 recognises that: (a) many Australian families continue to suffer as a result of their loss and injury from overseas terrorist acts; (b) victims of overseas terrorism have not been entitled to compensation such as
 that received by domestic victims of crime under the various State and Territory victims of crime schemes; and (c) the Government did not support amendments to the Social Security Amendment (Supporting Australian
 Victims of Terrorism Overseas) Bill 2012 which would have provided assistance for any action after 10 September 2001; and (3) supports the Coalition’s request that the Minister make the appropriate retrospective 
declarations so that all of the Australian victims of overseas terrorism acts since 10 September 2001, or their next of kin, can receive this important, but modest, help. (Notice given 20 September 2012.) Time all
otted — remaining private Members’ business time prior to 9:30 pm. Speech time limits — Mr Abbott — 10 minutes. Next 5 Members speaking — 10 minutes each. Other Members — 5 minutes each. [Minimum number of propose
d Members speaking = 6 x 10 + 6 x 5 mins] The Committee determined that consideration of this matter should continue on a future day. Items for Federation Chamber (approx 11 am to approx 1:30 pm) PRIVATE MEMBERS’ 
BUSINESS Notices 1 MR BANDT: To move: That this House: (1) affirms that science is central to our economy and prosperity and that government investment in research is central to maintaining and growing Australia’s
 scientific capacity; (2) notes the: (a) growing concern amongst the science and research community about the security of funding; and (b) risks to jobs and the economy if funding is not secured, especially in Vic
toria where much of Australia’s health and medical research is conducted; and (3) calls on the Treasurer to: (a) guarantee that science and research funding will be protected this financial year; and (b) rule out 
any attempt to defer, freeze or pause Australian Research Council, National Health and Medical Research Council, or other science and research grants in an attempt to achieve a Budget surplus. (Notice given 20 Sep
tember 2012.) Time allotted — 30 minutes. Speech time limits — Mr Bandt — 5 minutes. Other Members — 5 minutes each. [Minimum number of proposed Members speaking = 6 x 5 mins] The Committee determined that conside
ration of this matter should continue on a future day. Orders of the day 1 CODE OF CONDUCT FOR MEMBERS OF PARLIAMENT: Resumption of debate (from 17 September 2012) on the motion of Mr Oakeshott: That this House: (
1) endorses the draft code of conduct at Appendix 5 of the report of the House of Representatives Standing Committee of Privileges and Members’ Interests, Draft Code of Conduct for Members of Parliament; and (2) r
equests the Leader of the House to bring forward urgently for the House’s consideration the proposed changes to standing orders and resolutions of the House necessary to give effect to the Code, procedures for con
sidering complaints under the Code, and for the role of the Standing Committee of Privileges and Members’ Interests in oversight of the Code. Time allotted — 20 minutes. Speech time limits — All Members — 5 minute
s each. [Minimum number of proposed Members speaking = 4 x 5 mins] The Committee determined that consideration of this matter should continue on a future day. Notices — continued 2 MS SMYTH: To move: That this Hou
se: (1) recognises the reliance of many families and individuals across our community on penalty rates as a key component of their income, particularly our lowest-paid workers; (2) acknowledges that work-life bala
nce is important to the health and welfare of workers, families and our community; (3) recognises that penalty rates often compensate workers for time they may otherwise spend with family; and (4) opposes measures
 that would remove or undermine penalty rates. (Notice given 12 September 2012.) Time allotted — 60 minutes. Speech time limits — Ms Smyth — 10 minutes. Next Member speaking — 10 minutes. Other Members — 5 minutes
 each. [Minimum number of proposed Members speaking = 2 x 10 + 8 x 5 mins] The Committee determined that consideration of this matter should continue on a future day. 3 MR COULTON: To move: That this House: (1) ac
knowledges the sacrifices made by those who have served Australia in past and present wars and conflicts and the importance of Remembrance Day in honouring those who have fallen; and (2) notes that many Indigenous
 servicemen and women have also made valuable contributions to the Australian Defence Force, and that: (a) in the past these contributions have not been fully acknowledged and recognised; (b) historically many peo
ple of Aboriginal and Torres Strait Islander background experienced difficulties in enlisting due to their race; (c) the full extent of the contribution of Indigenous peoples to past wars and conflicts is a subjec
t that is still being researched today; (d) more information will only add to the valuable wealth of knowledge that informs Australia’s commemoration ceremonies and enriches the historic record; (e) it is estimate
d that at least 400 Aboriginals or Torres Strait Islanders served in the First World War, and between 3000 and 6000 in the Second World War, and limited historical records indicate that these figures may have been
 much higher; and (f) the maintenance of all war memorials, including those dedicated to the efforts of Indigenous people, should be a national priority. (Notice given 17 September 2012.) Time allotted — remaining
 private Members’ business time prior to approx 1:30 pm. Speech time limits — Mr Coulton — 10 minutes. Next 3 Members — 10 minutes each. [Minimum number of proposed Members speaking = 4 x 10 mins] The Committee de
termined that consideration of this matter should continue at a later hour. Items for Federation Chamber (approx 6:30 to 9 pm) PRIVATE MEMBERS’ BUSINESS Notices — continued 3 MR COULTON: To move: That this House: 
(1) acknowledges the sacrifices made by those who have served Australia in past and present wars and conflicts and the importance of Remembrance Day in honouring those who have fallen; and (2) notes that many Indi
genous servicemen and women have also made valuable contributions to the Australian Defence Force, and that: (a) in the past these contributions have not been fully acknowledged and recognised; (b) historically ma
ny people of Aboriginal and Torres Strait Islander background experienced difficulties in enlisting due to their race; (c) the full extent of the contribution of Indigenous peoples to past wars and conflicts is a 
subject that is still being researched today; (d) more information will only add to the valuable wealth of knowledge that informs Australia’s commemoration ceremonies and enriches the historic record; (e) it is es
timated that at least 400 Aboriginals or Torres Strait Islanders served in the First World War, and between 3000 and 6000 in the Second World War, and limited historical records indicate that these figures may hav
e been much higher; and (f) the maintenance of all war memorials, including those dedicated to the efforts of Indigenous people, should be a national priority. (Notice given 17 September 2012.) Time allotted — 50 
minutes. Speech time limits — All Members — 5 minutes each. [Minimum number of proposed Members speaking = 10 x 5 mins] The Committee determined that consideration of this matter should continue on a future day. 4
 MR HUSIC: To move: That this House notes: (1) with deep concern, proposals being advanced to automatically return any Sri Lankan national seeking asylum in Australia; and (2) that: (a) this is a policy that would
 target only one group of asylum seekers originating from only one particular country; (b) the automatic return of Sri Lankan nationals without the processing of their claims for asylum fails to comply with the Re
fugee Convention; and (c) if enacted, the policy would forcibly return asylum seekers to a country that is not a party to the Refugee Convention. (Notice given 11 September 2012.) Time allotted — 30 minutes. Speec
h time limits — Mr Husic — 10 minutes. Next Member speaking — 10 minutes. Other Members — 5 minutes each. [Minimum number of proposed Members speaking = 2 x 10 + 2 x 5 mins] The Committee determined that considera
tion of this matter should continue on a future day. 5 MS RISHWORTH: To move: That this House: (1) notes the significant impact of the United Kingdom Government’s refusal to index pensions allocated to British exp
atriates living in Australia under the United Kingdom’s National Insurance Fund; (2) recognises that: (a) affected British pensioners have made contributions to this scheme; (b) British pensions for expatriates co
ntinue to be indexed in numerous other countries including the United States of America and within the European Union, but are frozen in mostly former Commonwealth countries, including Australia, Canada, New Zeala
nd and South Africa; and (c) the United Kingdom Government’s: (i) current policy discriminates in its treatment of its expatriate pensioners depending on their country of residence; and (ii) unfair and discriminat
ory policy has resulted in the erosion of the purchasing power of British pensions for more than 250,000 British pensioners living in Australia; (3) acknowledges: (a) that through the Australian pension system, th
e Australian Government provides more than $100 million each year to recipients of a British pension living in Australia, which helps supplement the shortfall created by the United Kingdom Government’s frozen pens
ion policy; and (b) the ongoing efforts of the Australian Government in making repeated representations to the United Kingdom Government, calling on it to address the issue of frozen pensions for British expatriat
es living in Australia; (4) commends the Minister for Families, Community Services and Indigenous Affairs for her continued efforts in raising the issue with the United Kingdom Government, most recently during her
 meeting with the United Kingdom Secretary of State for Work and Pensions; and (5) calls on the United Kingdom Government to treat recipients of a British pension equitably by fairly indexing entitlements regardle
ss of where they choose to retire, so that British pensioners can receive the full benefits they deserve. (Notice given 20 September 2012.) Time allotted — 30 minutes. Speech time limits — Ms Rishworth — 10 minute
s. Next Member speaking — 10 minutes. Other Members — 5 minutes each. [Minimum number of proposed Members speaking = 2 x 10 + 2 x 5 mins] The Committee determined that consideration of this matter should continue 
on a future day. 6 MR COULTON: To move: That this House: (1) acknowledges the significant community contribution Meals on Wheels Australia has made to the most vulnerable in our society for nearly 60 years; (2) va
lues the many Meals on Wheels Australia volunteers that selflessly dedicate their time to ensure that our local communities’ most vulnerable members receive warm and nutritious meals; (3) recognises that Meals on 
Wheels Australia allows elderly people to maintain their independence and provides them with regular social contact; (4) acknowledges that nearly one-third of frail patients admitted to hospital are malnourished a
nd that a further 60 per cent are at risk of malnutrition; and (5) calls on the Government to: (a) support the Meals on Wheels Australia’s initiative to research new ways to improve the nutritional status of elder
ly Australians; and (b) recognise that this initiative to improve nutrition has the potential to change the health, happiness and well-being of elderly Australians. (Notice given 17 September 2012.) Time allotted 
— 20 minutes. Speech time limits — Mr Coulton — 5 minutes. Other Members — 5 minutes each. [Minimum number of proposed Members speaking = 4 x 5 mins] The Committee determined that consideration of this matter shou
ld continue on a future day. 7 MS HALL: To move: That this House: (1) notes that: (a) October is Breast Cancer Awareness Month, and that Monday 22 October 2012 is Pink Ribbon Day; (b) breast cancer is the most com
mon cancer in Australian women (excluding melanoma) and the second leading cause of cancer-related death in Australia; and (c) the incidence of breast cancer in Australia is increasing; and (2) encourages all wome
n to have a mammogram every two years. (Notice given 9 October 2012.) Time allotted — remaining private Members’ business time prior to 9 pm. Speech time limits — Ms Hall — 5 minutes. Other Members — 5 minutes eac
h. [Minimum number of proposed Members speaking = 4 x 5 mins] The Committee determined that consideration of this matter should continue on a future day. 3. The committee recommends that the following item of priv
ate Members’ business listed on the notice paper be voted on: Order of the Day—
Newstart payments (Mr Bandt)"""

interjections = [{'text': "The SPEAKER (15:16): I present report No. 67 of the Selection Committee, relating to the consideration of committee and delegation business and private members' business on Monday, 29 October 2012. The report will be printed in the Hansard for today and the committee’s determinations will appear on tomorrow’s Notice Paper. Copies of the report have been placed on the table.", 'author': '83S', 'sequence': 1, 'type': 3}]
