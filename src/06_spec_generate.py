from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from groq import Groq


# this script is for task 4.3
# it reads the automated personas and groups
# then it generates a stronger automated spec with 2 requirements per persona
# i made it more defensive because llm output can be vague or inconsistent sometimes

REPO_ROOT = Path(__file__).resolve().parents[1]

PERSONAS_PATH = REPO_ROOT / "personas" / "personas_auto.json"
GROUPS_PATH = REPO_ROOT / "data" / "review_groups_auto.json"
SPEC_PATH = REPO_ROOT / "spec" / "spec_auto.md"
PROMPT_PATH = REPO_ROOT / "prompts" / "prompt_auto.json"

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
TEMPERATURE = 0.2
REQUIREMENTS_PER_PERSONA = 2

VAGUE_TERMS = [
    "easy",
    "easier",
    "better",
    "best",
    "seamless",
    "user-friendly",
    "user friendly",
    "intuitive",
    "fast",
    "faster",
    "quick",
    "quickly",
    "helpful",
    "effective",
    "effectively",
    "regular",
    "improve",
    "improves",
    "improved",
    "personalized",
    "transparent",
    "clear",
    "useful"
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text)


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


def contains_vague_language(text: str) -> bool:
    lowered = text.lower()
    for term in VAGUE_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lowered):
            return True
    return False


def is_valid_acceptance_criteria(text: str) -> bool:
    lowered = text.lower()
    return "given" in lowered and "when" in lowered and "then" in lowered


def normalize_description(text: str) -> str:
    text = str(text).strip()
    if not text.lower().startswith("the system shall"):
        text = "The system shall " + text.lstrip()
    return text


def build_group_lookup(groups_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {group["group_id"]: group for group in groups_data["groups"]}


def build_persona_prompt(persona: Dict[str, Any], group: Dict[str, Any]) -> Tuple[str, str]:
    # this first prompt asks for 2 strong requirements for 1 persona only
    system_prompt = (
        "You are helping with software requirements engineering for a mental health app. "
        "Generate exactly 2 functional requirements for the single persona you are given. "
        "Each requirement must describe concrete system behavior and must be testable. "
        "Avoid vague words such as easy, better, seamless, user friendly, intuitive, fast, helpful, effective, regular, personalized, transparent, clear, or useful. "
        "Do not write general product goals. Write actual system requirements. "
        "Each acceptance criteria must use Given, When, Then and be specific enough to test. "
        "Return strict JSON only with this shape: "
        "{\"requirements\": ["
        "{\"description\": \"The system shall ...\", "
        "\"acceptance_criteria\": \"Given ... When ... Then ...\"}"
        "]}"
    )

    lines: List[str] = [
        f"Persona ID: {persona['id']}",
        f"Persona Name: {persona['name']}",
        f"Persona Description: {persona['description']}",
        f"Derived Group: {persona['derived_from_group']}",
        f"Group Theme: {group['theme']}",
        f"Group Summary: {group.get('group_summary', '')}"
    ]

    if persona.get("goals"):
        lines.append("Goals: " + "; ".join(persona["goals"]))
    if persona.get("pain_points"):
        lines.append("Pain Points: " + "; ".join(persona["pain_points"]))
    if persona.get("context"):
        lines.append("Context: " + "; ".join(persona["context"]))
    if persona.get("constraints"):
        lines.append("Constraints: " + "; ".join(persona["constraints"]))
    if group.get("keywords"):
        lines.append("Keywords: " + ", ".join(group["keywords"]))
    if group.get("example_reviews"):
        lines.append("Example Reviews:")
        for review in group["example_reviews"]:
            lines.append(f"- {review}")

    lines.append("")
    lines.append("Good requirement style examples:")
    lines.append("- The system shall display a Premium label on each premium feature before the user attempts to open that feature.")
    lines.append("- The system shall allow users to export their saved mood history as a file.")
    lines.append("- The system shall store a user selected reminder time and send a notification at that time.")

    user_prompt = (
        "Create exactly 2 strong functional requirements for this persona.\n"
        "They must be concrete and testable.\n\n"
        + "\n".join(lines)
    )

    return system_prompt, user_prompt


def build_retry_prompt(
    persona: Dict[str, Any],
    group: Dict[str, Any],
    rejected_requirements: List[Dict[str, Any]],
    reasons: List[str]
) -> Tuple[str, str]:
    # this second prompt is stricter and tells the model what went wrong
    system_prompt = (
        "You are rewriting weak requirements into stronger software requirements. "
        "Generate exactly 2 functional requirements only. "
        "They must be concrete, testable, and written as system behavior. "
        "Do not use vague words. "
        "Acceptance criteria must use Given, When, Then and define observable behavior. "
        "Return strict JSON only with this shape: "
        "{\"requirements\": ["
        "{\"description\": \"The system shall ...\", "
        "\"acceptance_criteria\": \"Given ... When ... Then ...\"}"
        "]}"
    )

    lines: List[str] = [
        f"Persona Name: {persona['name']}",
        f"Derived Group: {persona['derived_from_group']}",
        f"Group Theme: {group['theme']}",
        f"Group Summary: {group.get('group_summary', '')}"
    ]

    if persona.get("goals"):
        lines.append("Goals: " + "; ".join(persona["goals"]))
    if persona.get("pain_points"):
        lines.append("Pain Points: " + "; ".join(persona["pain_points"]))
    if group.get("keywords"):
        lines.append("Keywords: " + ", ".join(group["keywords"]))

    if rejected_requirements:
        lines.append("The earlier requirements were weak:")
        for item in rejected_requirements:
            lines.append(f"- {item.get('description', '')}")

    if reasons:
        lines.append("Problems to avoid:")
        for reason in reasons:
            lines.append(f"- {reason}")

    user_prompt = (
        "Rewrite the requirements so they are more concrete.\n"
        "For example, instead of saying the system should be effective or helpful, say exactly what data it displays, stores, exports, or sends.\n"
        "Generate exactly 2 better requirements now.\n\n"
        + "\n".join(lines)
    )

    return system_prompt, user_prompt


def fallback_requirements_for_persona(persona: Dict[str, Any], group: Dict[str, Any]) -> List[Dict[str, str]]:
    # this fallback is here so the script can still finish with strong enough requirements
    theme = group["theme"].lower()

    if "privacy" in theme or "data" in theme:
        return [
            {
                "description": "The system shall display a data usage summary for each category of personal data collected by the app.",
                "acceptance_criteria": "Given the user opens the privacy settings screen, When the user selects a data category, Then the system must display the purpose of collection, whether the data is shared, and which third party services receive it."
            },
            {
                "description": "The system shall allow users to export their saved mood history and journal data.",
                "acceptance_criteria": "Given the user has saved mood records in the app, When the user selects the export data option, Then the system must generate an export file containing the user's saved mood history and journal entries."
            }
        ]

    if "technical" in theme or "bug" in theme:
        return [
            {
                "description": "The system shall display an error screen with a retry action when a requested page fails to load.",
                "acceptance_criteria": "Given the user opens a page that cannot be loaded, When the loading attempt fails, Then the system must display an error screen with a retry button instead of a blank page."
            },
            {
                "description": "The system shall restore unsaved questionnaire responses after an unexpected application close.",
                "acceptance_criteria": "Given the user has entered questionnaire responses and the app closes unexpectedly, When the user reopens the app, Then the system must restore the unsaved responses from the interrupted session."
            }
        ]

    if "pricing" in theme or "paywall" in theme:
        return [
            {
                "description": "The system shall display a Premium label on each premium feature before the user attempts to open that feature.",
                "acceptance_criteria": "Given the user is viewing a list of app features, When the feature list is displayed, Then every premium feature must show a Premium label and free features must not show that label."
            },
            {
                "description": "The system shall display the subscription price, billing period, and included features before the user confirms a premium purchase.",
                "acceptance_criteria": "Given the user selects a premium plan, When the purchase screen is opened, Then the system must display the price, billing period, and included premium features before payment is confirmed."
            }
        ]

    if "usability" in theme or "feedback" in theme:
        return [
            {
                "description": "The system shall allow users to submit interface or content feedback from within the app.",
                "acceptance_criteria": "Given the user opens the feedback screen, When the user enters feedback text and submits it, Then the system must save the submission and display a confirmation message."
            },
            {
                "description": "The system shall allow users to hide a question they mark as not applicable from future question sets.",
                "acceptance_criteria": "Given the user is answering a question, When the user marks the question as not applicable, Then the system must exclude that question from future question sets for that user."
            }
        ]

    return [
        {
            "description": "The system shall display a mood trend view based on the user's saved mood entries.",
            "acceptance_criteria": "Given the user has saved multiple mood entries, When the user opens the mood trends screen, Then the system must display a trend view generated from the saved mood entries."
        },
        {
            "description": "The system shall display recommendations based on patterns found in the user's recorded mood history.",
            "acceptance_criteria": "Given the user has recorded multiple mood entries over time, When the user opens the recommendations screen, Then the system must display recommendations that are based on the user's recorded mood history."
        }
    ]


def validate_requirement_pair(requirements: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []

    if len(requirements) != 2:
        reasons.append("the response did not contain exactly 2 requirements")
        return False, reasons

    descriptions_seen = set()

    for req in requirements:
        description = normalize_description(req.get("description", ""))
        acceptance = str(req.get("acceptance_criteria", "")).strip()

        if contains_vague_language(description):
            reasons.append(f"vague language found in description: {description}")

        if not description.lower().startswith("the system shall"):
            reasons.append("description does not start with The system shall")

        if not is_valid_acceptance_criteria(acceptance):
            reasons.append(f"acceptance criteria is not in Given When Then format: {acceptance}")

        key = description.lower().strip()
        if key in descriptions_seen:
            reasons.append("duplicate requirement descriptions were generated")
        descriptions_seen.add(key)

    return len(reasons) == 0, reasons


def clean_requirement_pair(
    requirements: List[Dict[str, Any]],
    persona: Dict[str, Any],
    group: Dict[str, Any]
) -> List[Dict[str, str]]:
    cleaned: List[Dict[str, str]] = []

    for req in requirements[:2]:
        cleaned.append({
            "description": normalize_description(req.get("description", "")),
            "acceptance_criteria": str(req.get("acceptance_criteria", "")).strip(),
            "source_persona": persona["name"],
            "source_group": persona["derived_from_group"]
        })

    return cleaned


def generate_requirements_for_persona(
    client: Groq,
    persona: Dict[str, Any],
    group: Dict[str, Any]
) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    # first try
    system_prompt, user_prompt = build_persona_prompt(persona, group)
    first_result = call_groq_json(client, system_prompt, user_prompt)
    first_requirements = first_result.get("requirements", [])
    first_ok, first_reasons = validate_requirement_pair(first_requirements)

    if first_ok:
        return clean_requirement_pair(first_requirements, persona, group), {
            "persona_id": persona["id"],
            "first_attempt_system_prompt": system_prompt,
            "first_attempt_user_prompt": user_prompt,
            "first_attempt_raw_response": first_result,
            "retry_attempt_system_prompt": "",
            "retry_attempt_user_prompt": "",
            "retry_attempt_raw_response": {},
            "used_fallback": False
        }

    # retry if the first one is weak
    retry_system_prompt, retry_user_prompt = build_retry_prompt(
        persona=persona,
        group=group,
        rejected_requirements=first_requirements if isinstance(first_requirements, list) else [],
        reasons=first_reasons
    )
    retry_result = call_groq_json(client, retry_system_prompt, retry_user_prompt)
    retry_requirements = retry_result.get("requirements", [])
    retry_ok, retry_reasons = validate_requirement_pair(retry_requirements)

    if retry_ok:
        return clean_requirement_pair(retry_requirements, persona, group), {
            "persona_id": persona["id"],
            "first_attempt_system_prompt": system_prompt,
            "first_attempt_user_prompt": user_prompt,
            "first_attempt_raw_response": first_result,
            "retry_attempt_system_prompt": retry_system_prompt,
            "retry_attempt_user_prompt": retry_user_prompt,
            "retry_attempt_raw_response": retry_result,
            "used_fallback": False
        }

    # final fallback if the model is still messy
    fallback = fallback_requirements_for_persona(persona, group)
    return clean_requirement_pair(fallback, persona, group), {
        "persona_id": persona["id"],
        "first_attempt_system_prompt": system_prompt,
        "first_attempt_user_prompt": user_prompt,
        "first_attempt_raw_response": first_result,
        "retry_attempt_system_prompt": retry_system_prompt,
        "retry_attempt_user_prompt": retry_user_prompt,
        "retry_attempt_raw_response": retry_result,
        "used_fallback": True,
        "retry_failure_reasons": retry_reasons
    }


def build_markdown_spec(requirements: List[Dict[str, str]]) -> str:
    parts: List[str] = []

    for i, req in enumerate(requirements, start=1):
        parts.append(f"# Requirement ID: AFR{i}\n")
        parts.append(f"- Description: [{req['description']}]")
        parts.append(f"- Source Persona: [{req['source_persona']}]")
        parts.append(f"- Traceability: [Derived from review group {req['source_group']}]")
        parts.append(f"- Acceptance Criteria: [{req['acceptance_criteria']}]")
        parts.append("")

    return "\n".join(parts).strip() + "\n"


def update_prompt_file(spec_prompt_record: Dict[str, Any]) -> None:
    existing: Dict[str, Any] = {}

    if PROMPT_PATH.exists():
        try:
            existing = load_json(PROMPT_PATH)
        except Exception:
            existing = {}

    existing["spec_generation"] = spec_prompt_record
    save_json(existing, PROMPT_PATH)


def main() -> None:
    personas_data = load_json(PERSONAS_PATH)
    groups_data = load_json(GROUPS_PATH)
    group_lookup = build_group_lookup(groups_data)

    client = get_client()

    all_requirements: List[Dict[str, str]] = []
    prompt_records: List[Dict[str, Any]] = []

    for persona in personas_data["personas"]:
        group = group_lookup[persona["derived_from_group"]]
        persona_requirements, prompt_record = generate_requirements_for_persona(client, persona, group)
        all_requirements.extend(persona_requirements)
        prompt_records.append(prompt_record)

    if len(all_requirements) != 10:
        raise ValueError("the final requirement set does not contain exactly 10 requirements")

    spec_text = build_markdown_spec(all_requirements)
    save_text(spec_text, SPEC_PATH)

    spec_prompt_record = {
        "model": MODEL_NAME,
        "requirements_per_persona": REQUIREMENTS_PER_PERSONA,
        "generation_records": prompt_records
    }
    update_prompt_file(spec_prompt_record)

    print("automated spec generation finished")
    print(f"saved automated spec to {SPEC_PATH}")
    print(f"updated prompts in {PROMPT_PATH}")


if __name__ == "__main__":
    main()