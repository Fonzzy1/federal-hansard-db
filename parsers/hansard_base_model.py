import datetime
import re
from lxml import html
import lxml.etree as ET
from parsers.errors import *
import re


class ChamberSpeechExtractor:

    def __init__(self, element, date, speech_parsing_class, parliament=None):
        self.speech_parsing_class = speech_parsing_class
        self.root = element
        self.date = date
        self.parliament = parliament

        # Build child → parent map
        self.parent_map = {
            child: parent for parent in self.root.iter() for child in parent
        }

    def _extract_elements(self):
        check_elements = self.root.xpath(".//speech | .//question | .//answer")

        # If no relevant elements found, raise an exception
        if not check_elements:
            raise HansardNoElementsException("No parsable Elements")

        elements = []
        raw_elements = list(self.root.iter())

        used_answers = set()  # store id() of used answers

        # First pass: handle question+answer or question-only
        for el in raw_elements:
            tag = el.tag.lower()
            if tag == "question":
                parent = el.getparent()
                found_el = False
                answer = None
                for child in parent:
                    if child is el:
                        found_el = True
                        continue
                    if found_el and child.tag.lower() == "answer":
                        answer = child
                        break

                if answer is not None:
                    elements.append(
                        {
                            "type": "question",
                            "question": self._clean_element(el),
                            "answer": self._clean_element(answer),
                        }
                    )
                    used_answers.add(id(answer))  # mark this answer as used
                else:
                    # if theere are no
                    elements.append(
                        {
                            "type": "question",
                            "question": self._clean_element(el),
                        }
                    )
            elif tag == "speech":
                elements.append(
                    {"type": "speech", "element": self._clean_element(el)}
                )

        # Second pass: add orphan answers
        for el in raw_elements:
            if el.tag.lower() == "answer" and id(el) not in used_answers:
                elements.append(
                    {"type": "answer", "element": self._clean_element(el)}
                )
        return elements

    def extract(self):
        elements = self._extract_elements()
        results = []
        for elem in elements:
            if elem["type"] == "question" and "answer" in elem.keys():
                title = self._get_debate_info(elem["question"])
                q_author, q_interjections, q_text = self.speech_parsing_class(
                    elem["question"], parliament = self.parliament
                ).extract()
                a_author, a_interjections, a_text = self.speech_parsing_class(
                    elem["answer"], parliament = self.parliament
                ).extract()
                entry = {
                    "type": "question",
                    "interjections": q_interjections,
                    "text": q_text,
                    "author": q_author,
                    "title": title,
                    "answer": {
                        "type": "answer",
                        "author": a_author,
                        "text": a_text,
                        "interjections": a_interjections,
                        "title": title,
                    },
                }
                results.append(entry)
            elif elem["type"] == "question" and "answer" in elem.keys():
                # Question with answer - need to set parliament before calling extract
                q_extractor = self.speech_parsing_class(elem["question"],parliament = self.parliament)
                q_author, q_interjections, q_text = q_extractor.extract()
                
                a_extractor = self.speech_parsing_class(elem["answer"],parliament = self.parliament)
                a_author, a_interjections, a_text = a_extractor.extract()
                
                entry = {
                    "type": "question",
                    "interjections": q_interjections,
                    "text": q_text,
                    "author": q_author,
                    "title": self._get_debate_info(elem["question"]),
                    "answer": {
                        "type": "answer",
                        "author": a_author,
                        "text": a_text,
                        "interjections": a_interjections,
                        "title": self._get_debate_info(elem["question"]),
                    },
                }
                results.append(entry)
            elif elem["type"] == "question" and "answer" not in elem.keys():
                q_extractor = self.speech_parsing_class(elem["question"],parliament = self.parliament)
                q_extractor.parliament = self.parliament
                q_author, q_interjections, q_text = q_extractor.extract()

                entry = {
                    "type": "question",
                    "author": q_author,
                    "text": q_text,
                    "interjections": q_interjections,
                    "title": self._get_debate_info(elem["question"]),
                }
                results.append(entry)

            elif elem["type"] in ["answer", "speech"]:
                speech_extractor = self.speech_parsing_class(elem["element"],
                                                             parliament =
                                                             self.parliament)
                speech_extractor.parliament = self.parliament
                author, interjections, text = speech_extractor.extract()
                entry = {
                    "type": elem["type"],
                    "author": author,
                    "title": self._get_debate_info(elem["element"]),
                    "text": text,
                    "interjections": interjections,
                }
                results.append(entry)
            else:
                raise FailedElementParsingException(elem)

        return results

    def _get_debate_info(self, el):
        titles = []
        while el in self.parent_map:
            parent = self.parent_map[el]
            # Look for an info element directly under this parent
            for tag in ["debateinfo", "subdebateinfo", "title"]:
                info = parent.find(tag)
                if info is not None:
                    if info.tag == "title":
                        titles.append(
                            re.sub(
                                r"\s+", " ", "".join(info.itertext())
                            ).strip()
                        )
                    else:
                        title = info.findtext("title")
                        if title is not None:
                            titles.append(title.strip())
                    break
            el = parent
        # Reverse so it's top-down order (debate → subdebate.1 → subdebate.2)
        titles.reverse()
        return ", ".join(titles)

    def _clean_element(self, el):
        return el


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

    def _extract_text_and_description(self, elem):
        """Extract text and description from para elements.
        
        Description exists only at the start of the first para if:
        - The para has class="italic", OR
        - There's no text before the first child AND first child is inline italic
        """

        
        # Get list of paras to cheok
        if elem.tag.lower() in ("para", "p"):
            paras = [elem]
        
        else:
            paras = elem.findall(".//para") or elem.findall(".//p")
        
        if not paras:
            return "", ""
        
        first_para = paras[0]
        
        # Case 1: para has class="italic" → all is description
        if first_para.attrib.get("class") == "italic":
            description = "".join(first_para.itertext()).strip()
            return "", description
        
        # Case 2: Check if first child is italic with NO text before it
        # elem.text is the text before the first child element
        has_text_before = first_para.text and first_para.text.strip()
        
        if not has_text_before:
            # Find first element child that is emphasis or inline
            first_child = None
            for child in first_para:
                if child.tag in ('emphasis', 'inline'):
                    first_child = child
                    break
            
            if first_child is not None and hasattr(first_child, 'tag') and is_italic(first_child): # First child is italic with no text before → it's a description
                description = "".join(first_child.itertext()).strip()
                # Get all text excluding the italic
                all_text = re.sub(r"\s+", " ", "".join(first_para.itertext())).strip()
                text = all_text.replace(description, "", 1).strip()
                return text, description
        
        # No description found - all content is text
        all_texts = []
        for para in paras:
            para_text = re.sub(r"\s+", " ", "".join(para.itertext())).strip()
            if para_text:
                all_texts.append(para_text)
        
        return " ".join(all_texts), ""

    def _pull_paras(self, elem):
        text, _ = self._extract_text_and_description(elem)
        return text

    def _extract_description(self, elem):
        _, description = self._extract_text_and_description(elem)
        return description

    def _is_interjection_element(self, et_elem):
        """
        Returns True if the element is an interjection, otherwise False.
        """
        return False

    def _interjection_type(self, et_elem):
        """
        speaker - there is a member of parliament who said the interjection
        office - the speaker, president, or clerk, made the interjection
        general - the interjection is not attribuited to a specific speaker
        unrecorded - the interjection is attributed, but the actual speech is
        not recorded
        unattributed - there is text, but no definitive author attribution
        """

        raise FailedInterjectionTypeAssingment(et_elem)

    def _interjection_flag(self, et_elem):
        """
        Returns:
          0 - not an interjection
             1 - speaker - there is a member of parliament who said the interjection
             2 - general - the interjection is not attribuited to a specific speaker
             3 - office - the speaker, president, or clerk, made the interjection
             4 - unrecorded - the interjection is attributed, but the actual speech is not recorded
             5 - unattributed - there is text, but no definitive author attribution
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
            elif t == "unrecorded":
                return 4
            elif t == "unattributed":
                return 5
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
        record_office_interjector=False,
        record_unrecored_interjector=False,
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
                if interject_type == 1:
                    author = self._extract_talker(child)
                elif record_office_interjector and interject_type == 3:
                    author = self._extract_talker(child)
                elif record_unrecored_interjector and interject_type == 4:
                    author = self._extract_talker(child)
                elif interject_type == 3:
                    author = "10000"
                else:
                    author = ""
                interjections.append(
                    {
                        "text": self._clean_text(self._pull_paras(child)),
                        "author": author,
                        "sequence": interj_count,
                        "type": interject_type,
                        "description": self._clean_text(self._extract_description(child))
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


def print_tag_tree(element, max_depth, indent=0):
    if indent >= max_depth:
        return
    print("  " * indent + f"{element.tag}")
    for child in element:
        print_tag_tree(child, max_depth, indent + 1)


class HansardExtractor:

    def __init__(
        self,
        source,
        chamber_parsing_class,
        speech_parsing_class,
        from_file=False,
    ):
        """
        :param source: XML filename or string, depending on from_file.
        :param from_file: If True, treat source as filename. If False, treat as string.
        """

        self.chamber_parsing_class = chamber_parsing_class
        self.speech_parsing_class = speech_parsing_class
        if from_file:
            hansard_string = open(source).read()
        else:
            hansard_string = source

        if len(hansard_string) == 0:
            raise EmptyDocumentError

        cleaned_string = self._clean_hansard(hansard_string)
        self.root = ET.fromstring(cleaned_string)

    def extract(self):
        chambers = self._get_distinct_chambers()
        info_dict = self.get_session_info()
        parliament = info_dict.get("parliament")
        return_list = [info_dict.copy() for _ in chambers]
        for i, (k, v) in enumerate(chambers.items()):
            parser = self.chamber_parsing_class(
                v,
                info_dict["date"],
                speech_parsing_class=self.speech_parsing_class,
                parliament=parliament,
            )
            try:
                docs = parser.extract()
            except HansardNoElementsException:
                docs = []
            return_list[i]["documents"] = docs
            return_list[i]["chamber"] = k
        return return_list

    def _get_distinct_chambers(self):
        raw_chambers = {
            x.tag.replace(".xscript", ""): x
            for x in self.root.getchildren()
            if not x.tag in ["session.header", "debate", "para"]
        }
        hanging_debates = [
            x for x in self.root.getchildren() if x.tag == "debate"
        ]

        for element in hanging_debates:
            debate_info = element.find("debateinfo")
            if (
                debate_info is not None
                and debate_info.findtext("type")
                and "notice" in debate_info.findtext("type").lower()
                and "answer" in debate_info.findtext("type").lower()
            ):
                if "answers.to.questions" in raw_chambers.keys():
                    raw_chambers["answers.to.questions"].append(element)
                else:
                    raw_chambers["answers.to.questions"] = ET.Element(
                        "answers.to.questions"
                    )
                    raw_chambers["answers.to.questions"].append(element)
            else:
                raw_chambers["chamber"].append(element)

        # # Special check for qeustions on notice
        # main_element = raw_chambers.get("chamber")
        # if main_element is not None:
        #     debates = [
        #         x for x in list(main_element) if x.tag.lower() == "debate"
        #     ]
        #     for element in debates:
        #         debate_info = element.find("debateinfo")
        #         if (
        #             debate_info is not None
        #             and debate_info.findtext("type")
        #             and "notice" in debate_info.findtext("type").lower()
        #             and "answer" in debate_info.findtext("type").lower()
        #         ):
        #             raw_chambers["chamber"].remove(element)
        #             if "answers.to.questions" in raw_chambers.keys():
        #                 raw_chambers["answers.to.questions"].append(element)
        #             else:
        #                 raw_chambers["answers.to.questions"] = ET.Element(
        #                     "answers.to.questions"
        #                 )
        #                 raw_chambers["answers.to.questions"].append(element)

        return raw_chambers

    def get_session_info(self):
        info = self.root.find("session.header")
        date = (
            info.findtext("date") if info is not None else None
        ) or self.root.get("date")
        parliament = (
            info.findtext("parliament.no") if info is not None else None
        ) or self.root.get("parliament.no")
        session = (
            info.findtext("session.no") if info is not None else None
        ) or self.root.get("session.no")
        period = (
            info.findtext("period.no") if info is not None else None
        ) or self.root.get("period.no")
        house = (
            info.findtext("chamber") if info is not None else None
        ) or self.root.get("chamber")

        if all(x is None for x in [date, house]):
            raise ValueError("Missing session info")

        if date is not None:
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
                try:
                    date = datetime.datetime.strptime(date, fmt)
                    date = date.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue

        return {
            "date": date,
            "parliament": int(parliament) if parliament is not None else None,
            "session": int(session) if session is not None else None,
            "period": int(period) if period is not None else None,
            "house": house,
        }

    def _clean_hansard(self, string):
        # Step 1: Strip problematic declarations
        lines = string.split("\n")
        if lines:
            for i, line in enumerate(lines):
                if "<hansard" in line.lower():
                    string = "\n".join(lines[i:])
                    break

        # Step 2: Replace character entities
        char_map = {
            "&mdash;": "---",
            "&nbsp;": " ",  # optional: handles Word exports
        }
        for k, v in char_map.items():
            string = string.replace(k, v)

        # Step 3: Remove unbound namespace-prefixed tags (mc:, v:, o:, w10:, etc.)
        # This prevents XML parser from failing
        string = re.sub(r"<(/?)(mc|v|o|w10|w|o14|m):[^>]*>", "", string)
        string = re.sub(
            r'\s(xmlns:[a-zA-Z0-9]+)="[^"]+"', "", string
        )  # remove xmlns decls
        string = re.sub(
            r'\s[a-zA-Z0-9]+:[a-zA-Z0-9\-]+="[^"]*"', "", string
        )  # remove prefix:attr="..."

        # Remove all break elements
        string = re.sub(r"<BREAK[^>]*>", "", string, flags=re.IGNORECASE)
        string = re.sub(r"<TAB[^>]*>", "", string, flags=re.IGNORECASE)

        # Step 4: Parse using forgiving HTML parser
        try:
            repaired = html.fromstring(string)
            ET.strip_tags(repaired, ET.Comment)
            fixed_xml = html.tostring(repaired, method="xml").decode()
        except ET.XMLSyntaxError:
            raise FailedTextExtractionException(
                "XML could not be parsed even after cleaning."
            )

        return fixed_xml

    def _find_session_date(self):
        # 1. Try <HANSARD DATE="...">
        hansard_elem = self.root
        if hansard_elem is not None and hansard_elem.get("date"):
            date_str = hansard_elem.get("date")
        else:
            # 2. Try <DAY.START DATE="...">
            day_start_elem = self.root.find(".//day.start")
            if day_start_elem is not None and day_start_elem.get("date"):
                date_str = day_start_elem.get("date")
            else:
                # 3. Fallback to <date> element
                date_elem = self.root.find(".//date")
                date_str = (
                    date_elem.text.strip()
                    if date_elem is not None and date_elem.text
                    else None
                )

        if date_str:
            # Try parsing multiple formats
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
                try:
                    parsed_date = datetime.datetime.strptime(date_str, fmt)
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue

        # If no valid date found, raise an error
        raise ValueError("No valid session date found in the XML.")

def is_italic(el):
    if el.tag == "inline":
        return (  el.attrib.get("font-weight") == "bold" or el.attrib.get("font-style") == "italic" or el.attrib.get("class") == "italic")
    elif el.tag.lower()== 'emphasis':
       return el.attrib.get('font-slant') == "ITAL"
    else:
       return False
