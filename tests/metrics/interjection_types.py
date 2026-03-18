"""
Metric: Type 1 (speaker) interjection count.
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


class Type1InterjectionCountMetric(CountMetric):
    """Count type 1 (speaker) interjections."""
    
    @property
    def name(self) -> str:
        return "t1_speaker"
    
    @property
    def display_name(self) -> str:
        return "T1 Speaker"
    
    @property
    def description(self) -> str:
        return "Type 1 interjections - attributed to a specific speaker (MP by name)"
    
    def count(self, documents: list) -> int:
        return sum(1 for ij in get_all_interjections(documents) if ij.get("type") == 1)


class Type2InterjectionCountMetric(CountMetric):
    """Count type 2 (general) interjections."""
    
    @property
    def name(self) -> str:
        return "t2_general"
    
    @property
    def display_name(self) -> str:
        return "T2 General"
    
    @property
    def description(self) -> str:
        return "Type 2 interjections - general/unattributed (e.g., 'Opposition members interjecting')"
    
    def count(self, documents: list) -> int:
        return sum(1 for ij in get_all_interjections(documents) if ij.get("type") == 2)


class Type3InterjectionCountMetric(CountMetric):
    """Count type 3 (office) interjections."""
    
    @property
    def name(self) -> str:
        return "t3_office"
    
    @property
    def display_name(self) -> str:
        return "T3 Office"
    
    @property
    def description(self) -> str:
        return "Type 3 interjections - from office holders (President, Clerk, Speaker)"
    
    def count(self, documents: list) -> int:
        return sum(1 for ij in get_all_interjections(documents) if ij.get("type") == 3)


class Type4InterjectionCountMetric(CountMetric):
    """Count type 4 (unrecorded) interjections."""
    
    @property
    def name(self) -> str:
        return "t4_unrecorded"
    
    @property
    def display_name(self) -> str:
        return "T4 Unrecorded"
    
    @property
    def description(self) -> str:
        return "Type 4 interjections - unrecorded/general crowd reactions"
    
    def count(self, documents: list) -> int:
        return sum(1 for ij in get_all_interjections(documents) if ij.get("type") == 4)


class Type5InterjectionCountMetric(CountMetric):
    """Count type 5 (unattributed) interjections."""
    
    @property
    def name(self) -> str:
        return "t5_unattributed"
    
    @property
    def display_name(self) -> str:
        return "T5 Unattributed"
    
    @property
    def description(self) -> str:
        return "Type 5 interjections - unattributed (text present but no definitive author)"
    
    def count(self, documents: list) -> int:
        return sum(1 for ij in get_all_interjections(documents) if ij.get("type") == 5)
