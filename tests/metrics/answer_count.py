"""
Metric: Answer count.
"""

from .base import CountMetric


class AnswerCountMetric(CountMetric):
    @property
    def name(self) -> str:
        return "answers"
    
    @property
    def display_name(self) -> str:
        return "Answers"
    
    @property
    def description(self) -> str:
        return "Number of answers (standalone answers or questions with answers)"
    
    def count(self, documents: list) -> int:
        count = 0
        for d in documents:
            t = d.get("type", "")
            if t == "question" and "answer" in d:
                count += 1
            elif t == "answer":
                count += 1
        return count
