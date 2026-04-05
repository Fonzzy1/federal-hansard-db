"""
Metric: Question count.
"""

from .base import CountMetric


class QuestionCountMetric(CountMetric):
    @property
    def name(self) -> str:
        return "questions"
    
    @property
    def display_name(self) -> str:
        return "Questions"
    
    @property
    def description(self) -> str:
        return "Number of question entries (with or without answers)"
    
    def count(self, documents: list) -> int:
        return sum(1 for d in documents if d.get("type") == "question")
