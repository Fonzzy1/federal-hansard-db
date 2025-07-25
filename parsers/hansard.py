from prisma import Prisma
import asyncio
import os 
import xml.etree.ElementTree as ET
from tqdm import tqdm 
import lxml.etree as ET
from lxml import html
import re
from lxml.etree import _Element


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
        self.message = str(ET.tostring(element,encoding='unicode'))
        super().__init__(self.message)

class FailedTextExtractionException(Exception):
    def __init__(self, element):
        self.message = str(ET.tostring(element,encoding='unicode'))
        super().__init__(self.message)


class HansardSpeechExtractor:

    def _clean_hansard(self, string):
        # Step 1: Strip problematic declarations
        lines = string.split('\n')
        if lines and ('DOCTYPE' in lines[0] or 'encoding' in lines[0]):
            string = '\n'.join(lines[1:])

        # Step 2: Replace character entities
        char_map = {
            "&mdash;": "---",
            "&nbsp;": " ",  # optional: handles Word exports
        }
        for k, v in char_map.items():
            string = string.replace(k, v)

        # Step 3: Remove unbound namespace-prefixed tags (mc:, v:, o:, w10:, etc.)
        # This prevents XML parser from failing
        string = re.sub(r'<(/?)(mc|v|o|w10|w|o14|m):[^>]*>', '', string)
        string = re.sub(r'\s(xmlns:[a-zA-Z0-9]+)="[^"]+"', '', string)  # remove xmlns decls
        string = re.sub(r'\s[a-zA-Z0-9]+:[a-zA-Z0-9\-]+="[^"]*"', '', string)  # remove prefix:attr="..."

        # Step 4: Parse using forgiving HTML parser
        try:
            repaired = html.fromstring(string)
            ET.strip_tags(repaired, ET.Comment)
            fixed_xml = html.tostring(repaired, method='xml').decode()
        except etree.XMLSyntaxError:
            raise FailedTextExtractionException("XML could not be parsed even after cleaning.")
        
        return fixed_xml

    def __init__(self, source, from_file=True):
        """
        :param source: XML filename or string, depending on from_file.
        :param from_file: If True, treat source as filename. If False, treat as string.
        """
        if from_file:
            hansard_string = open(source).read()
        else:
            hansard_string = source

        if len(hansard_string) == 0:
            raise EmptyDocumentError()

        cleaned_string = self._clean_hansard(hansard_string)
        self.tree = ET.fromstring(cleaned_string)
        self.root = self.tree
        self.date = self.root.attrib.get('DATE', None)

    def _find_session_date(self):
        date_elem = self.root.find('.//session.header/date')
        return date_elem.text.strip() if date_elem is not None and date_elem.text else None

    def _extract_elements(self):
        self.elements = []
        # Iterate over document to get all the items
        raw_elements = list(self.tree.iter())
        i = 0
        while i < len(raw_elements):
            el = raw_elements[i]
            tag = el.tag.lower()
            if tag == "question":
                parent = el.getparent()
                answer_ls = [child for child in parent if child is not el and child.tag.lower() == 'answer']
                if len(answer_ls) != 0:
                    self.elements.append({
                        "type": "question_answer",
                        "question": self._clean_element(el),
                        "answer": self._clean_element(answer_ls[0])
                        })
                else:
                    self.elements.append({
                        "type": "question_answer",
                        "question": self._clean_element(el),
                        "answer": None
                        })

                i += 1
            elif tag == "speech":
                self.elements.append({
                    "type": "speech",
                    "element": self._clean_element(el)
                })
            elif tag == "petition":
                self.elements.append({
                    "type": "petition",
                    "element": self._clean_element(el)
                })

            i += 1

    def extract(self):
        self._extract_elements()

        results = []
        for elem in self.elements:
            if elem['type'] == 'question_answer':

                entry = {
                        'type'  :'question_answer',
                        'question_speaker': self._extract_talker(elem['question']),
                        'answer_speaker': self._extract_talker(elem['answer']) if elem['answer'] else None,
                        'question': self._extract_text(elem['question']),
                        'answer': self._extract_text(elem['answer']) if elem['answer'] else None,
                        'date': self.date
                        }

                results.append(entry)

            else:
                entry = {
                        'type': elem['type'],
                        'talker': self._extract_talker(elem['element']),
                        'text':self._extract_text(elem['element']),
                        'date':self.date
                        }
                results.append(entry)


        if len(results) < len(self.elements):
            raise Exception('Failed to parse elements')
        return results


    def _clean_element(self,el):
        for interjection in el.xpath('.//interjection'):
            parent = interjection.getparent()
            if parent is not None:
                parent.remove(interjection)
        return el

    def _extract_talker(self, elem):
        name = ""
        try:
            names = elem.xpath('.//name[@role="metadata"]/text()')
            unique_names = set(names)
            name = list(unique_names)[0]
        except:
            pass
        try:
            names = elem.xpath('.//name[@role="display"]/text()')
            unique_names = set(names)
            name = list(unique_names)[0]
        except:
            pass
        try:
            names = elem.xpath('.//name/text()')
            unique_names = set(names)
            name = list(unique_names)[0]
        except:
            pass

        # Fallback: check attributes of the element itself
        if not name and "speaker" in elem.attrib:
            name = elem.attrib.get("speaker", "")

        if not name:
            raise  FailedTalkerExtractionException(elem)
        return name


    def _extract_text(self, elem):
        texts = []
        # Extract all <para> or <p>
        elements = elem.xpath('.//para | .//p')
        for p in elements:
            para_text = re.sub(r'\s+', ' ', ''.join(p.itertext())).strip()
            if para_text:
                texts.append(para_text)

        # If text was found in <para>/<p>, return it
        if texts:
            return '\n'.join(texts)



def print_tag_tree(element, max_depth, indent=0):
    if indent >= max_depth:
        return
    print('  ' * indent + f"{element.tag}")
    for child in element:
        print_tag_tree(child, max_depth, indent + 1)
        


# db = Prisma()

# await db.connect()

# groups = {'House of Reps Hansard':None, 'Senate Hansard':None, 'Hansard':None}
# for group_name in groups.keys():
#     g = await db.sourcegroup.find_unique(where={'name': group_name})
#     if not existing:
#         g = await db.sourcegroup.create({'name': group_name})
#     groups[group_name] = g.id

base_path = './scrapers/raw_sources/hansard'
folders = ['senate', 'hofreps']

all_files = []
for folder in folders:
    folder_path = os.path.join(base_path, folder)
    if os.path.exists(folder_path):
        files = os.listdir(folder_path)
        # Optionally, join folder name for full paths:
        files = [os.path.join(folder_path, f) for f in files]
        all_files.extend(files)

all_files = sorted(all_files,reverse=True)

for filename in tqdm(all_files, total = len(all_files)):
    try:
        self = HansardSpeechExtractor(filename)
        results = self.extract()
    except EmptyDocumentError:
        pass
    if len(results)==0:
        raise Exception(f'{filename} failed to parse')









    
