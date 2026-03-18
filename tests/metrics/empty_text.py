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
        return "Speeches or interjections with empty or minimal text (less than 2 chars)"
    
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
            
            for ij in d.get("interjections", []):
                ij_text = ij.get("text", "")
                if is_empty(ij_text):
                    issues.append({"type": "interjection", "ij_type": ij.get("type"), "text": ij_text[:60] if ij_text else "(empty)"})
            
            if "answer" in d:
                for ij in d.get("answer", {}).get("interjections", []):
                    ij_text = ij.get("text", "")
                    if is_empty(ij_text):
                        issues.append({"type": "answer_interjection", "ij_type": ij.get("type"), "text": ij_text[:60] if ij_text else "(empty)"})
        
        return issues
