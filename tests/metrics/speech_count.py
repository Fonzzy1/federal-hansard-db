"""
Metric: Speech count.
"""

from .base import CountMetric


class SpeechCountMetric(CountMetric):
    @property
    def name(self) -> str:
        return "speeches"
    
    @property
    def display_name(self) -> str:
        return "Speeches"
    
    @property
    def description(self) -> str:
        return "Number of speech entries (non-question entries)"
    
    def count(self, documents: list) -> int:
        return sum(1 for d in documents if d.get("type") == "speech")
