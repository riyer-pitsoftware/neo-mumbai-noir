#!/usr/bin/env python3
"""
Validate character_data.json schema and required fields.
"""
import json
import sys
from pathlib import Path

REQUIRED_FIELDS = ["name", "age", "ethnicity", "gender"]
OPTIONAL_FIELDS = ["facial_features", "clothing", "key_scenes", "emotions"]


def verify_character_data(filepath="characters/character_data.json"):
    """Validate character_data.json and return results dict."""
    results = {"passed": True, "errors": [], "warnings": [], "characters": 0}

    path = Path(filepath)
    if not path.exists():
        results["passed"] = False
        results["errors"].append(f"File not found: {filepath}")
        return results

    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        results["passed"] = False
        results["errors"].append(f"Invalid JSON: {e}")
        return results

    if "characters" not in data:
        results["passed"] = False
        results["errors"].append("Missing top-level 'characters' key")
        return results

    if not isinstance(data["characters"], list):
        results["passed"] = False
        results["errors"].append("'characters' must be a list")
        return results

    if len(data["characters"]) == 0:
        results["passed"] = False
        results["errors"].append("No characters found")
        return results

    results["characters"] = len(data["characters"])

    for i, char in enumerate(data["characters"]):
        char_name = char.get("name", f"Character #{i+1}")

        for field in REQUIRED_FIELDS:
            if field not in char or not char[field]:
                results["passed"] = False
                results["errors"].append(f"{char_name}: missing required field '{field}'")

        for field in OPTIONAL_FIELDS:
            if field not in char:
                results["warnings"].append(f"{char_name}: missing optional field '{field}'")
            elif isinstance(char.get(field), list) and len(char[field]) == 0:
                results["warnings"].append(f"{char_name}: '{field}' is empty")

    return results


def print_results(results):
    """Print verification results."""
    status = "PASS" if results["passed"] else "FAIL"
    print(f"\nVerification: {status}")
    print(f"Characters found: {results['characters']}")

    if results["errors"]:
        print(f"\nErrors ({len(results['errors'])}):")
        for err in results["errors"]:
            print(f"  - {err}")

    if results["warnings"]:
        print(f"\nWarnings ({len(results['warnings'])}):")
        for warn in results["warnings"]:
            print(f"  - {warn}")

    return results["passed"]


if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "characters/character_data.json"
    results = verify_character_data(filepath)
    passed = print_results(results)
    sys.exit(0 if passed else 1)
