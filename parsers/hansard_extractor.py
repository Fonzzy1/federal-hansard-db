import datetime
import re
from lxml import html
import lxml.etree as ET
from parsers.errors import *


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

def print_tag_tree(element, max_depth, indent=0):
    if indent >= max_depth:
        return
    print("  " * indent + f"{element.tag}")
    for child in element:
        print_tag_tree(child, max_depth, indent + 1)

def is_italic(el):
    if el.tag == "inline":
        return (  el.attrib.get("font-weight") == "bold" or el.attrib.get("font-style") == "italic" or el.attrib.get("class") == "italic")
    elif el.tag.lower()== 'emphasis':
       return el.attrib.get('font-slant') == "ITAL"
    else:
       return False
