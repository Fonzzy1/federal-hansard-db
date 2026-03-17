#!/usr/bin/env python3
"""
Hansard Parser Report - Generates a diagnostic report for each parser/test file.

Run with: python3 tests/run_report.py
"""

import sys
import traceback
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import (
    hansard1901,
    hansard1981,
    hansard1992,
    hansard1997,
    hansard1998,
    hansard2000,
    hansard2011,
    hansard2012,
    hansard2021,
)
from tests.metrics import get_all_metrics
from tests.metrics.base import MetricResult

TESTS_DIR = Path(__file__).parent / "xml"

# Map year ranges to parser modules
PARSER_MAPPING = {
    (1901, 1980): hansard1901,
    (1981, 1991): hansard1981,
    (1992, 1996): hansard1992,
    (1997, 1997): hansard1997,
    (1998, 1999): hansard1998,
    (2000, 2011): hansard2000,
    (2012, 2012): hansard2011,
    (2012, 2021): hansard2012,
    (2022, 2026): hansard2021,
}


def get_all_test_files():
    """Get all XML test files (excluding test.xml and double extensions)."""
    return sorted(f for f in TESTS_DIR.glob("*.xml") if f.stem != "test" and not f.stem.endswith(".xml"))


def get_parser_for_year(year):
    """Get parser module for a given year."""
    if year == "2025a":
        return hansard2021
    year = int(year)
    for (start, end), parser in PARSER_MAPPING.items():
        if start <= year <= end:
            return parser
    return None


def generate_report():
    """Generate a diagnostic report for all parsers and test files."""
    print("=" * 80)
    print("HANSARD PARSER DIAGNOSTIC REPORT")
    print("=" * 80)
    
    # Get all metric classes
    metric_classes = get_all_metrics()
    print(f"\nLoaded {len(metric_classes)} metrics")
    
    test_files = get_all_test_files()
    print(f"Found {len(test_files)} test files\n")
    
    results = []
    
    for test_file in test_files:
        year = test_file.stem
        parser = get_parser_for_year(year)
        
        report = {
            "year": year,
            "parser": parser.__name__ if parser else None,
            "error": None,
            "metrics": {},
        }
        
        if parser is None:
            report["error"] = "No parser found"
            results.append(report)
            continue
        
        try:
            text = test_file.read_text()
            parsed_result = parser.parse(text)
            
            if not isinstance(parsed_result, list):
                report["error"] = f"parse() returned {type(parsed_result).__name__}, expected list"
                results.append(report)
                continue
            
            if len(parsed_result) == 0:
                results.append(report)
                continue
            
            # Run each metric
            for metric_cls in metric_classes:
                metric = metric_cls()
                try:
                    result = metric.run(parsed_result)
                    report["metrics"][result.name] = result
                except Exception as e:
                    report["metrics"][metric.name] = {"error": str(e)}
                
        except Exception:
            report["error"] = traceback.format_exc()
        
        results.append(report)
    
    return results


# Define which metrics are "counts" (basic stats) vs "issues" (problems to flag)
COUNT_METRICS = [
    "docs",
    "speeches", 
    "questions",
    "answers",
    "total_interjections",
    "t1_speaker",
    "t2_general",
    "t3_office",
    "t4_unrecorded",
]

ISSUE_METRICS = [
    "empty_author",
    "t1_empty_author",
    "t2_empty_author",
    "t3_empty_author",
    "t4_empty_author",
    "doc_no_author",
    "titles_in_content",
    "title_at_speech_start",
    "title_at_ij_start",
    "times_in_content",
    "empty_text",
    "non_office_keywords",
    "bad_interjecting",
    "raw_member_interjecting",
]


def print_report(results):
    """Print the report in a readable format - split into counts and issues."""
    
    # Filter to non-error results
    valid_results = [r for r in results if not r["error"]]
    
    # --- COUNTS SECTION ---
    print("\n" + "=" * 80)
    print("DOCUMENT COUNTS")
    print("=" * 80)
    
    # Calculate column widths dynamically
    col_widths = {"Year": 8, "Parser": 12}
    for name in COUNT_METRICS:
        col_widths[name] = max(len(name), 6)
    
    # Add data widths
    for r in valid_results:
        for name in COUNT_METRICS:
            metric_result = r.get("metrics", {}).get(name)
            if metric_result and hasattr(metric_result, "count"):
                col_widths[name] = max(col_widths[name], len(str(metric_result.count)))
    
    # Build header
    header_parts = []
    for col in ["Year", "Parser"] + COUNT_METRICS:
        width = col_widths[col]
        if col == "Year" or col == "Parser":
            header_parts.append(f"{col:<{width}}")
        else:
            header_parts.append(f"{col:>{width}}")
    header = "  ".join(header_parts)
    print(header)
    print("-" * len(header))
    
    # Data rows
    for r in valid_results:
        row_parts = []
        row_parts.append(f"{r['year']:<{col_widths['Year']}}")
        row_parts.append(f"{r.get('parser', '').replace('parsers.', ''):<{col_widths['Parser']}}")
        for name in COUNT_METRICS:
            metric_result = r.get("metrics", {}).get(name)
            width = col_widths[name]
            if metric_result is None or not hasattr(metric_result, "count"):
                row_parts.append(f"{'-':>{width}}")
            else:
                row_parts.append(f"{metric_result.count:>{width}}")
        print("  ".join(row_parts))
    
    print("-" * len(header))
    
    # Counts summary
    print("\nTOTALS:")
    for name in COUNT_METRICS:
        total = sum(
            r.get("metrics", {}).get(name, MetricResult("", "", "", 0)).count
            for r in valid_results
            if hasattr(r.get("metrics", {}).get(name), "count")
        )
        print(f"  {name}: {total}")
    
    # --- ISSUES SECTION ---
    print("\n" + "=" * 80)
    print("ISSUES (non-zero counts)")
    print("=" * 80)
    
    # Find which issue metrics have any issues
    active_issues = []
    for name in ISSUE_METRICS:
        total = sum(
            r.get("metrics", {}).get(name, MetricResult("", "", "", 0)).count
            for r in valid_results
            if hasattr(r.get("metrics", {}).get(name), "count")
        )
        if total > 0:
            active_issues.append(name)
    
    if not active_issues:
        print("No issues found!")
    else:
        # Calculate column widths for issues
        issue_col_widths = {"Year": 8}
        for name in active_issues:
            issue_col_widths[name] = len(name)
        
        # Add data widths
        for r in valid_results:
            for name in active_issues:
                metric_result = r.get("metrics", {}).get(name)
                if metric_result and hasattr(metric_result, "count"):
                    issue_col_widths[name] = max(issue_col_widths[name], len(str(metric_result.count)))
        
        # Build header
        header_parts = [f"{'Year':<{issue_col_widths['Year']}}"]
        for name in active_issues:
            header_parts.append(f"{name:>{issue_col_widths[name]}}")
        header = "  ".join(header_parts)
        print(header)
        print("-" * len(header))
        
        for r in valid_results:
            has_issue = False
            row_parts = [f"{r['year']:<{issue_col_widths['Year']}}"]
            for name in active_issues:
                metric_result = r.get("metrics", {}).get(name)
                width = issue_col_widths[name]
                if metric_result is None or not hasattr(metric_result, "count"):
                    row_parts.append(f"{'-':>{width}}")
                else:
                    count = metric_result.count
                    row_parts.append(f"{count:>{width}}")
                    if count > 0:
                        has_issue = True
            if has_issue:
                print("  ".join(row_parts))
        
        print("-" * len(header))
        
        # Issue totals
        print("\nISSUE TOTALS:")
        for name in active_issues:
            total = sum(
                r.get("metrics", {}).get(name, MetricResult("", "", "", 0)).count
                for r in valid_results
                if hasattr(r.get("metrics", {}).get(name), "count")
            )
            print(f"  {name}: {total}")
    
    # Errors
    errors = [r for r in results if r["error"]]
    if errors:
        print("\n" + "=" * 80)
        print("ERRORS")
        print("=" * 80)
        for r in errors:
            print(f"{r['year']}: {r['error'][:100]}")


def print_issue_details(results):
    """Print detailed examples of each issue."""
    
    valid_results = [r for r in results if not r["error"]]
    
    print("\n" + "=" * 80)
    print("ISSUE DETAILS")
    print("=" * 80)
    
    for r in valid_results:
        year = r["year"]
        has_printed_year = False
        
        for name in ISSUE_METRICS:
            metric_result = r.get("metrics", {}).get(name)
            if metric_result is None:
                continue
            if not hasattr(metric_result, "count"):
                continue
            if metric_result.count == 0:
                continue
            
            if not has_printed_year:
                print(f"\n--- {year} ---")
                has_printed_year = True
            
            print(f"  {metric_result.name}: {metric_result.count}")
            print(f"    {metric_result.description}")
            if metric_result.examples:
                for ex in metric_result.examples[:3]:
                    print(f"      - {ex}")


if __name__ == "__main__":
    results = generate_report()
    print_report(results)
    print_issue_details(results)
