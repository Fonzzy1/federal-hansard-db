from prisma import Prisma
import asyncio
import os 
import xml.etree.ElementTree as ET
from tqdm import tqdm 
import lxml.etree as ET


class HansardSpeechExtractorB:
    MAIN_TAGS = ('speech', 'question', 'answer', 'continue', 'interjection', 'petition')
    def __init__(self, source, from_file=True):
        """
        :param source: XML filename or string, depending on from_file.
        :param from_file: If True, treat source as filename. If False, treat as string.
        """
        self.tree = ET.parse(source) if from_file else ET.fromstring(source)
        self.root = self.tree.getroot() if from_file else self.tree
        self.date = self.root.attrib.get('DATE', None)

    def extract(self):
        """Extract records for all main tags, return as list of dicts."""
        result = []
        result += self._extract_petitions()
        result += self._extract_speeches()
        result += self._extract_questions()
        result += self._extract_answers()
        result += self._extract_interjections()
        # Implement _extract_continues if you encounter <CONTINUE> tags
        return result

    def _get_text(self, elem):
        # Utility: get text of all PARA elements beneath elem
        return ' '.join([' '.join(para.itertext()).strip()
                        for para in elem.xpath('.//PARA')]).strip()

    def _find_speaker(self, elem):
        sp = elem.attrib.get('SPEAKER', '')
        if not sp:
            # Try <TALKER>/<NAME>
            tkr = elem.find('.//TALKER/NAME')
            sp = tkr.text if tkr is not None else ''
        return sp

    def _extract_petitions(self):
        out = []
        for p in self.root.xpath('.//PETITION'):
            presenters = p.xpath('./PRESENTER.BLOCK//NAME/text()')
            sp = '; '.join(presenters)
            txt = self._get_text(p)
            out.append({
                "tag": "petition",
                "speaker": sp,
                "text": txt,
                "date": self.date,
            })
        return out

    def _extract_speeches(self):
        out = []
        for s in self.root.xpath('.//SPEECH'):
            sp = self._find_speaker(s)
            txt = self._get_text(s)
            out.append({
                "tag": "speech",
                "speaker": sp,
                "text": txt,
                "date": self.date,
            })
        return out

    def _extract_questions(self):
        out = []
        for q in self.root.xpath('.//QUESTION'):
            sp = self._find_speaker(q)
            txt = self._get_text(q)
            out.append({
                "tag": "question",
                "speaker": sp,
                "text": txt,
                "date": self.date,
            })
        return out

    def _extract_answers(self):
        out = []
        for a in self.root.xpath('.//ANSWER'):
            sp = self._find_speaker(a)
            txt = self._get_text(a)
            out.append({
                "tag": "answer",
                "speaker": sp,
                "text": txt,
                "date": self.date,
            })
        return out

    def _extract_interjections(self):
        out = []
        for i in self.root.xpath('.//INTERJECT'):
            sp = self._find_speaker(i)
            txt = self._get_text(i)
            out.append({
                "tag": "interjection",
                "speaker": sp,
                "text": txt,
                "date": self.date,
            })
        return out

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
        self = HansardSpeechExtractorB(filename)
        self.extract()
        
