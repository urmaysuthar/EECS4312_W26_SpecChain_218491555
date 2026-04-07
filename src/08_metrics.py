from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


# this script computes metrics for the manual, auto, and hybrid pipelines
# it can generate one pipeline at a time or all of them together
# later it also builds metrics_summary.json when all pipeline metric files exist

REPO_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = REPO_ROOT / "data"
PERSONAS_DIR = REPO_ROOT / "personas"
SPEC_DIR = REPO_ROOT / "spec"
TESTS_DIR = REPO_ROOT / "tests"
METRICS_DIR = REPO_ROOT / "metrics"

CLEAN_REVIEWS_PATH = DATA_DIR / "reviews_clean.jsonl"
SUMMARY_PATH = METRICS_DIR / "metrics_summary.json"

PIPELINE_FILES = {
    "manual": {
        "groups": DATA_DIR / "review_groups_manual.json",
        "personas": PERSONAS_DIR / "personas_manual.json",
        "spec": SPEC_DIR / "spec_manual.md",
        "tests": TESTS_DIR / "tests_manual.json",
        "metrics": METRICS_DIR / "metrics_manual.json",
    },
    "auto": {
        "groups": DATA_DIR / "review_groups_auto.json",
        "personas": PERSONAS_DIR / "personas_auto.json",
        "spec": SPEC_DIR / "spec_auto.md",
        "tests": TESTS_DIR / "tests_auto.json",
        "metrics": METRICS_DIR / "metrics_auto.json",
    },
    "hybrid": {
        "groups": DATA_DIR / "review_groups_hybrid.json",
        "personas": PERSONAS_DIR / "personas_hybrid.json",
        "spec": SPEC_DIR / "spec_hybrid.md",
        "tests": TESTS_DIR / "tests_hybrid.json",
        "metrics": METRICS_DIR / "metrics_hybrid.json",
    },
}

AMBIGUOUS_TERMS = [
    "easy",
    "easier",
    "better",
    "best",
    "fast",
    "faster",
    "quick",
    "quickly",
    "user-friendly",
    "user friendly",
    "intuitive",
    "seamless",
    "helpful",
    "effective",
    "effectively",
    "useful",
    "clear",
    "clearly",
    "transparent",
    "regular",
    "improve",
    "improves",
    "improved",
    "readable",
    "simple",
    "smooth",
    "meaningful",
    "personalized",
    "relevant",
    "appropriate",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute SpecChain pipeline metrics.")
    parser.add_argument(
        "--pipeline",
        choices=["manual", "auto", "hybrid", "all"],
        default="auto",
        help="Which pipeline metrics to compute."
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def parse_spec_markdown(text: str) -> List[Dict[str, str]]:
    # this extracts requirement blocks from the markdown spec file
    pattern = re.compile(
        r"# Requirement ID:\s*(?P<rid>[^\n]+)\n\s*"
        r"- Description:\s*\[(?P<desc>.*?)\]\n\s*"
        r"- Source Persona:\s*\[(?P<persona>.*?)\]\n\s*"
        r"- Traceability:\s*\[(?P<trace>.*?)\]\n\s*"
        r"- Acceptance Criteria:\s*\[(?P<ac>.*?)\]",
        re.DOTALL
    )

    requirements: List[Dict[str, str]] = []

    for match in pattern.finditer(text):
        trace_text = match.group("trace").strip()
        group_match = re.search(r"review group\s+([A-Z0-9_]+)", trace_text, re.IGNORECASE)

        requirements.append({
            "requirement_id": match.group("rid").strip(),
            "description": match.group("desc").strip(),
            "source_persona": match.group("persona").strip(),
            "traceability": trace_text,
            "source_group": group_match.group(1).strip() if group_match else "",
            "acceptance_criteria": match.group("ac").strip(),
        })

    return requirements


def load_spec_requirements(path: Path) -> List[Dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    return parse_spec_markdown(text)


def contains_ambiguous_language(text: str) -> bool:
    lowered = text.lower()
    for term in AMBIGUOUS_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lowered):
            return True
    return False


def compute_ambiguity_ratio(requirements: List[Dict[str, str]]) -> float:
    if not requirements:
        return 0.0

    ambiguous_count = 0
    for req in requirements:
        description = req["description"]
        acceptance = req["acceptance_criteria"]
        if contains_ambiguous_language(description) or contains_ambiguous_language(acceptance):
            ambiguous_count += 1

    return round(ambiguous_count / len(requirements), 4)


def compute_traceability_links(
    groups_data: Dict[str, Any],
    personas_data: Dict[str, Any],
    requirements: List[Dict[str, str]],
    tests_data: Dict[str, Any]
) -> Tuple[int, Dict[str, int]]:
    # this counts explicit links between artifacts
    review_group_to_review_links = 0
    for group in groups_data.get("groups", []):
        review_group_to_review_links += len(group.get("review_ids", []))

    persona_to_group_links = 0
    persona_to_evidence_review_links = 0
    for persona in personas_data.get("personas", []):
        if persona.get("derived_from_group"):
            persona_to_group_links += 1
        persona_to_evidence_review_links += len(persona.get("evidence_reviews", []))

    requirement_to_persona_links = 0
    requirement_to_group_links = 0
    for req in requirements:
        if req.get("source_persona"):
            requirement_to_persona_links += 1
        if req.get("source_group"):
            requirement_to_group_links += 1

    test_to_requirement_links = 0
    for test in tests_data.get("tests", []):
        if test.get("requirement_id"):
            test_to_requirement_links += 1

    breakdown = {
        "review_group_to_review_links": review_group_to_review_links,
        "persona_to_group_links": persona_to_group_links,
        "persona_to_evidence_review_links": persona_to_evidence_review_links,
        "requirement_to_persona_links": requirement_to_persona_links,
        "requirement_to_group_links": requirement_to_group_links,
        "test_to_requirement_links": test_to_requirement_links,
    }

    total_links = sum(breakdown.values())
    return total_links, breakdown


def compute_review_coverage_ratio(groups_data: Dict[str, Any], dataset_size: int) -> float:
    if dataset_size == 0:
        return 0.0

    unique_review_ids = set()
    for group in groups_data.get("groups", []):
        for review_id in group.get("review_ids", []):
            unique_review_ids.add(review_id)

    return round(len(unique_review_ids) / dataset_size, 4)


def compute_traceability_ratio(requirements: List[Dict[str, str]]) -> float:
    if not requirements:
        return 0.0

    traceable = 0
    for req in requirements:
        if req.get("source_persona"):
            traceable += 1

    return round(traceable / len(requirements), 4)


def compute_testability_rate(requirements: List[Dict[str, str]], tests_data: Dict[str, Any]) -> float:
    if not requirements:
        return 0.0

    requirement_ids = {req["requirement_id"] for req in requirements}
    tested_ids = {
        test.get("requirement_id")
        for test in tests_data.get("tests", [])
        if test.get("requirement_id")
    }

    covered = 0
    for rid in requirement_ids:
        if rid in tested_ids:
            covered += 1

    return round(covered / len(requirement_ids), 4)


def compute_pipeline_metrics(pipeline: str, cleaned_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    files = PIPELINE_FILES[pipeline]

    groups_data = load_json(files["groups"])
    personas_data = load_json(files["personas"])
    requirements = load_spec_requirements(files["spec"])
    tests_data = load_json(files["tests"])

    dataset_size = len(cleaned_reviews)
    persona_count = len(personas_data.get("personas", []))
    requirements_count = len(requirements)
    tests_count = len(tests_data.get("tests", []))

    traceability_links, traceability_breakdown = compute_traceability_links(
        groups_data=groups_data,
        personas_data=personas_data,
        requirements=requirements,
        tests_data=tests_data
    )

    review_coverage_ratio = compute_review_coverage_ratio(groups_data, dataset_size)
    traceability_ratio = compute_traceability_ratio(requirements)
    testability_rate = compute_testability_rate(requirements, tests_data)
    ambiguity_ratio = compute_ambiguity_ratio(requirements)

    metrics = {
        "pipeline": pipeline,
        "dataset_size": dataset_size,
        "persona_count": persona_count,
        "requirements_count": requirements_count,
        "tests_count": tests_count,
        "traceability_links": traceability_links,
        "review_coverage_ratio": review_coverage_ratio,
        "traceability_ratio": traceability_ratio,
        "testability_rate": testability_rate,
        "ambiguity_ratio": ambiguity_ratio,
        "traceability_breakdown": traceability_breakdown,
    }

    return metrics


def build_metrics_summary() -> Dict[str, Any] | None:
    # this only works when all 3 pipeline metric files exist
    # and also already contain the full set of expected metric fields
    required_paths = [PIPELINE_FILES[p]["metrics"] for p in ["manual", "auto", "hybrid"]]
    if not all(path.exists() for path in required_paths):
        return None

    manual_metrics = load_json(PIPELINE_FILES["manual"]["metrics"])
    auto_metrics = load_json(PIPELINE_FILES["auto"]["metrics"])
    hybrid_metrics = load_json(PIPELINE_FILES["hybrid"]["metrics"])

    required_keys = [
        "dataset_size",
        "persona_count",
        "requirements_count",
        "tests_count",
        "traceability_links",
        "review_coverage_ratio",
        "traceability_ratio",
        "testability_rate",
        "ambiguity_ratio",
    ]

    for metrics_obj in [manual_metrics, auto_metrics, hybrid_metrics]:
        if not all(key in metrics_obj for key in required_keys):
            return None

    summary = {
        "manual": manual_metrics,
        "auto": auto_metrics,
        "hybrid": hybrid_metrics,
        "comparison_table": {
            "dataset_size": {
                "manual": manual_metrics["dataset_size"],
                "auto": auto_metrics["dataset_size"],
                "hybrid": hybrid_metrics["dataset_size"],
            },
            "persona_count": {
                "manual": manual_metrics["persona_count"],
                "auto": auto_metrics["persona_count"],
                "hybrid": hybrid_metrics["persona_count"],
            },
            "requirements_count": {
                "manual": manual_metrics["requirements_count"],
                "auto": auto_metrics["requirements_count"],
                "hybrid": hybrid_metrics["requirements_count"],
            },
            "tests_count": {
                "manual": manual_metrics["tests_count"],
                "auto": auto_metrics["tests_count"],
                "hybrid": hybrid_metrics["tests_count"],
            },
            "traceability_links": {
                "manual": manual_metrics["traceability_links"],
                "auto": auto_metrics["traceability_links"],
                "hybrid": hybrid_metrics["traceability_links"],
            },
            "review_coverage_ratio": {
                "manual": manual_metrics["review_coverage_ratio"],
                "auto": auto_metrics["review_coverage_ratio"],
                "hybrid": hybrid_metrics["review_coverage_ratio"],
            },
            "traceability_ratio": {
                "manual": manual_metrics["traceability_ratio"],
                "auto": auto_metrics["traceability_ratio"],
                "hybrid": hybrid_metrics["traceability_ratio"],
            },
            "testability_rate": {
                "manual": manual_metrics["testability_rate"],
                "auto": auto_metrics["testability_rate"],
                "hybrid": hybrid_metrics["testability_rate"],
            },
            "ambiguity_ratio": {
                "manual": manual_metrics["ambiguity_ratio"],
                "auto": auto_metrics["ambiguity_ratio"],
                "hybrid": hybrid_metrics["ambiguity_ratio"],
            },
        }
    }

    return summary


def main() -> None:
    args = parse_args()

    cleaned_reviews = load_jsonl(CLEAN_REVIEWS_PATH)

    pipelines = ["manual", "auto", "hybrid"] if args.pipeline == "all" else [args.pipeline]

    for pipeline in pipelines:
        metrics = compute_pipeline_metrics(pipeline, cleaned_reviews)
        metrics_path = PIPELINE_FILES[pipeline]["metrics"]
        save_json(metrics, metrics_path)
        print(f"computed metrics for {pipeline}")
        print(f"saved metrics to {metrics_path}")

    # only try to build the summary after all pipelines are really ready
    if args.pipeline == "all":
        summary = build_metrics_summary()
        if summary is not None:
            save_json(summary, SUMMARY_PATH)
            print(f"saved metrics summary to {SUMMARY_PATH}")
        else:
            print("summary not created yet because one or more pipeline metric files are still incomplete")