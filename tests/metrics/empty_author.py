"""
Metric: Find interjections with empty author.
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


class EmptyAuthorMetric(IssueMetric):
    """Find interjections with empty author field."""
    
    @property
    def name(self) -> str:
        return "empty_author"
    
    @property
    def display_name(self) -> str:
        return "Empty Author (All)"
    
    @property
    def description(self) -> str:
        return "All interjections with missing/empty author field (any type)"
    
    def find_issues(self, documents: list) -> list:
        return [ij for ij in get_all_interjections(documents) if not ij.get("author", "")]
