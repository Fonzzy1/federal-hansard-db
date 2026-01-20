import datetime
import re
from lxml import html
import lxml.etree as ET


"""
Goal is to extract:
    Speeches
    Question and answer pairs
    Petitions

All with interjections removed, and continues sliced together

"""


class HansardNoElementsException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class EmptyDocumentError(Exception):
    def __init__(self):
        super().__init__()


class FailedTalkerExtractionException(Exception):
    def __init__(self, element):
        self.message = str(ET.tostring(element, encoding="unicode"))
        super().__init__(self.message)


class FailedTextExtractionException(Exception):
    def __init__(self, element):
        self.message = str(ET.tostring(element, encoding="unicode"))
        super().__init__(self.message)


class HansardSpeechExtractor:

    def __init__(self, source, from_file=False):
        """
        :param source: XML filename or string, depending on from_file.
        :param from_file: If True, treat source as filename. If False, treat as string.
        """
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
        return_list = [info_dict.copy() for _ in chambers]
        for i, (k, v) in enumerate(chambers.items()):
            parser = ChamberSpeechExtractor(v, info_dict["date"])
            return_list[i]["documents"] = parser.extract()
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
                "answer" in debate_info.findtext("title").lower()
                or "question" in debate_info.findtext("title").lower()
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


class ChamberSpeechExtractor:

    def __init__(self, element, date):
        self.root = element
        self.date = date

        # Build child → parent map
        self.parent_map = {
            child: parent for parent in self.root.iter() for child in parent
        }

    def _extract_elements(self):
        check_elements = self.root.xpath(".//speech | .//question | .//answer")

        # If no relevant elements found, raise an exception
        if not check_elements:
            raise HansardNoElementsException("No parsable Elements")

        self.elements = []
        # Iterate over document to get all the items
        raw_elements = list(self.root.iter())
        i = 0
        while i < len(raw_elements):
            el = raw_elements[i]
            tag = el.tag.lower()
            if tag == "question":
                parent = el.getparent()
                answer = None
                found_el = False
                for child in parent:
                    if child is el:
                        found_el = True
                        continue
                    if found_el and child.tag.lower() == "answer":
                        answer = child
                        break
                if answer is not None:
                    self.elements.append(
                        {
                            "type": "question",
                            "question": self._clean_element(el),
                            "answer": self._clean_element(answer),
                        }
                    )
                ## Exception weh threre is no answer
                else:
                    self.elements.append(
                        {
                            "type": "question",
                            "element": self._clean_element(el),
                        }
                    )

                i += 1
            elif tag == "speech":
                self.elements.append(
                    {"type": "speech", "element": self._clean_element(el)}
                )

            i += 1

    def extract(self):
        self._extract_elements()
        results = []
        for elem in self.elements:
            if elem["type"] == "question" and "answer" in elem.keys():
                # If there is a valid question
                valid_question = self._extract_text(elem["question"])
                valid_answer = self._extract_text(elem["answer"])
                if valid_question and valid_answer:
                    q_interjections, q_text = self._extract_text(
                        elem["question"]
                    )
                    a_interjections, a_text = self._extract_text(elem["answer"])

                    entry = {
                        "type": "question",
                        "interjections": q_interjections,
                        "text": q_text,
                        "author": self._extract_talker(elem["question"]),
                        "title": self._get_debate_info(elem["question"]),
                        "answer": {
                            "type": "answer",
                            "author": self._extract_talker(elem["answer"]),
                            "text": a_text,
                            "interjections": a_interjections,
                            "title": self._get_debate_info(elem["answer"]),
                        },
                    }
                    results.append(entry)
                elif valid_answer and not valid_question:
                    a_interjections, a_text = self._extract_text(elem["answer"])
                    entry = {
                        "type": "answer",
                        "author": self._extract_talker(elem["answer"]),
                        "text": a_text,
                        "interjections": a_interjections,
                        "title": self._get_debate_info(elem["answer"]),
                    }
                    results.append(entry)
                elif valid_question and not valid_answer:

                    q_interjections, q_text = self._extract_text(
                        elem["question"]
                    )

                    entry = {
                        "type": "question",
                        "author": self._extract_talker(elem["question"]),
                        "text": q_text,
                        "interjections": q_interjections,
                        "title": self._get_debate_info(elem["question"]),
                    }
                    results.append(entry)

            else:
                if self._extract_text(elem["element"]):
                    interjections, text = self._extract_text(elem["element"])
                    entry = {
                        "type": elem["type"],
                        "author": self._extract_talker(elem["element"]),
                        "title": self._get_debate_info(elem["element"]),
                        "text": text,
                        "interjections": interjections,
                    }
                    results.append(entry)

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

    def _extract_talker(self, elem):
        name = elem.get("nameid")
        if name and name.lower() != "null":
            return name
        for xpath_expr in [
            "talk.start/talker/name.id",
            ".//name.id/text()",
            ".//NAME/@NAMEID",
            ".//@nameid",
        ]:
            try:
                if "text()" in xpath_expr or "@" in xpath_expr:
                    result = elem.xpath(xpath_expr)
                else:
                    result = elem.find(xpath_expr)
                if result is not None:
                    if isinstance(result, list):
                        unique = set(r for r in result if r.lower() != "null")
                        if len(unique) == 1:
                            return unique.pop()
                    else:
                        if result.text and result.text.lower() != "null":
                            return result.text
            except:
                pass
        return ""

        # try:
        #     names = elem.xpath('.//name[@role="metadata"]/text()')
        #     unique_names = set(names)
        #     return list(unique_names)[0]
        # except:
        #     pass
        # try:
        #     names = elem.xpath('.//name[@role="display"]/text()')
        #     unique_names = set(names)
        #     return list(unique_names)[0]
        # except:
        #     pass
        # try:
        #     names = elem.xpath(".//name/text()")
        #     unique_names = set(names)
        #     return list(unique_names)[0]
        # except:gb
        #     pass

        # if "speaker" in elem.attrib:
        #     return elem.attrib.get("speaker", "")

        # if len([x for x in elem]) == 1:
        #     if [x for x in elem][0].tag in ["p", "para"]:
        #         return ""
        # if len([x for x in elem]) == 0:
        #     return ""
        # if all(
        #     x.tag
        #     in ["p", "para", "quote", "inline", "list", "item", "debateinfo"]
        #     for x in elem
        # ):
        #     return ""
        # print(str(ET.tostring(elem, encoding="unicode")))
        return ""

        raise FailedTalkerExtractionException(elem)

    def _pull_paras(self, elem):
        if elem.find("talk.start") is not None:
            return self._pull_paras(elem.find("talk.start"))

        texts = []
        if elem.tag.lower() in ("p", "para"):
            return re.sub(r"\s+", " ", "".join(elem.itertext())).strip()
        for p in elem.getchildren():
            para_text = self._pull_paras(p)
            if para_text:
                texts.append(para_text)
        return "\n".join(texts)

    def _is_interjection_element(self, et_elem):
        # Check element tag
        if et_elem.tag.lower() in {"interject", "interjection"}:
            return True
        # Check all attribute values
        if any(
            [
                "interject" in x.get("class", "").lower()
                and not "general" in x.get("class", "").lower()
                for x in et_elem.xpath(".//span")
            ]
        ):
            return True
        return False

    def _extract_text(self, elem):
        children = elem.getchildren()
        ## Fix for when we have the embedded interjections
        if "talk.text" in [x.tag for x in children]:
            interjections, text = self._extract_text(elem.find("talk.text"))
            interjection_obj = elem.findall("interjection")
            if interjection_obj:
                if len(interjection_obj) == len(interjections):
                    for i in range(len(interjections)):
                        interjections[i]["author"] = self._extract_talker(
                            interjection_obj[i]
                        )
                else:
                    for i in range(len(interjections)):
                        interjections[i]["author"] = ""
            return interjections, text

        interjections = []
        out_text = []
        interj_count = 1

        for child in children:
            # Collect all consecutive interjections
            if self._is_interjection_element(child):
                key = f"INTERJECTION{interj_count:02d}"
                interjections.append(
                    {
                        "text": self._pull_paras(child),
                        "author": self._extract_talker(child),
                        "sequence": interj_count,
                    }
                )
                out_text.append(f"[{key}]")
                interj_count += 1
            # If it's a continues, append its text
            else:
                out_text.append(self._pull_paras(child))

        final_main_text = " ".join(out_text)
        return interjections, final_main_text


def print_tag_tree(element, max_depth, indent=0):
    if indent >= max_depth:
        return
    print("  " * indent + f"{element.tag}")
    for child in element:
        print_tag_tree(child, max_depth, indent + 1)


def parse(file_text):
    try:
        extractor = HansardSpeechExtractor(file_text)
        results = extractor.extract()
    except EmptyDocumentError:
        results = []
    except HansardNoElementsException:
        results = []
    return results


# self = HansardSpeechExtractor("test.xml", from_file=True)
# print_tag_tree(self.root, 2)
# docs = self.extract()

# [x["chamber"] for x in docs]

# info = self.root.find("session.header")
# print_tag_tree(info, 2)
# [doc for doc in docs if doc.get("interjections")]
# [doc for doc in docs if not doc.get("text")]
