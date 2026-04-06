"""
Clean the raw Google Play review dataset and save the cleaned dataset as JSONL.

This script is designed for EECS 4312 SpecChain Task 2.

Input:
- data/reviews_raw.jsonl

Output:
- data/reviews_clean.jsonl
- data/dataset_metadata.json (updated with cleaning information)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set

import emoji
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from num2words import num2words


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RAW_PATH = DATA_DIR / "reviews_raw.jsonl"
CLEAN_PATH = DATA_DIR / "reviews_clean.jsonl"
METADATA_PATH = DATA_DIR / "dataset_metadata.json"

MIN_TOKENS = 3

# Download required NLTK resources once.
nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)
nltk.download("omw-1.4", quiet=True)

STOP_WORDS = set(stopwords.words("english"))
LEMMATIZER = WordNetLemmatizer()

NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\b")
WHITESPACE_PATTERN = re.compile(r"\s+")
NON_ALPHA_PATTERN = re.compile(r"[^a-zA-Z\s]")


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Raw dataset not found: {path}")

    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(records: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def number_to_words(match: re.Match[str]) -> str:
    value = match.group(0)
    try:
        if "." in value:
            return " " + num2words(float(value)) + " "
        return " " + num2words(int(value)) + " "
    except Exception:
        return " "


def clean_text(text: str) -> str:
    text = text.strip()

    # Convert numbers to words before removing punctuation/special characters.
    text = NUMBER_PATTERN.sub(number_to_words, text)

    # Remove emojis.
    text = emoji.replace_emoji(text, replace=" ")

    # Lowercase.
    text = text.lower()

    # Remove punctuation, special characters, and anything non-alphabetic.
    text = NON_ALPHA_PATTERN.sub(" ", text)

    # Remove extra whitespace.
    text = WHITESPACE_PATTERN.sub(" ", text).strip()

    # Remove stop words and lemmatize.
    tokens = text.split()
    tokens = [token for token in tokens if token not in STOP_WORDS]
    tokens = [LEMMATIZER.lemmatize(token) for token in tokens]

    return " ".join(tokens).strip()


def load_metadata() -> Dict[str, Any]:
    if METADATA_PATH.exists():
        with METADATA_PATH.open("r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_metadata(metadata: Dict[str, Any]) -> None:
    with METADATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def main() -> None:
    raw_records = read_jsonl(RAW_PATH)

    seen_review_ids: Set[str] = set()
    seen_clean_texts: Set[str] = set()
    cleaned_records: List[Dict[str, Any]] = []

    duplicate_count = 0
    empty_count = 0
    short_count = 0

    for record in raw_records:
        review_id = record.get("reviewId")
        original_text = (record.get("content") or "").strip()

        # Remove empty reviews.
        if not original_text:
            empty_count += 1
            continue

        # Remove duplicates by Google Play review ID.
        if review_id and review_id in seen_review_ids:
            duplicate_count += 1
            continue
        if review_id:
            seen_review_ids.add(review_id)

        cleaned_text = clean_text(original_text)

        # Remove records that become empty after cleaning.
        if not cleaned_text:
            empty_count += 1
            continue

        # Remove extremely short reviews.
        token_count = len(cleaned_text.split())
        if token_count < MIN_TOKENS:
            short_count += 1
            continue

        # Remove duplicates by cleaned text as well.
        if cleaned_text in seen_clean_texts:
            duplicate_count += 1
            continue
        seen_clean_texts.add(cleaned_text)

        cleaned_record = {
            "id": record["id"],
            "reviewId": review_id,
            "app_id": record.get("app_id"),
            "app_name": record.get("app_name"),
            "score": record.get("score"),
            "at": record.get("at"),
            "reviewCreatedVersion": record.get("reviewCreatedVersion"),
            "appVersion": record.get("appVersion"),
            "original_text": original_text,
            "clean_text": cleaned_text,
        }

        cleaned_records.append(cleaned_record)

    write_jsonl(cleaned_records, CLEAN_PATH)

    metadata = load_metadata()
    metadata["dataset_size"] = len(cleaned_records)
    metadata["cleaned_dataset_size"] = len(cleaned_records)
    metadata["cleaning_decisions"] = {
        "script": "src/02_clean.py",
        "removed_duplicates": True,
        "removed_empty_entries": True,
        "removed_extremely_short_reviews": True,
        "extremely_short_threshold": f"fewer than {MIN_TOKENS} tokens after cleaning",
        "removed_punctuation": True,
        "removed_special_characters_and_emojis": True,
        "converted_numbers_to_text": True,
        "removed_extra_whitespace": True,
        "lowercased_text": True,
        "removed_stop_words": True,
        "lemmatized_reviews": True,
        "records_removed_as_duplicates": duplicate_count,
        "records_removed_as_empty": empty_count,
        "records_removed_as_too_short": short_count
    }

    save_metadata(metadata)

    print(f"Read {len(raw_records)} raw reviews")
    print(f"Saved {len(cleaned_records)} cleaned reviews to {CLEAN_PATH}")


if __name__ == "__main__":
    main()