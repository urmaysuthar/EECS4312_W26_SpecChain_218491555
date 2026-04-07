from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


# this script runs the automated pipeline from start to finish
# it does not try to automate the manual or hybrid steps
# it only runs the parts that are supposed to be generated programmatically

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the automated SpecChain pipeline.")
    parser.add_argument("--count", type=int, default=5000, help="number of raw reviews to collect")
    parser.add_argument("--lang", type=str, default="en", help="review language")
    parser.add_argument("--country", type=str, default="ca", help="country code for review collection")
    parser.add_argument(
        "--sort",
        type=str,
        default="newest",
        choices=["newest", "most_relevant"],
        help="review sorting mode for collection"
    )
    return parser.parse_args()


def run_step(step_name: str, command: list[str]) -> None:
    print(f"\n--- {step_name} ---")
    print("running:", " ".join(command))
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> None:
    args = parse_args()

    # groq is needed for the automated llm steps
    if not os.getenv("GROQ_API_KEY"):
        raise EnvironmentError("GROQ_API_KEY is not set. Please set it before running the automated pipeline.")

    python_exe = sys.executable

    # step 1
    # collect raw reviews and write:
    # data/reviews_raw.jsonl
    # data/dataset_metadata.json
    run_step(
        "step 1 - collect raw reviews",
        [
            python_exe,
            str(SRC_DIR / "01_collect_or_import.py"),
            "--count", str(args.count),
            "--lang", args.lang,
            "--country", args.country,
            "--sort", args.sort,
        ],
    )

    # step 2
    # clean the raw dataset and write:
    # data/reviews_clean.jsonl
    # data/dataset_metadata.json
    run_step(
        "step 2 - clean reviews",
        [
            python_exe,
            str(SRC_DIR / "02_clean.py"),
        ],
    )

    # step 3
    # generate automated review groups and personas and write:
    # data/review_groups_auto.json
    # personas/personas_auto.json
    # prompts/prompt_auto.json
    run_step(
        "step 3 - generate automated groups and personas",
        [
            python_exe,
            str(SRC_DIR / "05_personas_auto.py"),
        ],
    )

    # step 4
    # generate automated requirements and write:
    # spec/spec_auto.md
    # prompts/prompt_auto.json
    run_step(
        "step 4 - generate automated specification",
        [
            python_exe,
            str(SRC_DIR / "06_spec_generate.py"),
        ],
    )

    # step 5
    # generate automated tests and write:
    # tests/tests_auto.json
    # prompts/prompt_auto.json
    run_step(
        "step 5 - generate automated tests",
        [
            python_exe,
            str(SRC_DIR / "07_tests_generate.py"),
        ],
    )

    # step 6
    # compute automated metrics and write:
    # metrics/metrics_auto.json
    run_step(
        "step 6 - compute automated metrics",
        [
            python_exe,
            str(SRC_DIR / "08_metrics.py"),
            "--pipeline",
            "auto",
        ],
    )

    print("\nautomated pipeline finished successfully")
    print("files produced in the automated pipeline include:")
    print("- data/reviews_raw.jsonl")
    print("- data/reviews_clean.jsonl")
    print("- data/dataset_metadata.json")
    print("- data/review_groups_auto.json")
    print("- personas/personas_auto.json")
    print("- spec/spec_auto.md")
    print("- tests/tests_auto.json")
    print("- metrics/metrics_auto.json")
    print("- prompts/prompt_auto.json")


if __name__ == "__main__":
    main()