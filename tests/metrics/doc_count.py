"""
Metric: Total document count.
"""

from .base import CountMetric


class DocumentCountMetric(CountMetric):
    @property
    def name(self) -> str:
        return "docs"
    
    @property
    def display_name(self) -> str:
        return "Documents"
    
    @property
    def description(self) -> str:
        return "Total number of documents parsed from the XML"
    
    def count(self, documents: list) -> int:
        return len(documents)
