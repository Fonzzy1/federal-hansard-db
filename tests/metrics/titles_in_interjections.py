"""
Metric: Find titles (Mr, Senator, etc.) in interjections.
"""

import re

from .base import IssueMetric


# Patterns for titles (e.g., "Senator SMITH", "Mr WATT") - only when name is ALL CAPS
TITLE_PATTERN = re.compile(r'\b(Mr|Mrs|Ms|Dr|Senator|Sir|Madam|Hon)\s+[A-Z]{2,}\b')


class TitlesInInterjectionsMetric(IssueMetric):
    """Find interjections containing title patterns."""
    
    @property
    def name(self) -> str:
        return "titles_in_interjections"
    
    @property
    def display_name(self) -> str:
        return "Titles in Interjections"
    
    @property
    def description(self) -> str:
        return "Interjections containing title patterns (Mr, Senator, Sir, etc.) - may indicate parsing issue"
    
    def find_issues(self, documents: list) -> list:
        issues = []
        
        for d in documents:
            # Check interjections in speech
            for ij in d.get("interjections", []):
                ij_text = ij.get("text", "")
                if TITLE_PATTERN.search(ij_text):
                    issues.append({"type": d.get("type"), "text": ij_text[:60], "where": "interjection"})
            
            # Check interjections in answers
            if "answer" in d:
                for ij in d.get("answer", {}).get("interjections", []):
                    ij_text = ij.get("text", "")
                    if TITLE_PATTERN.search(ij_text):
                        issues.append({"type": d.get("type"), "text": ij_text[:60], "where": "answer_interjection"})
        
        return issues
