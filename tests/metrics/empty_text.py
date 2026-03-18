"""
Metric: Find empty speeches and interjections.
"""

import string

from .base import IssueMetric


class EmptyTextMetric(IssueMetric):
    """Find speeches and interjections with empty or minimal text."""
    
    @property
    def name(self) -> str:
        return "empty_text"
    
    @property
    def display_name(self) -> str:
        return "Empty Text"
    
    @property
    def description(self) -> str:
        return "Speeches with empty or minimal text (less than 2 chars)"
    
    def find_issues(self, documents: list) -> list:
        issues = []
        
        def is_empty(text):
            """Check if text is empty after removing whitespace and punctuation."""
            if not text:
                return True
            stripped = text.strip()
            cleaned = stripped.translate(str.maketrans("", "", string.punctuation))
            return not cleaned or len(cleaned) < 2
        
        for d in documents:
            text = d.get("text", "")
            if is_empty(text):
                issues.append({"type": d.get("type"), "text": text[:60] if text else "(empty)"})
            

            if "answer" in d:
                for a in d.get("answer", {}):
                    text = a.get("text", "")
                    if is_empty(text):
                        issues.append({"type": a.get("type"), "text": text[:60] if text else "(empty)"})
            
        return issues
