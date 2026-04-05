"""
Metric: "interjecting" in wrong interjection types.
"""

from .base import IssueMetric


def get_all_interjections(documents):
    """Get all interjections from documents and answers."""
    return [
        ij
        for d in documents
        for ij in d.get("interjections", [])
        + d.get("answer", {}).get("interjections", [])
    ]


class BadInterjectingTypesMetric(IssueMetric):
    """Find interjections with 'interjecting' text in wrong types."""
    
    @property
    def name(self) -> str:
        return "bad_interjecting"
    
    @property
    def display_name(self) -> str:
        return "Bad Interjecting Type"
    
    @property
    def description(self) -> str:
        return "'interjecting' text found in non-type2/non-type4/non-type5 interjections"
    
    def find_issues(self, documents: list) -> list:
        return [
            ij for ij in get_all_interjections(documents)
            if ij.get("type") not in [2, 4, 5]
            and "members interjecting" in ij.get("text", "").lower()
        ]
