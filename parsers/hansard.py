from prisma import Prisma
import asyncio
import os 
import xml.etree.ElementTree as ET
from tqdm import tqdm 

class HansardSpeechExtractorA:
    MAIN_TAGS = ('speech', 'question', 'answer', 'continue', 'interjection')

    def __init__(self, xml_file_or_root):
        if isinstance(xml_file_or_root, str):
            tree = ET.parse(xml_file_or_root)
            self.root = tree.getroot()
        else:
            self.root = xml_file_or_root
        self.session_date = self._find_session_date()

    def _find_session_date(self):
        date_elem = self.root.find('.//session.header/date')
        return date_elem.text.strip() if date_elem is not None and date_elem.text else None

    def extract(self):
        print_tag_tree(self.root,3)
        # Iterate in document order
        elements = []
        for elem in self.root.iter():
            if elem.tag in self.MAIN_TAGS:
                elements.append(elem)
        results = []
        for elem in elements:
                entry = self._extract_entry(elem, elem.tag)
                if entry.get('speaker') and entry.get('text'):
                    results.append(entry)

        if len(results) == 0:
            raise Exception('Failed to parse')
        return results


    def _extract_talker(self, talker_elem):
        if talker_elem is None:
            return None, self.session_date
        names = [n.text for n in talker_elem.findall('name') if n.text]
        name = names[0] if names else None
        date = talker_elem.findtext('time.stamp', default=None) or self.session_date
        return name, date

    def _extract_text(self, elem):
        texts = []
        elements = elem.findall('.//para')
        for p in elements:
            para_text = ''.join(p.itertext()).strip()
            if para_text:
                texts.append(para_text)
        return '\n'.join(texts)

    def _extract_entry(self, elem, tag_type):
        # All these tags have a "talk.start"
        talk_start = elem.find('talk.start')
        if talk_start is not None:
            talker = talk_start.find('talker')
            name, date = self._extract_talker(talker)
            text = self._extract_text(talk_start)
        else:
            talker = elem.find('talker')
            name, date = self._extract_talker(talker)
            text = self._extract_text(elem)
        # Some "continue"/"interjection" nodes may have direct text as well.
        if elem != talk_start:
            extra = self._extract_text(elem)
            if extra and not text:
                text = extra
            elif extra and extra not in text:
                text += '\n' + extra
        return {
            'speaker': name,
            'date': date,
            'text': text.strip(),
            'type': tag_type
        }


def print_tag_tree(element, max_depth, indent=0):
    if indent >= max_depth:
        return
    print('  ' * indent + f"{element.tag}")
    for child in element:
        print_tag_tree(child, max_depth, indent + 1)
        

def main():
    db = Prisma()

    await db.connect()

    groups = {'House of Reps Hansard':None, 'Senate Hansard':None, 'Hansard':None}
    for group_name in groups.keys():
        g = await db.sourcegroup.find_unique(where={'name': group_name})
        if not existing:
            g = await db.sourcegroup.create({'name': group_name})
        groups[group_name] = g.id

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
        self = HansardSpeechExtractorA(filename)
        self.extract()
        
