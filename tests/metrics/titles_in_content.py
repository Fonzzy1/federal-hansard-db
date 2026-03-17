"""
Metric: Find titles (Mr, Senator, etc.) in content.
"""

import re

from .base import IssueMetric


# Patterns for titles (e.g., "Senator SMITH", "Mr WATT") - only when name is ALL CAPS
TITLE_PATTERN = re.compile(r'\b(Mr|Mrs|Ms|Dr|Senator|Sir|Madam|Hon)\s+[A-Z]{2,}\b')


class TitlesInContentMetric(IssueMetric):
    """Find content containing title patterns."""
    
    @property
    def name(self) -> str:
        return "titles_in_content"
    
    @property
    def display_name(self) -> str:
        return "Titles in Content"
    
    @property
    def description(self) -> str:
        return "Content containing title patterns (Mr, Senator, Sir, etc.) - may indicate missed interjections"
    
    def find_issues(self, documents: list) -> list:
        issues = []
        
        for d in documents:
            # Check speech text
            text = d.get("text", "")
            if TITLE_PATTERN.search(text):
                issues.append({"type": d.get("type"), "text": text[:60], "where": "speech"})
            
            # Check interjections
            for ij in d.get("interjections", []):
                ij_text = ij.get("text", "")
                if TITLE_PATTERN.search(ij_text):
                    issues.append({"type": d.get("type"), "text": ij_text[:60], "where": "interjection"})
            
            # Check answers
            if "answer" in d:
                ans_text = d.get("answer", {}).get("text", "")
                if TITLE_PATTERN.search(ans_text):
                    issues.append({"type": d.get("type"), "text": ans_text[:60], "where": "answer"})
                for ij in d.get("answer", {}).get("interjections", []):
                    ij_text = ij.get("text", "")
                    if TITLE_PATTERN.search(ij_text):
                        issues.append({"type": d.get("type"), "text": ij_text[:60], "where": "answer_interjection"})
        
        return issues
