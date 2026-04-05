"""
Metric: Total interjection count.
"""

from .base import CountMetric


def get_all_interjections(documents):
    """Get all interjections from documents and answers."""
    return [
        ij
        for d in documents
        for ij in d.get("interjections", [])
        + d.get("answer", {}).get("interjections", [])
    ]


class InterjectionCountMetric(CountMetric):
    @property
    def name(self) -> str:
        return "total_interjections"
    
    @property
    def display_name(self) -> str:
        return "Total Interj."
    
    @property
    def description(self) -> str:
        return "Total number of all interjections (types 1-5 combined)"
    
    def count(self, documents: list) -> int:
        return len(get_all_interjections(documents))
