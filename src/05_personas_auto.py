from __future__ import annotations

import json
import os
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from groq import Groq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# this script handles task 4.1 and 4.2
# it finds 5 automated review groups from the cleaned dataset
# then it creates 1 persona for each auto group
# it also saves the prompts used so the automation process is documented

REPO_ROOT = Path(__file__).resolve().parents[1]

CLEAN_REVIEWS_PATH = REPO_ROOT / "data" / "reviews_clean.jsonl"
AUTO_GROUPS_PATH = REPO_ROOT / "data" / "review_groups_auto.json"
AUTO_PERSONAS_PATH = REPO_ROOT / "personas" / "personas_auto.json"
PROMPT_PATH = REPO_ROOT / "prompts" / "prompt_auto.json"

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
TEMPERATURE = 0.2
RANDOM_SEED = 42

N_GROUPS = 5
SAMPLE_PER_SCORE = 25
EXTRA_LONG_REVIEWS = 35

TARGET_REVIEWS_PER_GROUP = 15
MIN_REVIEWS_PER_GROUP = 10
REPRESENTATIVE_REVIEW_IDS_PER_GROUP = 12
EXAMPLE_REVIEWS_PER_GROUP = 3
PERSONA_EVIDENCE_COUNT = 3


def load_reviews(path: Path) -> List[Dict[str, Any]]:
    # reads the cleaned jsonl file line by line
    reviews = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                reviews.append(json.loads(line))
    return reviews


def save_json(data: Any, path: Path) -> None:
    # saves normal json with indentation so it is easier to inspect
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_json(text: str) -> Any:
    # llms sometimes wrap json in code fences or add extra text
    # this tries a few safe ways to pull the json out
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
    # makes sure the key exists before trying anything
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set in your environment.")
    return Groq(api_key=api_key)


def call_groq_json(client: Groq, system_prompt: str, user_prompt: str) -> Any:
    # sends a request to groq and expects json back
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


def sample_reviews_for_theme_discovery(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # i do not want to send all 4000+ reviews in one prompt
    # so this picks a balanced sample from different ratings
    # and also includes some longer reviews because they carry more detail
    rng = random.Random(RANDOM_SEED)
    sampled: List[Dict[str, Any]] = []
    used_ids = set()

    by_score: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for review in reviews:
        by_score[review["score"]].append(review)

    for score in sorted(by_score.keys()):
        pool = by_score[score][:]
        rng.shuffle(pool)
        for review in pool[:SAMPLE_PER_SCORE]:
            if review["id"] not in used_ids:
                sampled.append(review)
                used_ids.add(review["id"])

    longest_reviews = sorted(
        reviews,
        key=lambda x: len(x["original_text"].split()),
        reverse=True
    )

    for review in longest_reviews[:EXTRA_LONG_REVIEWS]:
        if review["id"] not in used_ids:
            sampled.append(review)
            used_ids.add(review["id"])

    sampled.sort(key=lambda x: x["id"])
    return sampled


def build_theme_discovery_prompts(sampled_reviews: List[Dict[str, Any]]) -> Tuple[str, str]:
    # this prompt asks for 5 themes that are clearly different from each other
    # i am pushing it to avoid repetitive themes like "tracking and support" five times
    system_prompt = (
        "You are helping with software requirements engineering for a mental health app. "
        "Read the sampled user reviews and discover exactly 5 DISTINCT review group themes. "
        "Each theme must represent a clear user situation, recurring complaint, recurring need, or recurring value point. "
        "The 5 themes must be meaningfully different from each other. "
        "Do not produce five versions of general mood tracking or emotional support. "
        "If present in the reviews, try to capture different concerns such as pricing or paywalls, technical or login issues, "
        "reminders or habit support, insights or therapy usefulness, and usability, accessibility, language, privacy, or customization. "
        "The themes should be similar in granularity to manual requirements engineering groups, but not identical to any manual set. "
        "Return strict JSON only with this shape: "
        "{\"groups\": [{\"group_id\": \"AG1\", \"theme\": \"...\", \"summary\": \"...\", \"keywords\": [\"...\", \"...\"]}]}. "
        "Use exactly 5 groups named AG1 to AG5. "
        "Each keywords list should contain 6 to 10 short keywords or short phrases. "
        "Avoid overlap as much as possible."
    )

    lines = []
    for review in sampled_reviews:
        lines.append(f"[{review['id']} | score={review['score']}] {review['original_text']}")

    user_prompt = (
        "Here is a sample of cleaned MindDoc reviews.\n"
        "Create exactly 5 distinct automated review group blueprints.\n\n"
        "Sample reviews:\n"
        + "\n".join(lines)
    )

    return system_prompt, user_prompt


def discover_group_blueprints(
    client: Groq, sampled_reviews: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    # this gets the 5 theme blueprints from groq first
    system_prompt, user_prompt = build_theme_discovery_prompts(sampled_reviews)
    result = call_groq_json(client, system_prompt, user_prompt)

    groups = result.get("groups", [])
    if len(groups) != N_GROUPS:
        raise ValueError("model did not return exactly 5 review group blueprints")

    cleaned_groups = []
    for i, group in enumerate(groups, start=1):
        cleaned_groups.append({
            "group_id": f"AG{i}",
            "theme": str(group.get("theme", "")).strip(),
            "summary": str(group.get("summary", "")).strip(),
            "keywords": [str(k).strip() for k in group.get("keywords", []) if str(k).strip()][:10],
        })

    prompt_record = {
        "model": MODEL_NAME,
        "theme_discovery_system_prompt": system_prompt,
        "theme_discovery_user_prompt": user_prompt,
        "theme_discovery_raw_response": result
    }

    return cleaned_groups, prompt_record


def build_vectorizer() -> TfidfVectorizer:
    # this turns texts into tf idf vectors
    # using unigrams and bigrams helps catch short phrases better
    return TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=3,
        max_df=0.9
    )


def build_theme_text(theme: Dict[str, Any]) -> str:
    # combines the theme name, summary, and keywords into one text block
    theme_name = theme.get("theme", "")
    summary = theme.get("summary", "")
    keywords = " ".join(theme.get("keywords", []))
    return f"{theme_name}. {summary}. {keywords}".strip()


def keyword_match_score(clean_text: str, keywords: List[str]) -> float:
    # this gives a small bonus when the review explicitly uses theme keywords
    score = 0.0
    text = f" {clean_text} "

    for keyword in keywords:
        kw = keyword.strip().lower()
        if not kw:
            continue

        if " " in kw:
            if kw in clean_text:
                score += 1.5
        else:
            if f" {kw} " in text:
                score += 1.0

    return score


def score_reviews_against_themes(
    reviews: List[Dict[str, Any]],
    themes: List[Dict[str, Any]]
) -> List[List[float]]:
    # this scores every review against every theme using tf idf similarity
    # plus a small keyword bonus so obvious matches rise to the top
    review_texts = [review["clean_text"] for review in reviews]
    theme_texts = [build_theme_text(theme) for theme in themes]

    vectorizer = build_vectorizer()
    matrix = vectorizer.fit_transform(review_texts + theme_texts)

    review_matrix = matrix[:len(reviews)]
    theme_matrix = matrix[len(reviews):]

    sim_matrix = cosine_similarity(review_matrix, theme_matrix)

    all_scores: List[List[float]] = []

    for review_idx, review in enumerate(reviews):
        row_scores = []
        for theme_idx, theme in enumerate(themes):
            sim_score = float(sim_matrix[review_idx, theme_idx])
            kw_score = keyword_match_score(review["clean_text"], theme.get("keywords", []))
            total_score = sim_score + 0.08 * kw_score
            row_scores.append(total_score)
        all_scores.append(row_scores)

    return all_scores


def select_strong_reviews_for_groups(
    reviews: List[Dict[str, Any]],
    themes: List[Dict[str, Any]],
    all_scores: List[List[float]]
) -> Dict[str, List[int]]:
    # this is the important change
    # instead of forcing all reviews into one of the 5 groups,
    # i only keep the strongest matching reviews for each theme
    # that should give cleaner and more meaningful groups
    theme_rankings: Dict[str, List[Tuple[int, float, float]]] = {}

    for theme_idx, theme in enumerate(themes):
        ranking = []
        for review_idx, scores in enumerate(all_scores):
            best_score = max(scores)
            sorted_scores = sorted(scores, reverse=True)
            second_best = sorted_scores[1] if len(sorted_scores) > 1 else 0.0
            confidence_margin = best_score - second_best
            score_for_this_theme = scores[theme_idx]

            # bigger margin means the review fits this theme more cleanly than the others
            ranking.append((review_idx, score_for_this_theme, confidence_margin))

        ranking.sort(key=lambda x: (x[1], x[2]), reverse=True)
        theme_rankings[theme["group_id"]] = ranking

    selected: Dict[str, List[int]] = {theme["group_id"]: [] for theme in themes}
    used_review_indices = set()

    # first pass tries to fill each group with high quality unique reviews
    for theme in themes:
        group_id = theme["group_id"]
        for review_idx, score_value, margin in theme_rankings[group_id]:
            if review_idx in used_review_indices:
                continue

            # keep weak matches out when possible
            if score_value < 0.05:
                continue

            selected[group_id].append(review_idx)
            used_review_indices.add(review_idx)

            if len(selected[group_id]) >= TARGET_REVIEWS_PER_GROUP:
                break

    # second pass just makes sure every group has at least the minimum required
    for theme in themes:
        group_id = theme["group_id"]
        if len(selected[group_id]) >= MIN_REVIEWS_PER_GROUP:
            continue

        for review_idx, score_value, margin in theme_rankings[group_id]:
            if review_idx in used_review_indices:
                continue

            selected[group_id].append(review_idx)
            used_review_indices.add(review_idx)

            if len(selected[group_id]) >= MIN_REVIEWS_PER_GROUP:
                break

    return selected


def build_auto_groups(
    reviews: List[Dict[str, Any]],
    themes: List[Dict[str, Any]],
    selected: Dict[str, List[int]],
    all_scores: List[List[float]]
) -> Dict[str, Any]:
    # builds the final review_groups_auto.json structure
    groups = []

    group_lookup = {theme["group_id"]: theme for theme in themes}

    for theme_idx, theme in enumerate(themes):
        group_id = theme["group_id"]
        member_indices = selected[group_id]

        ranked_member_indices = sorted(
            member_indices,
            key=lambda idx: all_scores[idx][theme_idx],
            reverse=True
        )

        example_indices = ranked_member_indices[:EXAMPLE_REVIEWS_PER_GROUP]
        representative_indices = ranked_member_indices[:REPRESENTATIVE_REVIEW_IDS_PER_GROUP]

        groups.append({
            "group_id": group_id,
            "theme": theme["theme"],
            "review_ids": [reviews[idx]["id"] for idx in ranked_member_indices],
            "example_reviews": [reviews[idx]["original_text"] for idx in example_indices],
            "group_summary": theme["summary"],
            "keywords": theme["keywords"],
            "representative_review_ids": [reviews[idx]["id"] for idx in representative_indices]
        })

    return {"groups": groups}


def build_persona_generation_prompts(
    reviews: List[Dict[str, Any]],
    auto_groups_data: Dict[str, Any]
) -> Tuple[str, str]:
    # this prompt creates 1 persona per auto group using the representative reviews
    review_lookup = {review["id"]: review for review in reviews}

    system_prompt = (
        "You are creating requirements engineering personas from grouped app reviews. "
        "Generate one grounded persona for each provided review group. "
        "Return strict JSON only with this shape: "
        "{\"personas\": [{\"id\": \"P_auto_1\", \"name\": \"...\", \"description\": \"...\", "
        "\"derived_from_group\": \"AG1\", \"goals\": [\"...\"], \"pain_points\": [\"...\"], "
        "\"context\": [\"...\"], \"constraints\": [\"...\"], \"evidence_reviews\": [\"rev_...\"]}]}. "
        "Keep the language simple and practical. "
        "Do not invent details that are not supported by the group. "
        "Each persona should clearly match the group theme and use exactly 3 evidence review ids from the representative reviews shown."
    )

    parts = []
    for group in auto_groups_data["groups"]:
        parts.append(f"Group: {group['group_id']}")
        parts.append(f"Theme: {group['theme']}")
        parts.append(f"Summary: {group.get('group_summary', '')}")
        if group.get("keywords"):
            parts.append("Keywords: " + ", ".join(group["keywords"]))
        parts.append("Representative reviews:")

        for review_id in group.get("representative_review_ids", [])[:8]:
            review = review_lookup[review_id]
            parts.append(f"- [{review_id}] {review['original_text']}")

        parts.append("")

    user_prompt = (
        "Use the following automated review groups to create personas.\n\n"
        + "\n".join(parts)
    )

    return system_prompt, user_prompt


def generate_personas(
    client: Groq,
    reviews: List[Dict[str, Any]],
    auto_groups_data: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    # asks groq to generate all 5 personas from the final auto groups
    system_prompt, user_prompt = build_persona_generation_prompts(reviews, auto_groups_data)
    result = call_groq_json(client, system_prompt, user_prompt)

    personas = result.get("personas", [])
    if len(personas) != N_GROUPS:
        raise ValueError("model did not return exactly 5 personas")

    cleaned_personas = []
    for i, persona in enumerate(personas, start=1):
        cleaned_personas.append({
            "id": f"P_auto_{i}",
            "name": str(persona.get("name", f"Auto Persona {i}")).strip(),
            "description": str(persona.get("description", "")).strip(),
            "derived_from_group": str(persona.get("derived_from_group", f"AG{i}")).strip(),
            "goals": [str(x).strip() for x in persona.get("goals", []) if str(x).strip()],
            "pain_points": [str(x).strip() for x in persona.get("pain_points", []) if str(x).strip()],
            "context": [str(x).strip() for x in persona.get("context", []) if str(x).strip()],
            "constraints": [str(x).strip() for x in persona.get("constraints", []) if str(x).strip()],
            "evidence_reviews": [str(x).strip() for x in persona.get("evidence_reviews", []) if str(x).strip()][:PERSONA_EVIDENCE_COUNT]
        })

    prompt_record = {
        "persona_generation_system_prompt": system_prompt,
        "persona_generation_user_prompt": user_prompt,
        "persona_generation_raw_response": result
    }

    return {"personas": cleaned_personas}, prompt_record


def build_console_summary(auto_groups_data: Dict[str, Any]) -> str:
    # prints a short summary so the terminal output is easy to inspect
    lines = []
    for group in auto_groups_data["groups"]:
        lines.append(f"{group['group_id']}: {group['theme']} ({len(group['review_ids'])} reviews)")
    return "\n".join(lines)


def main() -> None:
    # main flow starts here
    # load reviews, discover themes, score reviews, keep strongest matches, then generate personas
    reviews = load_reviews(CLEAN_REVIEWS_PATH)
    client = get_client()

    sampled_reviews = sample_reviews_for_theme_discovery(reviews)
    themes, theme_prompt_record = discover_group_blueprints(client, sampled_reviews)

    all_scores = score_reviews_against_themes(reviews, themes)
    selected = select_strong_reviews_for_groups(reviews, themes, all_scores)
    auto_groups_data = build_auto_groups(reviews, themes, selected, all_scores)
    save_json(auto_groups_data, AUTO_GROUPS_PATH)

    personas_data, persona_prompt_record = generate_personas(client, reviews, auto_groups_data)
    save_json(personas_data, AUTO_PERSONAS_PATH)

    prompt_data = {
        "model": MODEL_NAME,
        "theme_discovery": theme_prompt_record,
        "persona_generation": persona_prompt_record,
        "notes": "This file stores the prompts used to generate automated review groups and personas for Task 4."
    }
    save_json(prompt_data, PROMPT_PATH)

    print("automated grouping and persona generation finished")
    print(build_console_summary(auto_groups_data))
    print(f"\nsaved automated review groups to {AUTO_GROUPS_PATH}")
    print(f"saved automated personas to {AUTO_PERSONAS_PATH}")
    print(f"saved prompts to {PROMPT_PATH}")


if __name__ == "__main__":
    main()