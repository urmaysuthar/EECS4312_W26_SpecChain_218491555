# EECS4312_W26_SpecChain

## instructions:
Please update to include: 
- App name
- Data collection method
- Original dataset
- Final cleaned dataset
- Exact commands to run pipeline

# example
Application: [MindDoc: Mental Health Support]

Dataset:
- reviews_raw.jsonl contains the collected reviews.
- reviews_clean.jsonl contains the cleaned dataset.
- The cleaned dataset contains 842 reviews.

Repository Structure:
- data/ contains datasets and review groups
- personas/ contains persona files
- spec/ contains specifications
- tests/ contains validation tests
- metrics/ contains all metric files
- src/ contains executable Python scripts
- reflection/ contains the final reflection

How to Run:
1. python src/00_validate_repo.py
2. python src/02_clean.py
3. python src/run_all.py
4. Open metrics/metrics_summary.json for comparison results

# EECS4312_W26_SpecChain_218491555

## Project Overview
This repository contains my EECS 4312 course project for transforming app reviews into software requirements artifacts using manual, automated, and hybrid pipelines.

**Application studied:** MindDoc  
**Google Play URL:** https://play.google.com/store/apps/details?id=de.moodpath.android&hl=en_CA

## Dataset
- `data/reviews_raw.jsonl` contains the raw reviews collected from the Google Play Store.
- `data/reviews_clean.jsonl` contains the cleaned review dataset after preprocessing.
- Raw dataset size: 5000 reviews
- Cleaned dataset size: 4267 reviews

## Data Collection Method
The reviews were collected programmatically from the Google Play Store using the `google-play-scraper` Python package through `src/01_collect_or_import.py`.

## Current Repository Structure
- `data/` contains datasets and review grouping files
- `personas/` contains persona files
- `spec/` contains specification files
- `tests/` contains validation test files
- `metrics/` contains metric outputs
- `src/` contains Python scripts for data collection, cleaning, generation, validation, and metrics
- `reflection/` contains the final reflection

## Current Commands Used
For Task 2, the following commands were used:

```bash
python src/01_collect_or_import.py --count 5000 --lang en --country ca --sort newest
python src/02_clean.py

