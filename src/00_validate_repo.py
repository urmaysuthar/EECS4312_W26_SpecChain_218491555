from __future__ import annotations

import sys
from pathlib import Path


# this script checks whether the final repo structure is complete
# it looks for the folders and files that should exist by the end of the project

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = [
    "data",
    "metrics",
    "personas",
    "prompts",
    "reflection",
    "spec",
    "src",
    "tests",
]

REQUIRED_FILES = [
    "README.md",
    "data/reviews_raw.jsonl",
    "data/reviews_clean.jsonl",
    "data/dataset_metadata.json",
    "data/review_groups_manual.json",
    "data/review_groups_auto.json",
    "data/review_groups_hybrid.json",
    "personas/personas_manual.json",
    "personas/personas_auto.json",
    "personas/personas_hybrid.json",
    "spec/spec_manual.md",
    "spec/spec_auto.md",
    "spec/spec_hybrid.md",
    "tests/tests_manual.json",
    "tests/tests_auto.json",
    "tests/tests_hybrid.json",
    "metrics/metrics_manual.json",
    "metrics/metrics_auto.json",
    "metrics/metrics_hybrid.json",
    "metrics/metrics_summary.json",
    "reflection/reflection.md",
    "prompts/prompt_auto.json",
    "src/00_validate_repo.py",
    "src/01_collect_or_import.py",
    "src/02_clean.py",
    "src/03_manual_coding_template.py",
    "src/04_personas_manual.py",
    "src/05_personas_auto.py",
    "src/06_spec_generate.py",
    "src/07_tests_generate.py",
    "src/08_metrics.py",
    "src/run_all.py",
]


def main() -> None:
    print("Checking repository structure...")

    missing_items: list[str] = []

    for folder in REQUIRED_DIRS:
        folder_path = REPO_ROOT / folder
        if folder_path.is_dir():
            print(f"{folder}/ found")
        else:
            print(f"{folder}/ MISSING")
            missing_items.append(f"{folder}/")

    for file_rel in REQUIRED_FILES:
        file_path = REPO_ROOT / file_rel
        if file_path.is_file():
            print(f"{file_rel} found")
        else:
            print(f"{file_rel} MISSING")
            missing_items.append(file_rel)

    print("Repository validation complete")

    if missing_items:
        print(f"missing items: {len(missing_items)}")
        sys.exit(1)

    print("repository structure is complete")
    sys.exit(0)


if __name__ == "__main__":
    main()