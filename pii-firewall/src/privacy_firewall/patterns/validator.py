"""Pattern validation utilities for ensuring regex correctness."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationIssue:
    """Issue found during pattern validation."""
    
    severity: str  # "error", "warning", "info"
    message: str
    pattern_name: str
    entity_type: str


def validate_pattern(pattern: Any) -> list[ValidationIssue]:
    """Validate EntityPattern and return list of issues.
    
    Checks for:
    - Regex compilation errors
    - Catastrophic backtracking risks
    - Empty match potential
    - Confidence score range
    - Context word validity
    
    Args:
        pattern: EntityPattern to validate
    
    Returns:
        List of ValidationIssue (empty if valid)
    """
    issues = []
    
    # Check 1: Regex compilation
    try:
        pattern.pattern.search("test")
    except Exception as e:
        issues.append(ValidationIssue(
            severity="error",
            message=f"Regex compilation failed: {e}",
            pattern_name=f"{pattern.entity_type}_{pattern.locale}",
            entity_type=pattern.entity_type,
        ))
        # Can't continue validation if regex doesn't compile
        return issues
    
    # Check 2: Confidence score range
    if not 0.0 <= pattern.confidence <= 1.0:
        issues.append(ValidationIssue(
            severity="error",
            message=f"Confidence score {pattern.confidence} out of range [0.0, 1.0]",
            pattern_name=f"{pattern.entity_type}_{pattern.locale}",
            entity_type=pattern.entity_type,
        ))
    
    # Check 3: Catastrophic backtracking (basic heuristics)
    regex_str = pattern.pattern.pattern
    
    # Nested quantifiers like (.*)*
    if re.search(r'\([^)]*\*[^)]*\)\*', regex_str) or re.search(r'\([^)]*\+[^)]*\)\+', regex_str):
        issues.append(ValidationIssue(
            severity="warning",
            message="Nested quantifiers detected - risk of catastrophic backtracking",
            pattern_name=f"{pattern.entity_type}_{pattern.locale}",
            entity_type=pattern.entity_type,
        ))
    
    # Overlapping quantifiers like .*.*
    if re.search(r'\.\*\s*\.\*', regex_str):
        issues.append(ValidationIssue(
            severity="warning",
            message="Overlapping .* quantifiers - may cause performance issues",
            pattern_name=f"{pattern.entity_type}_{pattern.locale}",
            entity_type=pattern.entity_type,
        ))
    
    # Check 4: Empty match potential
    try:
        if pattern.pattern.match(""):
            issues.append(ValidationIssue(
                severity="warning",
                message="Pattern can match empty string - may cause false positives",
                pattern_name=f"{pattern.entity_type}_{pattern.locale}",
                entity_type=pattern.entity_type,
            ))
    except Exception:
        pass
    
    # Check 5: Overly broad patterns
    if regex_str in (".*", ".+", ".*?", ".+?"):
        issues.append(ValidationIssue(
            severity="error",
            message="Pattern is too broad - will match almost anything",
            pattern_name=f"{pattern.entity_type}_{pattern.locale}",
            entity_type=pattern.entity_type,
        ))
    
    # Check 6: Context words validity
    if pattern.context_words:
        for word in pattern.context_words:
            if not word or not word.strip():
                issues.append(ValidationIssue(
                    severity="warning",
                    message=f"Empty context word found",
                    pattern_name=f"{pattern.entity_type}_{pattern.locale}",
                    entity_type=pattern.entity_type,
                ))
    
    return issues


def validate_catalog(catalog: Any) -> dict[str, list[ValidationIssue]]:
    """Validate entire pattern catalog.
    
    Args:
        catalog: PatternCatalog to validate
    
    Returns:
        Dict mapping locale to list of issues found in that locale
    """
    results = {}
    
    for locale in catalog._patterns.keys():
        locale_issues = []
        patterns = catalog.get_all_patterns_for_locale(locale)
        
        for pattern in patterns:
            issues = validate_pattern(pattern)
            locale_issues.extend(issues)
        
        if locale_issues:
            results[locale] = locale_issues
    
    return results


def print_validation_report(results: dict[str, list[ValidationIssue]]) -> None:
    """Print human-readable validation report.
    
    Args:
        results: Results from validate_catalog
    """
    total_errors = sum(1 for issues in results.values() for i in issues if i.severity == "error")
    total_warnings = sum(1 for issues in results.values() for i in issues if i.severity == "warning")
    
    print("=" * 80)
    print("PATTERN CATALOG VALIDATION REPORT")
    print("=" * 80)
    
    if not results:
        print("✅ All patterns valid - no issues found!")
        return
    
    print(f"\n⚠️  Found {total_errors} errors and {total_warnings} warnings\n")
    
    for locale, issues in sorted(results.items()):
        print(f"\n📍 Locale: {locale}")
        print("-" * 80)
        
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        
        if errors:
            print(f"\n  🔴 ERRORS ({len(errors)}):")
            for issue in errors:
                print(f"    - {issue.pattern_name}: {issue.message}")
        
        if warnings:
            print(f"\n  🟡 WARNINGS ({len(warnings)}):")
            for issue in warnings:
                print(f"    - {issue.pattern_name}: {issue.message}")
    
    print("\n" + "=" * 80)
    print(f"Summary: {total_errors} errors, {total_warnings} warnings")
    print("=" * 80)


if __name__ == "__main__":
    """Run validation on default catalog."""
    from privacy_firewall.patterns import create_default_catalog
    
    print("Loading default pattern catalog...")
    catalog = create_default_catalog()
    
    print(f"Validating {len(catalog._patterns)} locale groups...\n")
    
    results = validate_catalog(catalog)
    print_validation_report(results)
