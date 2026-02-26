# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This repository supports a reproducibility study of protein-ligand binding affinity prediction (PLBAP) models evaluated on the CASF-2016 benchmark. The core workflow is: for each model being audited, run the interactive wizard to produce a structured JSON report documenting paper metadata, artifact availability, and the outcome of any reproduction attempt.

## Running the Report Wizard

```bash
# Create a new report (saves to ./json_reports/<model_slug>.json)
python create_reports.py

# Save to a custom directory
python create_reports.py --out_dir my/reports/

# Resume an existing partial report
python create_reports.py --resume GIGN
```

Interactive commands available at any prompt:
- `enter` — skip (leave field as null)
- `null` / `none` — explicitly set field to null
- `1`, `2`, `3` … — pick from numbered lists
- `!undo` — undo the last saved answer
- `!quit` — save current progress and exit

## Architecture

The codebase has two files:

**`create_reports.py`** — The single interactive wizard. It walks through 7 sections in order:
1. Literature (paper metadata)
2. CASF Benchmark & Reported Metrics (benchmark setup, Pearson R, RMSE)
3. Code Repository (artifact availability flags, study fork)
4. Data Repository (separate Zenodo/Figshare links)
5. Reproducibility Outcome (status, failure modes, barriers, reproduced metrics)
6. Compute Environment (Python version, conda env, CUDA, hardware)
7. Final summary

The wizard auto-saves after every field to `json_reports/<slug>.json`. Undo is implemented via a deep-copy snapshot stack (`UndoStack`). All controlled vocabularies (status values, failure modes, barriers, target types) are defined as module-level constants at the top of the file.

**`plbap_report.schema.json`** — JSON Schema v2.1.0 defining the structure every report must conform to. The schema uses two shared `$defs`: `tristate` (`"yes"/"no"/"partial"/"unknown"/null`) and `metrics_block` (`pearson_r`, `rmse`, `rmse_unit`, `notes`). Reports are validated against this schema — `schema_version` must be the exact string `"2.1.0"`.

## Key Schema Concepts

- `barriers_to_attempt`: why a reproduction attempt was *not started* (structural absences like no public code, missing weights)
- `failure_modes`: what went wrong *during* an active attempt (runtime errors, broken dependencies, etc.)
- `target_normalized`: use `"pK_unspecified"` when the paper writes "pK" or "binding affinity" without distinguishing Kd/Ki/Ka
- `study_fork`: when changes were made to the upstream code to get it running, record the fork URL and a summary of changes here
