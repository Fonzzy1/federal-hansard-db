"""
Base metric class for parser diagnostics.

Each metric should inherit from Metric and implement the `run` method.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class MetricResult:
    """Result of running a metric."""
    name: str
    display_name: str
    description: str
    count: int = 0
    examples: list = field(default_factory=list)
    severity: str = "info"  # info, warning, error
    

class Metric(ABC):
    """Base class for all metrics."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Short name/key for the metric (used in data structures)."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for display in tables."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Detailed description of what this metric checks for."""
        pass
    
    @property
    def severity(self) -> str:
        """Severity level: info, warning, or error."""
        return "info"
    
    @property
    def enabled(self) -> bool:
        """Whether this metric is enabled by default."""
        return True
    
    @abstractmethod
    def run(self, parsed_result: dict) -> MetricResult:
        """
        Run the metric on parsed result.
        
        Args:
            parsed_result: The full dict output from parser.parse()
            
        Returns:
            MetricResult with count, examples, etc.
        """
        pass
    
    def get_examples(self, items: list, max_examples: int = 5, max_text_len: int = 60) -> list:
        """Helper to extract text examples from items."""
        return [
            item.get("text", "")[:max_text_len] if isinstance(item, dict) else str(item)[:max_text_len]
            for item in items[:max_examples]
        ]
    
    def get_documents(self, parsed_result: dict) -> list:
        """Helper to extract documents list from parsed result."""
        if not parsed_result:
            return []
        if isinstance(parsed_result, list) and len(parsed_result) > 0:
            return parsed_result[0].get("documents", [])
        return []


class CountMetric(Metric):
    """Base class for metrics that simply count something."""
    
    @property
    def severity(self) -> str:
        return "info"
    
    def run(self, parsed_result: dict) -> MetricResult:
        documents = self.get_documents(parsed_result)
        count = self.count(documents)
        return MetricResult(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            count=count,
            severity=self.severity
        )
    
    @abstractmethod
    def count(self, documents: list) -> int:
        """Return the count of items."""
        pass


class IssueMetric(Metric):
    """Base class for metrics that detect issues (with examples)."""
    
    @property
    def severity(self) -> str:
        return "warning"
    
    def run(self, parsed_result: dict) -> MetricResult:
        documents = self.get_documents(parsed_result)
        issues = self.find_issues(documents)
        return MetricResult(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            count=len(issues),
            examples=self.get_examples(issues),
            severity=self.severity
        )
    
    @abstractmethod
    def find_issues(self, documents: list) -> list:
        """Return list of issues found."""
        pass
