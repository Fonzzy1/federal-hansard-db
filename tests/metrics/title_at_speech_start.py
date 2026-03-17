"""
Metric: Title at start of speech (potential missed interjection).
"""

import re

from .base import IssueMetric


# Pattern for titles at START of text followed by ALL CAPS name and -
TITLE_AT_START_PATTERN = re.compile(r'^(Mr|Mrs|Ms|Dr|Senator|Sir|Madam|Hon)\s+[A-Z]{2,}.*?\s*-\s*')


class TitleAtSpeechStartMetric(IssueMetric):
    """Find speeches where title appears in first few words (potential interjection not extracted)."""
    
    @property
    def name(self) -> str:
        return "title_at_speech_start"
    
    @property
    def display_name(self) -> str:
        return "Title at Speech Start"
    
    @property
    def description(self) -> str:
        return "Title (Mr, Senator, etc.) at start of speech text - may be a missed interjection"
    
    def find_issues(self, documents: list) -> list:
        issues = []
        
        for d in documents:
            text = d.get("text", "")
            if text and TITLE_AT_START_PATTERN.match(text[:80]):
                issues.append({"type": d.get("type"), "text": text[:60], "where": "speech"})
            
            if "answer" in d:
                ans_text = d.get("answer", {}).get("text", "")
                if ans_text and TITLE_AT_START_PATTERN.match(ans_text[:80]):
                    issues.append({"type": d.get("type"), "text": ans_text[:60], "where": "answer"})
        
        return issues
