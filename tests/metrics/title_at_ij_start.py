"""
Metric: Title at start of interjection (title not stripped).
"""

import re

from .base import IssueMetric


# Pattern for titles at START of text followed by ALL CAPS name and -
TITLE_AT_START_PATTERN = re.compile(r'^(Mr|Mrs|Ms|Dr|Senator|Sir|Madam|Hon)\s+[A-Z]{2,}.*?\s*-\s*')


class TitleAtInterjectionStartMetric(IssueMetric):
    """Find interjections where title appears at start (title not stripped)."""
    
    @property
    def name(self) -> str:
        return "title_at_ij_start"
    
    @property
    def display_name(self) -> str:
        return "Title at IJ Start"
    
    @property
    def description(self) -> str:
        return "Title at start of interjection text - title was not stripped from the interjection"
    
    def find_issues(self, documents: list) -> list:
        issues = []
        
        for d in documents:
            # Check interjections
            for ij in d.get("interjections", []):
                ij_text = ij.get("text", "")
                if ij_text and TITLE_AT_START_PATTERN.match(ij_text[:80]):
                    issues.append({"type": d.get("type"), "text": ij_text[:60], "where": "interjection", "ij_type": ij.get("type")})
            
            # Check answer interjections
            if "answer" in d:
                for ij in d.get("answer", {}).get("interjections", []):
                    ij_text = ij.get("text", "")
                    if ij_text and TITLE_AT_START_PATTERN.match(ij_text[:80]):
                        issues.append({"type": d.get("type"), "text": ij_text[:60], "where": "answer_interjection", "ij_type": ij.get("type")})
        
        return issues
