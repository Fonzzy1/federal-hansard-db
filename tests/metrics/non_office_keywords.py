"""
Metric: Non-office interjections with office keywords (PRESIDENT, CLERK, SPEAKER).
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


class NonOfficeWithKeywordsMetric(IssueMetric):
    """Find non-office interjections with office keywords."""
    
    @property
    def name(self) -> str:
        return "non_office_keywords"
    
    @property
    def display_name(self) -> str:
        return "Non-Office + Keywords"
    
    @property
    def description(self) -> str:
        return "Non-type3 interjections containing PRESIDENT/CLERK/SPEAKER - should be type 3"
    
    def find_issues(self, documents: list) -> list:
        keywords = ["PRESIDENT", "CLERK", "SPEAKER"]
        return [
            ij for ij in get_all_interjections(documents)
            if ij.get("type") != 3
            and any(kw in ij.get("text", "") for kw in keywords)
        ]
