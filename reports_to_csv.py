"""
Convert all json_reports/*.json into a single CSV.

Controlled-vocabulary arrays (barriers_to_attempt, failure_modes) are
expanded into one boolean column each, named:
  barrier__<tag>
  failure__<tag>

All other nested fields are flattened with double-underscore separators.
"""

import csv
import json
import sys
from pathlib import Path

# ── Controlled vocabularies (must match schema) ───────────────────────────────

BARRIERS = [
    "no_public_code",
    "web_server_only",
    "supplementary_only",
    "missing_weights",
    "missing_preprocessing_code",
    "missing_inference_code",
    "missing_environment_spec",
    "notebook_only",
    "time_limit_reached",
]

FAILURE_MODES = [
    "missing_weights",
    "missing_preprocessing_code",
    "missing_inference_code",
    "missing_environment_spec",
    "broken_dependencies",
    "hard_coded_paths",
    "runtime_error",
    "incorrect_results",
    "undocumented_data_format",
    "hardware_incompatibility",
    "checkpoint_ambiguity",
]

# ── Column order ──────────────────────────────────────────────────────────────

COLUMNS = (
    # identity
    ["model_name"]

    # literature
    + [
        "lit__title",
        "lit__year",
        "lit__journal",
        "lit__doi",
        "lit__volume",
        "lit__issue",
        "lit__data_linked",
        "lit__code_linked",
        "lit__training_set",
    ]

    # casf benchmark
    + [
        "casf__year",
        "casf__n_complexes",
        "casf__target",
        "casf__target_unit",
        "casf__target_normalized",
    ]

    # reported metrics (crystal)
    + [
        "reported__pearson_r",
    ]

    # code repo
    + [
        "availability_type",
        "link",
        "license",
        "last_commit_date",
        "has_readme",
        "install_instructions",
        "explicit_versions",
        "environment_file",
        "install_script",
        "preprocessing_scripts",
        "inference_scripts",
        "training_scripts",
        "pretrained_weights",
        "notebook",
        "example_input_data",
        "example_intermediate_data",
        "example_output_predictions",
        "study_fork__link",
        "study_fork__changes_summary",
    ]

    # data repo
    + [
        "data_repo__link",
        "data_repo__doi",
        "data_repo__license",
        "data_repo__description",
    ]

    # environment
    + [
        "env__python_version",
        "env__conda_env_name",
        "env__conda_env_file",
        "env__cuda_toolkit",
        "env__hardware",
    ]

    # reproducibility
    + [
        "repro__status",
        "repro__troubleshooting_time",
        "repro__failure_notes",
        "repro__checkpoint_used",
        "repro__pearson_r",
        "repro__notes",
    ]

    # barriers (one bool column each)
    + [f"barrier__{b}" for b in BARRIERS]

    # failure modes (one bool column each)
    + [f"failure__{f}" for f in FAILURE_MODES]
)


# ── Extraction helpers ────────────────────────────────────────────────────────

def g(obj, *keys, default=None):
    """Safe nested get."""
    for k in keys:
        if obj is None or not isinstance(obj, dict):
            return default
        obj = obj.get(k, default)
    return obj


def extract_row(d: dict) -> dict:
    lit   = d.get("literature") or {}
    casf  = lit.get("casf_benchmark") or {}
    rsp   = lit.get("reported_scoring_power") or {}
    art   = d.get("artifacts") or {}
    cr    = art.get("code_repo") or {}
    sf    = cr.get("study_fork") or {}
    dr    = art.get("data_repo") or {}
    env   = d.get("environment") or {}
    rep   = d.get("reproducibility") or {}
    rm    = rep.get("reproduced_metrics") or {}

    barriers = set(rep.get("barriers_to_attempt") or [])
    failures = set(rep.get("failure_modes") or [])

    row = {
        "model_name": d.get("model_name"),

        "lit__title":         lit.get("title"),
        "lit__year":          lit.get("year"),
        "lit__journal":       lit.get("journal"),
        "lit__doi":           lit.get("doi"),
        "lit__volume":        lit.get("volume"),
        "lit__issue":         lit.get("issue"),
        "lit__data_linked":   lit.get("data_linked"),
        "lit__code_linked":   lit.get("code_linked"),
        "lit__training_set":  lit.get("training_set"),

        "casf__year":               casf.get("year"),
        "casf__n_complexes":        casf.get("n_complexes"),
        "casf__target":             casf.get("target"),
        "casf__target_unit":        casf.get("target_unit"),
        "casf__target_normalized":  casf.get("target_normalized"),

        "reported__pearson_r": rsp.get("pearson_r"),

        "availability_type":         cr.get("availability_type"),
        "link":                      cr.get("link"),
        "license":                   cr.get("license"),
        "last_commit_date":          cr.get("last_commit_date"),
        "has_readme":                cr.get("has_readme"),
        "install_instructions":      cr.get("install_instructions"),
        "explicit_versions":         cr.get("explicit_versions"),
        "environment_file":          cr.get("environment_file"),
        "install_script":            cr.get("install_script"),
        "preprocessing_scripts":     cr.get("preprocessing_scripts"),
        "inference_scripts":         cr.get("inference_scripts"),
        "training_scripts":          cr.get("training_scripts"),
        "pretrained_weights":        cr.get("pretrained_weights"),
        "notebook":                  cr.get("notebook"),
        "example_input_data":        cr.get("example_input_data"),
        "example_intermediate_data": cr.get("example_intermediate_data"),
        "example_output_predictions":cr.get("example_output_predictions"),
        "study_fork__link":          sf.get("link"),
        "study_fork__changes_summary": sf.get("changes_summary"),

        "data_repo__link":        dr.get("link"),
        "data_repo__doi":         dr.get("doi"),
        "data_repo__license":     dr.get("license"),
        "data_repo__description": dr.get("description"),

        "env__python_version":  env.get("python_version"),
        "env__conda_env_name":  env.get("conda_env_name"),
        "env__conda_env_file":  env.get("conda_env_file"),
        "env__cuda_toolkit":    env.get("cuda_toolkit"),
        "env__hardware":        env.get("hardware"),

        "repro__status":               rep.get("status"),
        "repro__troubleshooting_time": rep.get("troubleshooting_time"),
        "repro__failure_notes":        rep.get("failure_notes"),
        "repro__checkpoint_used":      rep.get("checkpoint_used"),
        "repro__pearson_r":            rm.get("pearson_r"),
        "repro__notes":                rm.get("notes"),
    }

    for b in BARRIERS:
        row[f"barrier__{b}"] = b in barriers

    for f in FAILURE_MODES:
        row[f"failure__{f}"] = f in failures

    return row


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--in_dir", default="json_reports",
        help="Directory containing *.json report files (default: json_reports)"
    )
    parser.add_argument(
        "--out", default="plbap_reports.csv",
        help="Output CSV path (default: plbap_reports.csv)"
    )
    args = parser.parse_args()

    in_dir = Path(args.in_dir)
    json_files = sorted(in_dir.glob("*.json"))
    if not json_files:
        sys.exit(f"No JSON files found in {in_dir}")

    rows = []
    for path in json_files:
        try:
            with path.open() as fh:
                data = json.load(fh)
            rows.append(extract_row(data))
        except Exception as exc:
            print(f"WARNING: skipping {path.name}: {exc}", file=sys.stderr)

    # Sort by model name
    rows.sort(key=lambda r: (r.get("model_name") or "").lower())

    out_path = Path(args.out)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows → {out_path}")


if __name__ == "__main__":
    main()
