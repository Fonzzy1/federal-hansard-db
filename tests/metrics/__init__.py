"""
Metrics package - modular tests for parser diagnostics.

Each file in this package contains a single Metric class.
Run with: python3 tests/run_report.py
"""


# Import all metrics for discovery
from .doc_count import DocumentCountMetric
from .speech_count import SpeechCountMetric
from .question_count import QuestionCountMetric
from .answer_count import AnswerCountMetric
from .interjection_count import InterjectionCountMetric
from .interjection_types import (
    Type1InterjectionCountMetric,
    Type2InterjectionCountMetric,
    Type3InterjectionCountMetric,
    Type4InterjectionCountMetric,
    Type5InterjectionCountMetric,
)
from .doc_no_author import EmptyDocAuthorMetric
from .titles_in_content import TitlesInContentMetric
from .title_at_speech_start import TitleAtSpeechStartMetric
from .title_at_ij_start import TitleAtInterjectionStartMetric
from .times_in_content import TimesInContentMetric
from .empty_text import EmptyTextMetric
from .non_office_keywords import NonOfficeWithKeywordsMetric
from .bad_interjecting import BadInterjectingTypesMetric
from .raw_member_interjecting import RawMemberInterjectingMetric
from .interjection_structure import InterjectionStructureMetric


# All metrics - add new metrics here
ALL_METRICS = [
    # Counts
    DocumentCountMetric,
    SpeechCountMetric,
    QuestionCountMetric,
    AnswerCountMetric,
    InterjectionCountMetric,
    Type1InterjectionCountMetric,
    Type2InterjectionCountMetric,
    Type3InterjectionCountMetric,
    Type4InterjectionCountMetric,
    Type5InterjectionCountMetric,
    EmptyDocAuthorMetric,
    TitlesInContentMetric,
    TitleAtSpeechStartMetric,
    TitleAtInterjectionStartMetric,
    TimesInContentMetric,
    EmptyTextMetric,
    NonOfficeWithKeywordsMetric,
    BadInterjectingTypesMetric,
    RawMemberInterjectingMetric,
    InterjectionStructureMetric,
]


def get_all_metrics():
    """Return list of all available metric classes."""
    return ALL_METRICS


def get_metric_by_name(name: str):
    """Get a metric class by its name property."""
    for metric_cls in ALL_METRICS:
        if metric_cls().name == name:
            return metric_cls
    return None
