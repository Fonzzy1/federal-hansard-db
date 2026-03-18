#!/usr/bin/env python3
"""
Hansard Parser Report - Generates a diagnostic report for each parser/test file.

Run with: python3 tests/run_report.py
"""

import sys
import traceback
import json
import datetime
import importlib
from pathlib import Path
import xml.etree.ElementTree as ET

# Directory to save parsed outputs
PARSED_OUTPUT_DIR = Path("/tmp/hansard_parsed")

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
from tests.metrics.base import MetricResult, CountMetric, IssueMetric

TESTS_DIR = Path(__file__).parent / "xml"

# Parser mapping from seed sources
PARSER_BY_MODULE = {
    "parsers.hansard1901": hansard1901,
    "parsers.hansard1981": hansard1981,
    "parsers.hansard1992": hansard1992,
    "parsers.hansard1997": hansard1997,
    "parsers.hansard1998": hansard1998,
    "parsers.hansard2000": hansard2000,
    "parsers.hansard2011": hansard2011,
    "parsers.hansard2012": hansard2012,
    "parsers.hansard2021": hansard2021,
}


def get_all_test_files():
    """Get all XML test files (excluding test.xml and double extensions)."""
    return sorted(f for f in TESTS_DIR.glob("*.xml") if f.stem != "test" and not f.stem.endswith(".xml"))


def get_date_from_xml(file_path):
    """Extract date from XML file."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        date_elem = root.find(".//date")
        if date_elem is not None and date_elem.text:
            return datetime.datetime.strptime(date_elem.text, "%Y-%m-%d").date()
    except Exception:
        pass
    return None


def load_sources_from_seed():
    """Load source date ranges from seed.py."""
    # Read the seed.py file and extract sources
    seed_path = Path(__file__).parent.parent / "scripts" / "seed.py"
    with open(seed_path) as f:
        content = f.read()
    
    # Parse sources from the file
    sources = []
    # Simple regex to extract id, parserModule, from_day, to_day
    import re
    pattern = r'"id":\s*(\d+).*?"parserModule":\s*"([^"]+)".*?"from_day":\s*"([^"]+)".*?"to_day":\s*"([^"]+)"'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        source_id, parser_module, from_day, to_day = match
        from_date = datetime.datetime.strptime(from_day, "%Y-%m-%d").date()
        to_date = datetime.datetime.strptime(to_day, "%Y-%m-%d").date()
        parser = PARSER_BY_MODULE.get(parser_module)
        if parser:
            sources.append({
                "id": int(source_id),
                "from_date": from_date,
                "to_date": to_date,
                "parser": parser,
            })
    
    return sorted(sources, key=lambda x: x["from_date"])


# Load sources once
SOURCES = load_sources_from_seed()


def get_parser_for_file(test_file):
    """Get parser module based on XML file date."""
    # Get date from XML
    file_date = get_date_from_xml(test_file)
    if file_date is None:
        # Fallback: try to use filename as year
        try:
            year_int = int(test_file.stem)
            for source in SOURCES:
                if source["from_date"].year <= year_int <= source["to_date"].year:
                    return source["parser"]
        except ValueError:
            pass
        return None
    
    # Find matching source by date range
    for source in SOURCES:
        if source["from_date"] <= file_date <= source["to_date"]:
            return source["parser"]
    
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
        parser = get_parser_for_file(test_file)
        
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
            
            # Save parsed result to file
            PARSED_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_file = PARSED_OUTPUT_DIR / f"{year}.json"
            with open(output_file, "w") as f:
                json.dump(parsed_result, f, indent=2, ensure_ascii=False)
            
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



all_metrics = get_all_metrics()
COUNT_METRICS = [m().name for m in all_metrics if issubclass(m, CountMetric)]
ISSUE_METRICS = [m().name for m in all_metrics if issubclass(m, IssueMetric)]


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
