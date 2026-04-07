from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from groq import Groq

# reads the automated spec file and generates automated validation tests


REPO_ROOT = Path(__file__).resolve().parents[1]

SPEC_PATH = REPO_ROOT / "spec" / "spec_auto.md"
TESTS_PATH = REPO_ROOT / "tests" / "tests_auto.json"
PROMPT_PATH = REPO_ROOT / "prompts" / "prompt_auto.json"

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
TEMPERATURE = 0.2
TESTS_PER_REQUIREMENT = 2


def load_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_json(text: str) -> Any:
    # sometimes the model adds code fences or extra text
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_]*\n?", "", text)
        text = re.sub(r"\n```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start_obj = text.find("{")
    end_obj = text.rfind("}")
    if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
        return json.loads(text[start_obj:end_obj + 1])

    start_arr = text.find("[")
    end_arr = text.rfind("]")
    if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
        return json.loads(text[start_arr:end_arr + 1])

    raise ValueError("could not parse json from model response")


def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set in your environment.")
    return Groq(api_key=api_key)


def call_groq_json(client: Groq, system_prompt: str, user_prompt: str) -> Any:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content
    return extract_json(content)


def parse_spec_markdown(text: str) -> List[Dict[str, str]]:
    # this reads the markdown spec and pulls out the requirement fields
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
            "acceptance_criteria": match.group("ac").strip()
        })

    return requirements


def build_test_prompt(requirement: Dict[str, str]) -> Tuple[str, str]:
    # this prompt asks for exactly 2 tests for one requirement
    system_prompt = (
        "You are helping with software requirements engineering test design. "
        "Generate exactly 2 validation test scenarios for the single requirement you are given. "
        "Each test must be concrete and clearly linked to the requirement. "
        "Each test must contain a short scenario name, a list of execution steps, and an expected result. "
        "Return strict JSON only with this shape: "
        "{\"tests\": ["
        "{\"scenario\": \"...\", "
        "\"steps\": [\"...\", \"...\"], "
        "\"expected_result\": \"...\"}"
        "]}"
    )

    user_prompt = (
        f"Requirement ID: {requirement['requirement_id']}\n"
        f"Description: {requirement['description']}\n"
        f"Source Persona: {requirement['source_persona']}\n"
        f"Source Group: {requirement['source_group']}\n"
        f"Acceptance Criteria: {requirement['acceptance_criteria']}\n\n"
        "Generate exactly 2 test scenarios for this requirement."
    )

    return system_prompt, user_prompt


def build_retry_prompt(requirement: Dict[str, str], rejected_tests: List[Dict[str, Any]], reasons: List[str]) -> Tuple[str, str]:
    # this retry prompt is stricter and points out what was weak before
    system_prompt = (
        "You are rewriting weak software validation tests into stronger tests. "
        "Generate exactly 2 validation test scenarios only. "
        "Each test must be concrete, readable, and clearly executable. "
        "Each test must include a scenario, steps list, and expected result. "
        "Return strict JSON only with this shape: "
        "{\"tests\": ["
        "{\"scenario\": \"...\", "
        "\"steps\": [\"...\", \"...\"], "
        "\"expected_result\": \"...\"}"
        "]}"
    )

    lines = [
        f"Requirement ID: {requirement['requirement_id']}",
        f"Description: {requirement['description']}",
        f"Acceptance Criteria: {requirement['acceptance_criteria']}"
    ]

    if rejected_tests:
        lines.append("Earlier weak tests:")
        for item in rejected_tests:
            lines.append(f"- {item.get('scenario', '')}")

    if reasons:
        lines.append("Problems to avoid:")
        for reason in reasons:
            lines.append(f"- {reason}")

    user_prompt = (
        "Rewrite the tests so they are stronger and more concrete.\n"
        "Generate exactly 2 better validation tests now.\n\n"
        + "\n".join(lines)
    )

    return system_prompt, user_prompt


def validate_tests(raw_tests: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []

    if len(raw_tests) != TESTS_PER_REQUIREMENT:
        reasons.append("the response did not contain exactly 2 tests")
        return False, reasons

    scenarios_seen = set()

    for test in raw_tests:
        scenario = str(test.get("scenario", "")).strip()
        steps = test.get("steps", [])
        expected = str(test.get("expected_result", "")).strip()

        if not scenario:
            reasons.append("a test is missing a scenario name")
        else:
            key = scenario.lower()
            if key in scenarios_seen:
                reasons.append("duplicate scenario names were generated")
            scenarios_seen.add(key)

        if not isinstance(steps, list) or len(steps) < 3:
            reasons.append("a test does not have at least 3 steps")

        if not expected:
            reasons.append("a test is missing an expected result")

    return len(reasons) == 0, reasons


def clean_tests(raw_tests: List[Dict[str, Any]], requirement_id: str, start_index: int) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []

    for offset, test in enumerate(raw_tests, start=0):
        cleaned.append({
            "test_id": f"T_auto_{start_index + offset}",
            "requirement_id": requirement_id,
            "scenario": str(test.get("scenario", "")).strip(),
            "steps": [str(step).strip() for step in test.get("steps", []) if str(step).strip()],
            "expected_result": str(test.get("expected_result", "")).strip()
        })

    return cleaned


def fallback_tests_for_requirement(requirement: Dict[str, str], start_index: int) -> List[Dict[str, Any]]:
    # this fallback is here so the script can still finish with usable tests
    rid = requirement["requirement_id"]
    desc = requirement["description"]

    fallback_raw = [
        {
            "scenario": f"Primary validation for {rid}",
            "steps": [
                "Open the relevant feature or screen for the requirement",
                "Perform the main user action described by the requirement",
                "Observe the system response after the action is completed"
            ],
            "expected_result": f"The system behaves according to requirement {rid} and matches the required outcome."
        },
        {
            "scenario": f"Stored result validation for {rid}",
            "steps": [
                "Open the relevant feature or screen for the requirement",
                "Complete the action described by the requirement",
                "Reopen the related screen or data view to verify the saved result"
            ],
            "expected_result": f"The result of requirement {rid} is saved or displayed correctly after the action is completed."
        }
    ]

    return clean_tests(fallback_raw, rid, start_index)


def generate_tests_for_requirement(
    client: Groq,
    requirement: Dict[str, str],
    start_index: int
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    # first try
    system_prompt, user_prompt = build_test_prompt(requirement)
    first_result = call_groq_json(client, system_prompt, user_prompt)
    first_tests = first_result.get("tests", [])
    first_ok, first_reasons = validate_tests(first_tests)

    if first_ok:
        return clean_tests(first_tests, requirement["requirement_id"], start_index), {
            "requirement_id": requirement["requirement_id"],
            "first_attempt_system_prompt": system_prompt,
            "first_attempt_user_prompt": user_prompt,
            "first_attempt_raw_response": first_result,
            "retry_attempt_system_prompt": "",
            "retry_attempt_user_prompt": "",
            "retry_attempt_raw_response": {},
            "used_fallback": False
        }

    # retry if the first output was weak
    retry_system_prompt, retry_user_prompt = build_retry_prompt(
        requirement=requirement,
        rejected_tests=first_tests if isinstance(first_tests, list) else [],
        reasons=first_reasons
    )
    retry_result = call_groq_json(client, retry_system_prompt, retry_user_prompt)
    retry_tests = retry_result.get("tests", [])
    retry_ok, retry_reasons = validate_tests(retry_tests)

    if retry_ok:
        return clean_tests(retry_tests, requirement["requirement_id"], start_index), {
            "requirement_id": requirement["requirement_id"],
            "first_attempt_system_prompt": system_prompt,
            "first_attempt_user_prompt": user_prompt,
            "first_attempt_raw_response": first_result,
            "retry_attempt_system_prompt": retry_system_prompt,
            "retry_attempt_user_prompt": retry_user_prompt,
            "retry_attempt_raw_response": retry_result,
            "used_fallback": False
        }

    # fallback if the model still gives weak tests
    return fallback_tests_for_requirement(requirement, start_index), {
        "requirement_id": requirement["requirement_id"],
        "first_attempt_system_prompt": system_prompt,
        "first_attempt_user_prompt": user_prompt,
        "first_attempt_raw_response": first_result,
        "retry_attempt_system_prompt": retry_system_prompt,
        "retry_attempt_user_prompt": retry_user_prompt,
        "retry_attempt_raw_response": retry_result,
        "used_fallback": True,
        "retry_failure_reasons": retry_reasons
    }


def update_prompt_file(test_prompt_record: Dict[str, Any]) -> None:
    existing: Dict[str, Any] = {}

    if PROMPT_PATH.exists():
        try:
            existing = load_json(PROMPT_PATH)
        except Exception:
            existing = {}

    existing["test_generation"] = test_prompt_record
    save_json(existing, PROMPT_PATH)


def main() -> None:
    spec_text = load_text(SPEC_PATH)
    requirements = parse_spec_markdown(spec_text)

    if not requirements:
        raise ValueError("no requirements were found in spec_auto.md")

    client = get_client()

    all_tests: List[Dict[str, Any]] = []
    prompt_records: List[Dict[str, Any]] = []

    next_test_number = 1

    for requirement in requirements:
        tests_for_requirement, prompt_record = generate_tests_for_requirement(
            client=client,
            requirement=requirement,
            start_index=next_test_number
        )
        all_tests.extend(tests_for_requirement)
        prompt_records.append(prompt_record)
        next_test_number += TESTS_PER_REQUIREMENT

    output = {"tests": all_tests}
    save_json(output, TESTS_PATH)

    test_prompt_record = {
        "model": MODEL_NAME,
        "tests_per_requirement": TESTS_PER_REQUIREMENT,
        "generation_records": prompt_records
    }
    update_prompt_file(test_prompt_record)

    print("automated test generation finished")
    print(f"generated {len(all_tests)} tests from {len(requirements)} requirements")
    print(f"saved automated tests to {TESTS_PATH}")
    print(f"updated prompts in {PROMPT_PATH}")


if __name__ == "__main__":
    main()