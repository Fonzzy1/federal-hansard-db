"""
Era modules for Federal Hansard parsers.

These modules provide intermediate base classes that group parsers by historical eras:
- earlydigital: 1981-1997
- massdigitisation: 1901-1980, 1998-2010
- modern: 2011-present
"""

from parsers.eras.earlydigital import SpeechExtractorEarlyDigital
from parsers.eras.massdigitisation import SpeechExtractorMassDigitisation
from parsers.eras.modern import SpeechExtractorModern

__all__ = [
    "SpeechExtractorEarlyDigital",
    "SpeechExtractorMassDigitisation",
    "SpeechExtractorModern",
]
