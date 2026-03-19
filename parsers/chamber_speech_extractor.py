import re
from parsers.errors import *


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
