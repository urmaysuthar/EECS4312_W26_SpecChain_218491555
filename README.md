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

## Dataset

### Data collection method
The raw reviews were collected programmatically from the Google Play Store using the Python package `google-play-scraper` through `src/01_collect_or_import.py`.

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

## Required Python Packages

Install the required packages before running the scripts:

```bash
pip install google-play-scraper nltk num2words emoji groq scikit-learn
```

## Groq API Setup

The automated pipeline will not run unless the `GROQ_API_KEY` environment variable is set first.

### PowerShell
```powershell
$env:GROQ_API_KEY = "your_key_here"
```

### Command Prompt
```cmd
set GROQ_API_KEY=your_key_here
```

Do **not** put your real API key inside the repository.

## How to Run

### 1. Validate the repository structure
```bash
python src/00_validate_repo.py
```

### 2. Run the full automated pipeline
Important: before running this command, make sure the `GROQ_API_KEY` environment variable is already set in the same terminal session.

```bash
python src/run_all.py
```

This script runs the automated pipeline in the following order:

1. collect raw reviews
2. clean the dataset
3. generate automated review groups and personas
4. generate the automated specification
5. generate automated tests
6. compute automated metrics

### 3. Compute all metrics and the summary file
```bash
python src/08_metrics.py --pipeline all
```

### 4. Open the comparison results
Open:
```text
metrics/metrics_summary.json
```

## Individual Commands

### Collect raw reviews
```bash
python src/01_collect_or_import.py --count 5000 --lang en --country ca --sort newest
```

### Clean the dataset
```bash
python src/02_clean.py
```

### Generate automated review groups and personas
```bash
python src/05_personas_auto.py
```

### Generate automated specification
```bash
python src/06_spec_generate.py
```

### Generate automated tests
```bash
python src/07_tests_generate.py
```

### Compute automated metrics only
```bash
python src/08_metrics.py --pipeline auto
```

### Compute hybrid metrics only
```bash
python src/08_metrics.py --pipeline hybrid
```

### Compute manual metrics only
```bash
python src/08_metrics.py --pipeline manual
```

## Pipeline Outputs

### Manual pipeline outputs
- `data/review_groups_manual.json`
- `personas/personas_manual.json`
- `spec/spec_manual.md`
- `tests/tests_manual.json`
- `metrics/metrics_manual.json`

### Automated pipeline outputs
- `data/review_groups_auto.json`
- `personas/personas_auto.json`
- `spec/spec_auto.md`
- `tests/tests_auto.json`
- `metrics/metrics_auto.json`
- `prompts/prompt_auto.json`

### Hybrid pipeline outputs
- `data/review_groups_hybrid.json`
- `personas/personas_hybrid.json`
- `spec/spec_hybrid.md`
- `tests/tests_hybrid.json`
- `metrics/metrics_hybrid.json`

### Comparison output
- `metrics/metrics_summary.json`

## Notes
- The automated pipeline depends on the Groq API key being set correctly before running the scripts.
- The manual and hybrid artifacts are already included in the repository.
- The repository validation script checks whether the required files and folders exist.
- The comparison between manual, automated, and hybrid pipelines is stored in `metrics/metrics_summary.json`.