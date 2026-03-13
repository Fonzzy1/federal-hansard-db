#!/usr/bin/env python3
"""
Hansard Parser Report - Generates a diagnostic report for each parser/test file.

Run with: python3 tests/run_report.py
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import (
    hansard1901,
    hansard1981,
    hansard1992,
    hansard1997,
    hansard1998,
    hansard2011,
    hansard2012,
    hansard2021,
)

TESTS_DIR = Path(__file__).parent

# Map year ranges to parser modules
PARSER_MAPPING = {
    (1901, 1980): hansard1901,
    (1981, 1991): hansard1981,
    (1992, 1996): hansard1992,
    (1997, 1997): hansard1997,
    (1998, 2007): hansard1998,
    (2011, 2011): hansard2011,
    (2012, 2020): hansard2012,
    (2021, 2026): hansard2021,
}


def get_all_test_files():
    # Exclude test.xml - it's likely not a year-based test file
    return sorted(f for f in TESTS_DIR.glob("*.xml") if f.stem != "test")


def get_parser_for_year(year):
    if year == "2025a":
        return hansard2021
    year = int(year)
    for (start, end), parser in PARSER_MAPPING.items():
        if start <= year <= end:
            return parser
    return None


def get_all_documents(parsed_result):
    if not parsed_result:
        return []
    if isinstance(parsed_result, list) and len(parsed_result) > 0:
        return parsed_result[0].get("documents", [])
    return []


def q_all_interjections(documents):
    return [
        interj
        for x in documents
        for interj in x.get("interjections", [])
        + x.get("answer", {}).get("interjections", [])
    ]


def q_type_n_interjections(documents, n):
    return [
        interj
        for x in documents
        for interj in x.get("interjections", [])
        + x.get("answer", {}).get("interjections", [])
        if interj.get("type") == n
    ]


def q_speaker_interjections(documents):
    return q_type_n_interjections(documents, 1)


def q_general_interjections(documents):
    return q_type_n_interjections(documents, 2)


def q_office_interjections(documents):
    return q_type_n_interjections(documents, 3)


def q_unrecorded_interjections(documents):
    return q_type_n_interjections(documents, 4)


# Parsers that expect actual author IDs (not 10000 placeholder) for office interjections
PARSERS_EXPECT_REAL_OFFICE_AUTHOR = {hansard2011, hansard2012, hansard2021}


def get_interjections_with_empty_author(documents, parser):
    """Get all interjections with empty author, grouped by type."""
    all_interjections = q_all_interjections(documents)
    
    type1_no_author = []
    type3_no_author = []
    
    for ij in all_interjections:
        author = ij.get("author", "")
        if not author:  # Empty string
            if ij.get("type") == 1:
                type1_no_author.append(ij)
            elif ij.get("type") == 3:
                type3_no_author.append(ij)
    
    return type1_no_author, type3_no_author


def q_interjections_with_procedural_keywords_not_office(documents):
    keywords = ["PRESIDENT", "CLERK", "SPEAKER"]
    return [
        interj
        for x in documents
        for interj in x.get("interjections", [])
        + x.get("answer", {}).get("interjections", [])
        if interj.get("type") != 3
        and any(kw in interj.get("text", "") for kw in keywords)
    ]


def q_interjections_with_interjecting_not_general_or_unrecorded(documents):
    return [
        interj
        for x in documents
        for interj in x.get("interjections", [])
        + x.get("answer", {}).get("interjections", [])
        if interj.get("type") not in [2, 4]
        and "interjecting" in interj.get("text", "").lower()
    ]


def q_raw_member_interjecting_text(documents):
    return [
        x
        for x in documents
        if "members interjecting"
        in x.get("answer", {"text": ""})["text"] + x.get("text", "")
    ]


import re

# Patterns for titles (e.g., "Mr Watt", "Senator Smith", "Sir John", "Mrs Jones")
TITLE_PATTERN = re.compile(r'\b(Mr|Mrs|Ms|Dr|Senator|Sir|Madam|Hon)\s+\w+', re.IGNORECASE)

# Pattern for titles at START of text (within first few words) followed by -
TITLE_AT_START_PATTERN = re.compile(r'^(Mr|Mrs|Ms|Dr|Senator|Sir|Madam|Hon)\s+\w+.*?\s*-\s*', re.IGNORECASE)

# Patterns for times (e.g., "10:30 am", "2:15pm", "10.30 a.m.")
TIME_PATTERN = re.compile(r'\b\d{1,2}[.:]\d{2}\s*(am|pm|a\.m\.|p\.m\.)\b', re.IGNORECASE)


def get_titles_at_speech_start(documents):
    """Find speeches where title appears in first few words (potential interjection not extracted)."""
    results = []
    
    for doc in documents:
        text = doc.get("text", "")
        # Check if title pattern appears at the start of text (within first 50 chars)
        if text and TITLE_AT_START_PATTERN.match(text[:80]):
            results.append({"type": doc.get("type"), "text": text[:60], "where": "speech"})
        
        # Check answers
        if "answer" in doc:
            ans_text = doc.get("answer", {}).get("text", "")
            if ans_text and TITLE_AT_START_PATTERN.match(ans_text[:80]):
                results.append({"type": doc.get("type"), "text": ans_text[:60], "where": "answer"})
    
    return results


def get_titles_at_interjection_start(documents):
    """Find interjections where title appears at start (title not stripped)."""
    results = []
    
    for doc in documents:
        # Check interjections
        for ij in doc.get("interjections", []):
            ij_text = ij.get("text", "")
            if ij_text and TITLE_AT_START_PATTERN.match(ij_text[:80]):
                results.append({"type": doc.get("type"), "text": ij_text[:60], "where": "interjection", "ij_type": ij.get("type")})
        
        # Check answer interjections
        if "answer" in doc:
            for ij in doc.get("answer", {}).get("interjections", []):
                ij_text = ij.get("text", "")
                if ij_text and TITLE_AT_START_PATTERN.match(ij_text[:80]):
                    results.append({"type": doc.get("type"), "text": ij_text[:60], "where": "answer_interjection", "ij_type": ij.get("type")})
    
    return results


def get_documents_with_titles(documents):
    """Find documents/interjections that contain title-like patterns."""
    results = []
    
    # Check speeches/questions/answers
    for doc in documents:
        text = doc.get("text", "")
        if TITLE_PATTERN.search(text):
            results.append({"type": doc.get("type"), "text": text[:60], "where": "speech"})
        
        # Check interjections
        for ij in doc.get("interjections", []):
            ij_text = ij.get("text", "")
            if TITLE_PATTERN.search(ij_text):
                results.append({"type": doc.get("type"), "text": ij_text[:60], "where": "interjection"})
        
        # Check answers
        if "answer" in doc:
            ans_text = doc.get("answer", {}).get("text", "")
            if TITLE_PATTERN.search(ans_text):
                results.append({"type": doc.get("type"), "text": ans_text[:60], "where": "answer"})
            for ij in doc.get("answer", {}).get("interjections", []):
                ij_text = ij.get("text", "")
                if TITLE_PATTERN.search(ij_text):
                    results.append({"type": doc.get("type"), "text": ij_text[:60], "where": "answer_interjection"})
    
    return results


def get_documents_with_times(documents):
    """Find documents/interjections that contain time-like patterns."""
    results = []
    
    # Check speeches/questions/answers
    for doc in documents:
        text = doc.get("text", "")
        if TIME_PATTERN.search(text):
            results.append({"type": doc.get("type"), "text": text[:60], "where": "speech"})
        
        # Check interjections
        for ij in doc.get("interjections", []):
            ij_text = ij.get("text", "")
            if TIME_PATTERN.search(ij_text):
                results.append({"type": doc.get("type"), "text": ij_text[:60], "where": "interjection"})
        
        # Check answers
        if "answer" in doc:
            ans_text = doc.get("answer", {}).get("text", "")
            if TIME_PATTERN.search(ans_text):
                results.append({"type": doc.get("type"), "text": ans_text[:60], "where": "answer"})
            for ij in doc.get("answer", {}).get("interjections", []):
                ij_text = ij.get("text", "")
                if TIME_PATTERN.search(ij_text):
                    results.append({"type": doc.get("type"), "text": ij_text[:60], "where": "answer_interjection"})
    
    return results


def generate_report():
    """Generate a diagnostic report for all parsers and test files."""
    print("=" * 80)
    print("HANSARD PARSER DIAGNOSTIC REPORT")
    print("=" * 80)
    
    test_files = get_all_test_files()
    print(f"\nFound {len(test_files)} test files\n")
    
    results = []
    
    for test_file in test_files:
        year = test_file.stem
        parser = get_parser_for_year(year)
        
        report = {
            "year": year,
            "parser": parser.__name__ if parser else None,
            "error": None,
            "docs": 0,
            "speeches": 0,
            "questions": 0,
            "answers": 0,
            "total_interjections": 0,
            "type1_speaker": 0,
            "type2_general": 0,
            "type3_office": 0,
            "type4_unrecorded": 0,
            "office_missing_10000": 0,
            "non_office_with_keywords": 0,
            "bad_interjecting_types": 0,
            "raw_member_interjecting": 0,
            "type1_no_author": 0,
            "type3_no_author": 0,
            "examples_type1_no_author": [],
            "examples_type3_no_author": [],
            "docs_no_author": 0,
            "examples_docs_no_author": [],
            "titles_in_speech_start": 0,
            "examples_titles_in_speech_start": [],
            "titles_in_interjection_start": 0,
            "examples_titles_in_interjection_start": [],
            "titles_in_content": 0,
            "examples_titles_in_content": [],
            "times_in_content": 0,
            "examples_times_in_content": [],
        }
        
        if parser is None:
            report["error"] = "No parser found"
            results.append(report)
            continue
        
        try:
            text = test_file.read_text()
            result = parser.parse(text)
            
            if not isinstance(result, list):
                report["error"] = f"parse() returned {type(result).__name__}, expected list"
                results.append(report)
                return results
            
            if len(result) == 0:
                results.append(report)
                return results
            
            documents = get_all_documents(result)
            report["docs"] = len(documents)
            
            # Count document types
            for doc in documents:
                t = doc.get("type", "")
                if t == "speech":
                    report["speeches"] += 1
                elif t == "question":
                    report["questions"] += 1
                    if "answer" in doc:
                        report["answers"] += 1
                elif t == "answer":
                    report["answers"] += 1
            
            # Count interjections
            all_interjections = q_all_interjections(documents)
            report["total_interjections"] = len(all_interjections)
            report["type1_speaker"] = len(q_speaker_interjections(documents))
            report["type2_general"] = len(q_general_interjections(documents))
            report["type3_office"] = len(q_office_interjections(documents))
            report["type4_unrecorded"] = len(q_unrecorded_interjections(documents))
            
            # Check for issues
            office_ij = q_office_interjections(documents)
            # For newer parsers (2011+), office should have REAL author IDs, not 10000
            # For older parsers, office should have 10000
            if parser in PARSERS_EXPECT_REAL_OFFICE_AUTHOR:
                # Should NOT have 10000, should have real author
                office_missing = [ij for ij in office_ij if ij.get("author") == "10000"]
                report["office_missing_10000"] = len(office_missing)
                report["examples_office_missing_10000"] = [ij.get("text", "")[:60] for ij in office_missing]
            else:
                # Should have 10000
                office_missing = [ij for ij in office_ij if ij.get("author") != "10000"]
                report["office_missing_10000"] = len(office_missing)
                report["examples_office_missing_10000"] = [ij.get("text", "")[:60] for ij in office_missing]
            
            report["non_office_with_keywords"] = len(q_interjections_with_procedural_keywords_not_office(documents))
            bad_ij = q_interjections_with_interjecting_not_general_or_unrecorded(documents)
            report["bad_interjecting_types"] = len(bad_ij)
            report["examples_bad_interjecting"] = [ij.get("text", "")[:60] for ij in bad_ij]
            
            non_office_kw = q_interjections_with_procedural_keywords_not_office(documents)
            report["examples_non_office_keywords"] = [ij.get("text", "")[:60] for ij in non_office_kw]
            
            raw_member = q_raw_member_interjecting_text(documents)
            report["raw_member_interjecting"] = len(raw_member)
            report["examples_raw_member_interjecting"] = [d.get("text", "")[:60] for d in raw_member]
            
            # Check for titles in content
            titles_found = get_documents_with_titles(documents)
            report["titles_in_content"] = len(titles_found)
            report["examples_titles_in_content"] = [d["text"] for d in titles_found]
            
            # Check for times in content
            times_found = get_documents_with_times(documents)
            report["times_in_content"] = len(times_found)
            report["examples_times_in_content"] = [d["text"] for d in times_found]
            
            # Check for empty authors
            type1_no_auth, type3_no_auth = get_interjections_with_empty_author(documents, parser)
            report["type1_no_author"] = len(type1_no_auth)
            report["type3_no_author"] = len(type3_no_auth)
            
            # Collect examples
            report["examples_type1_no_author"] = [ij.get("text", "")[:60] for ij in type1_no_auth]
            report["examples_type3_no_author"] = [ij.get("text", "")[:60] for ij in type3_no_auth]
            
            # Check for documents with no author
            docs_no_author = [d for d in documents if not d.get("author")]
            report["docs_no_author"] = len(docs_no_author)
            report["examples_docs_no_author"] = [
                {"type": d.get("type"), "text": d.get("text", "")[:60]} 
                for d in docs_no_author
            ]
            
            # Check for titles at start of speech (potential missed interjection)
            titles_at_start = get_titles_at_speech_start(documents)
            report["titles_in_speech_start"] = len(titles_at_start)
            report["examples_titles_in_speech_start"] = [d["text"] for d in titles_at_start]
            
            # Check for titles at start of interjection (title not stripped)
            titles_at_ij_start = get_titles_at_interjection_start(documents)
            report["titles_in_interjection_start"] = len(titles_at_ij_start)
            report["examples_titles_in_interjection_start"] = [d["text"] for d in titles_at_ij_start]
            
        except Exception as e:
            report["error"] = str(e)
        
        results.append(report)
    
    return results


def print_report(results):
    """Print the report in a readable format."""
    
    # Header
    print(f"{'Year':<8} {'Parser':<20} {'Docs':>5} {'Speech':>6} {'Q':>3} {'Ans':>4} {'Total':>6} {'T1':>4} {'T2':>4} {'T3':>4} {'T4':>4}")
    print("-" * 95)
    
    for r in results:
        if r["error"]:
            print(f"{r['year']:<8} {r.get('parser', ''):<20} {'ERROR':>5}")
            print(f"           Error: {r['error']}")
            continue
        
        print(
            f"{r['year']:<8} "
            f"{r.get('parser', ''):<20} "
            f"{r['docs']:>5} "
            f"{r['speeches']:>6} "
            f"{r['questions']:>3} "
            f"{r['answers']:>4} "
            f"{r['total_interjections']:>6} "
            f"{r['type1_speaker']:>4} "
            f"{r['type2_general']:>4} "
            f"{r['type3_office']:>4} "
            f"{r['type4_unrecorded']:>4}"
        )
        

    
    print("-" * 100)
    
    # Summary
    total_docs = sum(r["docs"] for r in results if not r["error"])
    total_speeches = sum(r["speeches"] for r in results if not r["error"])
    total_questions = sum(r["questions"] for r in results if not r["error"])
    total_answers = sum(r["answers"] for r in results if not r["error"])
    total_interjections = sum(r["total_interjections"] for r in results if not r["error"])
    total_errors = sum(1 for r in results if r["error"])
    
    print(f"\nTOTALS:")
    print(f"  Documents:    {total_docs}")
    print(f"  Speeches:     {total_speeches}")
    print(f"  Questions:    {total_questions}")
    print(f"  Answers:      {total_answers}")
    print(f"  Interjections: {total_interjections}")
    print(f"  Errors:       {total_errors}")


def print_issue_details(results):
    """Print detailed examples of each issue with explanations."""
    
    # Collect all issues from all results
    all_issues = []
    
    for r in results:
        if r["error"] or r["docs"] == 0:
            continue
            
        year = r["year"]
        parser = r.get("parser", "")
        
        # Check each issue type
        if r.get("office_missing_10000", 0) > 0:
            # For newer parsers, this means office interjections still have placeholder 10000 instead of real IDs
            # For older parsers, office should have 10000 - but if they don't, that's an issue
            parser_is_new = "2011" in parser or "2021" in parser
            if parser_is_new:
                reason = "Office interjections have '10000' but should have real author IDs from Hansard"
            else:
                reason = "Office interjections missing '10000' placeholder"
            all_issues.append({
                "year": year,
                "issue": "office_missing_10000",
                "count": r["office_missing_10000"],
                "reason": reason,
                "examples": r.get("examples_office_missing_10000", []),
            })
            
        if r.get("type1_no_author", 0) > 0:
            all_issues.append({
                "year": year,
                "issue": "type1_no_author",
                "count": r["type1_no_author"],
                "reason": "Speaker interjections (type 1) should have an author ID",
                "examples": r.get("examples_type1_no_author", []),
            })
            
        if r.get("type3_no_author", 0) > 0:
            all_issues.append({
                "year": year,
                "issue": "type3_no_author", 
                "count": r["type3_no_author"],
                "reason": "Office interjections (type 3) should have an author ID",
                "examples": r.get("examples_type3_no_author", []),
            })
            
        if r.get("non_office_with_keywords", 0) > 0:
            all_issues.append({
                "year": year,
                "issue": "non_office_keywords",
                "count": r["non_office_with_keywords"],
                "reason": "PRESIDENT/CLERK/SPEAKER keywords should only appear in office interjections",
                "examples": r.get("examples_non_office_keywords", []),
            })
            
        if r.get("bad_interjecting_types", 0) > 0:
            all_issues.append({
                "year": year,
                "issue": "bad_interjecting",
                "count": r["bad_interjecting_types"],
                "reason": "'interjecting' text should only appear in type 2 (general) or type 4 (unrecorded) interjections",
                "examples": r.get("examples_bad_interjecting", []),
            })
            
        if r.get("raw_member_interjecting", 0) > 0:
            all_issues.append({
                "year": year,
                "issue": "raw_member_interjecting",
                "count": r["raw_member_interjecting"],
                "reason": "Speeches contain raw 'members interjecting' text - should be parsed as interjections",
                "examples": r.get("examples_raw_member_interjecting", []),
            })
            
        if r.get("titles_in_speech_start", 0) > 0:
            all_issues.append({
                "year": year,
                "issue": "title_in_speech_start",
                "count": r["titles_in_speech_start"],
                "reason": "Title at start of speech - should have been extracted as interjection",
                "examples": r.get("examples_titles_in_speech_start", []),
            })
            
        if r.get("titles_in_interjection_start", 0) > 0:
            all_issues.append({
                "year": year,
                "issue": "title_in_interjection_start",
                "count": r["titles_in_interjection_start"],
                "reason": "Title at start of interjection - title not stripped from text",
                "examples": r.get("examples_titles_in_interjection_start", []),
            })
            
        if r.get("titles_in_content", 0) > 0:
            all_issues.append({
                "year": year,
                "issue": "titles_in_content",
                "count": r["titles_in_content"],
                "reason": "Content contains titles (Mr, Senator, Sir, etc.) - may need parsing as interjections",
                "examples": r.get("examples_titles_in_content", []),
            })
            
        if r.get("times_in_content", 0) > 0:
            all_issues.append({
                "year": year,
                "issue": "times_in_content",
                "count": r["times_in_content"],
                "reason": "Content contains times that may be misplaced or need special handling",
                "examples": r.get("examples_times_in_content", []),
            })
    
    if not all_issues:
        return
        
    print("\n" + "=" * 80)
    print("ISSUE DETAILS")
    print("=" * 80)
    
    for issue in all_issues:
        print(f"\n[{issue['year']}] {issue['issue']}: {issue['count']}")
        print(f"  WHY: {issue['reason']}")
        if issue.get("examples"):
            print(f"  EXAMPLES:")
            for ex in issue["examples"]:
                print(f"    - {ex}")


if __name__ == "__main__":
    results = generate_report()
    print_report(results)
    print_issue_details(results)
