"""
Collect raw Google Play reviews for the assigned app and save them as JSONL.

This script is designed for EECS 4312 SpecChain Task 2.

Output:
- data/reviews_raw.jsonl
- data/dataset_metadata.json (initial collection metadata)
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from google_play_scraper import Sort, reviews


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RAW_PATH = DATA_DIR / "reviews_raw.jsonl"
METADATA_PATH = DATA_DIR / "dataset_metadata.json"

APP_ID = "de.moodpath.android"
APP_NAME = "MindDoc"
APP_URL = "https://play.google.com/store/apps/details?id=de.moodpath.android&hl=en_CA"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect raw Google Play reviews.")
    parser.add_argument("--count", type=int, default=5000, help="Target number of reviews to collect.")
    parser.add_argument("--lang", type=str, default="en", help="Review language code.")
    parser.add_argument("--country", type=str, default="ca", help="Country code.")
    parser.add_argument(
        "--sort",
        type=str,
        default="newest",
        choices=["newest", "most_relevant"],
        help="Sorting strategy for Google Play reviews."
    )
    return parser.parse_args()


def json_safe_datetime(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def normalize_review(raw_review: Dict[str, Any], index: int, lang: str, country: str) -> Dict[str, Any]:
    """
    Convert the scraper output into a stable JSON structure for this project.
    """
    return {
        "id": f"rev_{index:06d}",
        "reviewId": raw_review.get("reviewId"),
        "app_id": APP_ID,
        "app_name": APP_NAME,
        "source_url": APP_URL,
        "content": raw_review.get("content", ""),
        "score": raw_review.get("score"),
        "thumbsUpCount": raw_review.get("thumbsUpCount"),
        "reviewCreatedVersion": raw_review.get("reviewCreatedVersion"),
        "appVersion": raw_review.get("appVersion"),
        "at": json_safe_datetime(raw_review.get("at")),
        "replyContent": raw_review.get("replyContent"),
        "repliedAt": json_safe_datetime(raw_review.get("repliedAt")),
        "lang": lang,
        "country": country,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "google-play-scraper"
    }


def fetch_reviews(target_count: int, lang: str, country: str, sort_mode: str) -> List[Dict[str, Any]]:
    """
    Fetch reviews using paginated requests until we hit the target count
    or there are no more new reviews to fetch.
    """
    sort_value = Sort.NEWEST if sort_mode == "newest" else Sort.MOST_RELEVANT

    collected_reviews: List[Dict[str, Any]] = []
    seen_review_ids: Set[str] = set()
    continuation_token = None

    while len(collected_reviews) < target_count:
        remaining = target_count - len(collected_reviews)
        batch_size = min(200, remaining)

        batch, continuation_token = reviews(
            APP_ID,
            lang=lang,
            country=country,
            sort=sort_value,
            count=batch_size,
            continuation_token=continuation_token,
        )

        if not batch:
            break

        new_in_this_batch = 0

        for review in batch:
            play_review_id = review.get("reviewId")
            if not play_review_id or play_review_id in seen_review_ids:
                continue

            seen_review_ids.add(play_review_id)
            collected_reviews.append(review)
            new_in_this_batch += 1

            if len(collected_reviews) >= target_count:
                break

        # Stop if pagination is exhausted or we are no longer getting new reviews.
        if continuation_token is None or new_in_this_batch == 0:
            break

    return collected_reviews


def write_jsonl(records: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_initial_metadata(raw_count: int, lang: str, country: str, sort_mode: str) -> None:
    metadata = {
        "app_name": APP_NAME,
        "app_id": APP_ID,
        "source_url": APP_URL,
        "dataset_size": None,  # filled after cleaning
        "raw_dataset_size": raw_count,
        "collection_method": {
            "tool": "google-play-scraper",
            "script": "src/01_collect_or_import.py",
            "platform": "Google Play Store",
            "lang": lang,
            "country": country,
            "sort": sort_mode,
            "target_raw_review_count": raw_count,
            "notes": "Collected programmatically using paginated review requests."
        },
        "cleaning_decisions": {}
    }

    with METADATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def main() -> None:
    args = parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    raw_reviews = fetch_reviews(
        target_count=args.count,
        lang=args.lang,
        country=args.country,
        sort_mode=args.sort,
    )

    normalized = [
        normalize_review(review, index=i + 1, lang=args.lang, country=args.country)
        for i, review in enumerate(raw_reviews)
    ]

    write_jsonl(normalized, RAW_PATH)
    write_initial_metadata(
        raw_count=len(normalized),
        lang=args.lang,
        country=args.country,
        sort_mode=args.sort,
    )

    print(f"Saved {len(normalized)} raw reviews to {RAW_PATH}")


if __name__ == "__main__":
    main()