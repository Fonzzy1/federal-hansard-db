"""
Metric: Empty author by interjection type.
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


class Type1EmptyAuthorMetric(IssueMetric):
    """Find type 1 (speaker) interjections with empty author."""
    
    @property
    def name(self) -> str:
        return "t1_empty_author"
    
    @property
    def display_name(self) -> str:
        return "T1 Empty Author"
    
    @property
    def description(self) -> str:
        return "Type 1 (speaker) interjections with empty/missing author - should have MP name"
    
    def find_issues(self, documents: list) -> list:
        return [
            ij for ij in get_all_interjections(documents)
            if ij.get("type") == 1 and not ij.get("author", "")
        ]


class Type2EmptyAuthorMetric(IssueMetric):
    """Find type 2 (general) interjections with empty author."""
    
    @property
    def name(self) -> str:
        return "t2_empty_author"
    
    @property
    def display_name(self) -> str:
        return "T2 Empty Author"
    
    @property
    def description(self) -> str:
        return "Type 2 (general) interjections with empty author - these are often group statements"
    
    def find_issues(self, documents: list) -> list:
        return [
            ij for ij in get_all_interjections(documents)
            if ij.get("type") == 2 and not ij.get("author", "")
        ]


class Type3EmptyAuthorMetric(IssueMetric):
    """Find type 3 (office) interjections with empty author."""
    
    @property
    def name(self) -> str:
        return "t3_empty_author"
    
    @property
    def display_name(self) -> str:
        return "T3 Empty Author"
    
    @property
    def description(self) -> str:
        return "Type 3 (office) interjections with empty author - should have President/Clerk/Speaker"
    
    def find_issues(self, documents: list) -> list:
        return [
            ij for ij in get_all_interjections(documents)
            if ij.get("type") == 3 and not ij.get("author", "")
        ]


class Type4EmptyAuthorMetric(IssueMetric):
    """Find type 4 (unrecorded) interjections with empty author."""
    
    @property
    def name(self) -> str:
        return "t4_empty_author"
    
    @property
    def display_name(self) -> str:
        return "T4 Empty Author"
    
    @property
    def description(self) -> str:
        return "Type 4 (unrecorded) interjections with empty author"
    
    def find_issues(self, documents: list) -> list:
        return [
            ij for ij in get_all_interjections(documents)
            if ij.get("type") == 4 and not ij.get("author", "")
        ]


class Type5EmptyAuthorMetric(IssueMetric):
    """Find type 5 (unattributed) interjections with empty author."""
    
    @property
    def name(self) -> str:
        return "t5_empty_author"
    
    @property
    def display_name(self) -> str:
        return "T5 Empty Author"
    
    @property
    def description(self) -> str:
        return "Type 5 (unattributed) interjections with empty author"
    
    def find_issues(self, documents: list) -> list:
        return [
            ij for ij in get_all_interjections(documents)
            if ij.get("type") == 5 and not ij.get("author", "")
        ]
