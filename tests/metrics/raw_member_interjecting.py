"""
Metric: Raw "members interjecting" in speech text.
"""

from .base import IssueMetric


class RawMemberInterjectingMetric(IssueMetric):
    """Find speeches that contain raw 'members interjecting' text."""
    
    @property
    def name(self) -> str:
        return "raw_member_interjecting"
    
    @property
    def display_name(self) -> str:
        return "Raw Member Interj."
    
    @property
    def description(self) -> str:
        return "Speeches containing raw 'members interjecting' text - may indicate missed interjection extraction"
    
    def find_issues(self, documents: list) -> list:
        return [
            d for d in documents
            if "members interjecting"
            in d.get("answer", {"text": ""})["text"] + d.get("text", "")
        ]
