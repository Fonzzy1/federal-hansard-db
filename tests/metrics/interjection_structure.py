"""
Metric: Validate interjection structure by type.
"""

import json
from .base import IssueMetric


def get_all_interjections(documents):
    """Get all interjections from documents and answers."""
    return [
        ij
        for d in documents
        for ij in d.get("interjections", [])
        + d.get("answer", {}).get("interjections", [])
    ]


class InterjectionStructureMetric(IssueMetric):
    """Validate interjection structure based on type."""
    
    @property
    def name(self) -> str:
        return "interjection_structure"
    
    @property
    def display_name(self) -> str:
        return "Interjection Structure"
    
    @property
    def description(self) -> str:
        return "Interjections with invalid structure by type"
    
    def find_issues(self, documents: list) -> list:
        issues = []
        for ij in get_all_interjections(documents):
            ij_type = ij.get("type")
            text = ij.get("text")
            author = ij.get("author", "")
            
            if ij_type == 1:
                # Type 1: should have author and text, no description
                if not author:
                    issues.append({**ij, "issue": "Type 1 missing author"})
                if not text:
                    issues.append({**ij, "issue": "Type 1 missing text"})
            
            elif ij_type == 2:
                # Type 2: should have just description, no text, no author
               if not text:
                    issues.append({**ij, "issue": "Type 2 should have text"})

            
            elif ij_type == 3:
                # Type 3: should have author and text, no description
                if not author:
                    issues.append({**ij, "issue": "Type 3 missing author"})
                if not text:
                    issues.append({**ij, "issue": "Type 3 missing text"})

    
    def get_examples(self, items: list, max_examples: int = 5, max_text_len: int = 500) -> list:
        """Return full JSON for each issue."""
        return [
            json.dumps(item, ensure_ascii=False)
            for item in items[:max_examples]
        ]
