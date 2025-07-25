from prisma import Prisma
import asyncio
import os 
import xml.etree.ElementTree as ET
from tqdm import tqdm 
import lxml.etree as ET
from lxml import html

class HansardNoElementsException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class FailedTalkerExtractionException(Exception):
    def __init__(self, element):
        self.message = str(ET.tostring(element,encoding='unicode'))
        super().__init__(self.message)

class FailedTextExtractionException(Exception):
    def __init__(self, element):
        self.message = str(ET.tostring(element,encoding='unicode'))
        super().__init__(self.message)


class HansardSpeechExtractor:
    MAIN_TAGS_DICT = {
            'speech': './/speech',
            'question': './/question',
            'answer': './/answer',
            'continue': './/continue',
            'interjection': './/interject',
            'petition': './/petition'
            }

    def _clean_hansard(self, string):
        # Remove the first line
        string = '\n'.join(string.split('\n')[1:])
        # Replace the bad chars
        char_map = {
                "&mdash;": '---'
                }
        for k,v in char_map.items():
            string = string.replace(k, v)
        repaired = html.fromstring(string)
        fixed_xml = html.tostring(repaired, method='xml').decode()
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
        cleaned_string = self._clean_hansard(hansard_string)
        self.tree = ET.fromstring(cleaned_string)
        self.root = self.tree
        self.date = self.root.attrib.get('DATE', None)

    def _find_session_date(self):
        date_elem = self.root.find('.//session.header/date')
        return date_elem.text.strip() if date_elem is not None and date_elem.text else None

    def extract(self):
        # Iterate over document to get all the items
        self.elements = []
        for k, v in self.MAIN_TAGS_DICT.items():
            self.elements += self.root.findall(v)
        if len(self.elements) == 0:
            raise Exception('Failed to find Any Elements')

        self.elements= [x for x in self.elements if self._validate_element(x)]

        results = []
        for elem in self.elements:
                entry = self._extract_entry(elem, elem.tag)
                results.append(entry)
        if len(results) < len(self.elements):
            raise Exception('Failed to parse elements')
        return results

    def _validate_element(self,elem):
        #Fail is elem is not para type or doensn't contain a para
        if elem.tag != 'para' and len(elem.findall('./para'))==0:
            return False
        return True




    def _extract_talker(self, elem):
        try:
            # All these tags have a "talk.start"
            talk_start = elem.find('talk.start')
            talker = talk_start.find('talker')
            names = [n.text for n in talker.findall('name') if n.text]
            name = names[0] if names else None
        except:
            raise  FailedTalkerExtractionException(elem)
        if not name:
            raise FailedTalkerExtractionException(elem)
        return name

    def _extract_text(self, elem):
        texts = []
        elements = elem.findall('.//para')
        for p in elements:
            para_text = ''.join(p.itertext()).strip()
            if para_text:
                texts.append(para_text)
        if len(texts)==0:
            raise FailedTextExtractionException(elem)
        return '\n'.join(texts)

    def _extract_entry(self, elem, tag_type):
        name= self._extract_talker(elem)
        text = self._extract_text(elem)
        return {
            'speaker': name,
            'date': self.date,
            'text': text.strip(),
            'type': tag_type
        }

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

all_files = sorted(all_files)

for filename in tqdm(all_files, total = len(all_files)):
    self = HansardSpeechExtractor(filename)
    results = self.extract()

    if len(results)==0:
        raise Exception(f'{filename} failed to parse')







    
