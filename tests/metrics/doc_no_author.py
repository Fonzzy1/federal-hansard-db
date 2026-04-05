"""
Metric: Documents with empty author.
"""

from .base import IssueMetric


class EmptyDocAuthorMetric(IssueMetric):
    """Find documents with no author field."""
    
    @property
    def name(self) -> str:
        return "doc_no_author"
    
    @property
    def display_name(self) -> str:
        return "Doc No Author"
    
    @property
    def description(self) -> str:
        return "Documents (speeches/questions/answers) with no author field"
    
    def find_issues(self, documents: list) -> list:
        return [d for d in documents if not d.get("author")]
