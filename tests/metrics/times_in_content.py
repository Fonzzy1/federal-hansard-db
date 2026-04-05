"""
Metric: Find times in content.
"""

import re

from .base import IssueMetric


TIME_IN_BRACKETS_PATTERN = re.compile(r'[\[\(][^\]\)]*\d{1,2}[.:]\d{2}\s*(am|pm|a\.m\.|p\.m\.)', re.IGNORECASE)


class TimesInContentMetric(IssueMetric):
    """Find content containing time patterns inside brackets."""
    
    @property
    def name(self) -> str:
        return "times_in_content"
    
    @property
    def display_name(self) -> str:
        return "Times in Content"
    
    @property
    def description(self) -> str:
        return "Time patterns (e.g., [7.30 pm]) inside brackets that should be stripped"
    
    def find_issues(self, documents: list) -> list:
        issues = []
        
        def has_time_in_brackets(text):
            """Check if time pattern appears inside brackets in first 10 words."""
            if not text:
                return False
            words = text.split()[:10]
            first_10_text = " ".join(words)
            return TIME_IN_BRACKETS_PATTERN.search(first_10_text) is not None
        
        for d in documents:
            text = d.get("text", "")
            if has_time_in_brackets(text):
                issues.append({"type": d.get("type"), "text": text[:60], "where": "speech"})
            
            for ij in d.get("interjections", []):
                ij_text = ij.get("text", "")
                if has_time_in_brackets(ij_text):
                    issues.append({"type": d.get("type"), "text": ij_text[:60], "where": "interjection"})
            
            if "answer" in d:
                ans_text = d.get("answer", {}).get("text", "")
                if has_time_in_brackets(ans_text):
                    issues.append({"type": d.get("type"), "text": ans_text[:60], "where": "answer"})
                for ij in d.get("answer", {}).get("interjections", []):
                    ij_text = ij.get("text", "")
                    if has_time_in_brackets(ij_text):
                        issues.append({"type": d.get("type"), "text": ij_text[:60], "where": "answer_interjection"})
        
        return issues
