# EECS4312_W26_SpecChain_218491555
# Urmay Suthar
## Project Overview
This repository contains my EECS 4312 course project for transforming Google Play app reviews into software requirements engineering artifacts using three pipelines:

- manual pipeline
- automated pipeline
- hybrid pipeline

The assigned application for this project is **MindDoc**.

Google Play link:  
https://play.google.com/store/apps/details?id=de.moodpath.android&hl=en_CA

---

How to Run:
1. python src/00_validate_repo.py
2. python src/02_clean.py
3. python src/run_all.py
4. Open metrics/metrics_summary.json for comparison results

    ## Groq API Setup

    The automated pipeline **will not run** unless the `GROQ_API_KEY` environment variable is set.

    ### PowerShell
    ```powershell
    $env:GROQ_API_KEY = "your_key_here"

## Dataset

### Data collection method
The raw reviews were collected programmatically from the Google Play Store using the Python package **google-play-scraper** through `src/01_collect_or_import.py`.

### Dataset files
- `data/reviews_raw.jsonl` contains the raw collected reviews
- `data/reviews_clean.jsonl` contains the cleaned review dataset after preprocessing
- `data/dataset_metadata.json` contains dataset metadata, collection details, and cleaning decisions

### Dataset size
- Raw dataset size: **5000 reviews**
- Final cleaned dataset size: **4267 reviews**

### Cleaning steps
The cleaning script in `src/02_clean.py` performs the following preprocessing steps:

- removes duplicates
- removes empty entries
- removes extremely short reviews
- removes punctuation
- removes special characters and emojis
- converts numbers to text
- removes extra whitespace
- converts text to lowercase
- removes stop words
- lemmatizes the reviews

---

## Repository Structure

### `data/`
Contains the raw and cleaned datasets, dataset metadata, and review grouping files for all three pipelines.

Files include:
- `reviews_raw.jsonl`
- `reviews_clean.jsonl`
- `dataset_metadata.json`
- `review_groups_manual.json`
- `review_groups_auto.json`
- `review_groups_hybrid.json`

### `personas/`
Contains persona files for the manual, automated, and hybrid pipelines.

Files include:
- `personas_manual.json`
- `personas_auto.json`
- `personas_hybrid.json`

### `spec/`
Contains the generated requirement specifications for the three pipelines.

Files include:
- `spec_manual.md`
- `spec_auto.md`
- `spec_hybrid.md`

### `tests/`
Contains validation test scenarios for the three pipelines.

Files include:
- `tests_manual.json`
- `tests_auto.json`
- `tests_hybrid.json`

### `metrics/`
Contains the metric outputs for each pipeline and the comparison summary.

Files include:
- `metrics_manual.json`
- `metrics_auto.json`
- `metrics_hybrid.json`
- `metrics_summary.json`

### `prompts/`
Contains the prompts used in the automated pipeline.

Files include:
- `prompt_auto.json`

### `reflection/`
Contains the final written reflection.

Files include:
- `reflection.md`

### `src/`
Contains the Python scripts used for validation, collection, cleaning, automated generation, and metrics.

Files include:
- `00_validate_repo.py`
- `01_collect_or_import.py`
- `02_clean.py`
- `03_manual_coding_template.py`
- `04_personas_manual.py`
- `05_personas_auto.py`
- `06_spec_generate.py`
- `07_tests_generate.py`
- `08_metrics.py`
- `run_all.py`

---

## Required Python Packages

Install the required packages before running the scripts:

```bash
pip install google-play-scraper nltk num2words emoji groq scikit-learn

