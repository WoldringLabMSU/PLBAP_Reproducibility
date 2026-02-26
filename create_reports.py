#!/usr/bin/env python3
"""
new_model.py  —  Interactively create a new PLBAP v2.1.0 JSON report from scratch.

Walks through the schema section by section, prompts for each field, and saves
the result to json_reports/<model_slug>.json. Supports resuming a partially
completed entry, undoing the last answer, and skipping optional blocks entirely.

Usage:
    python new_model.py                          # saves to ./json_reports/
    python new_model.py --out_dir my/reports/    # custom output directory
    python new_model.py --resume GIGN            # resume an existing partial entry
"""

import argparse
import json
import os
import sys
import re
import textwrap
from copy import deepcopy
from datetime import datetime
from pathlib import Path

# ─── ANSI colours (identical to fill_nulls) ───────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"

def clr(text, *codes): return "".join(codes) + str(text) + RESET
def label(text):  return clr(text, CYAN)
def hint(text):   return clr(text, DIM)
def ok(text):     return clr(text, GREEN)
def warn(text):   return clr(text, YELLOW)
def err(text):    return clr(text, RED)
def bold(text):   return clr(text, BOLD)
def section_header(title, idx, total):
    bar = "═" * 54
    print(f"\n{clr(bar, BLUE)}")
    print(f"  {clr(f'SECTION {idx}/{total}', BOLD, BLUE)}  {clr(title, BOLD, WHITE)}")
    print(f"{clr(bar, BLUE)}\n")

def divider():
    print(clr("─" * 54, DIM))

def wrap(text):
    return textwrap.fill(text, width=60, initial_indent="  ", subsequent_indent="  ")


# ─── Controlled vocabularies ──────────────────────────────────────────────────

SCHEMA_VERSION = "2.1.0"

TRISTATES         = ["yes", "no", "partial", "unknown"]
STATUSES          = ["Fully reproduced", "Nearly reproduced", "Partial", "Poor",
                     "Not reproducible", "Not attempted", "Unknown"]
TIMES             = ["<2h", "2-4h", "4-6h", "6-8h", "8-12h", ">12h"]
AVAILABILITY_TYPES= ["github", "gitlab", "zenodo_code", "supplementary_only",
                     "web_server_only", "none"]
TARGET_NORMALIZED = ["pKd", "pKi", "pKa", "pK_unspecified", "delta_G", "unknown"]
FAILURE_MODES     = ["missing_weights", "missing_preprocessing_code",
                     "missing_inference_code", "missing_environment_spec",
                     "broken_dependencies", "hard_coded_paths", "runtime_error",
                     "incorrect_results", "undocumented_data_format",
                     "hardware_incompatibility", "checkpoint_ambiguity"]
BARRIERS          = ["no_public_code", "web_server_only", "supplementary_only",
                     "missing_weights", "missing_preprocessing_code",
                     "missing_inference_code", "missing_environment_spec",
                     "notebook_only", "time_limit_reached"]


# ─── Undo stack ───────────────────────────────────────────────────────────────

class UndoStack:
    def __init__(self):
        self._stack = []   # list of (key_path_str, old_value) for display

    def push(self, label, snapshot):
        self._stack.append((label, snapshot))

    def pop(self):
        if self._stack:
            return self._stack.pop()
        return None

    def __len__(self):
        return len(self._stack)


# ─── Low-level prompt helpers ─────────────────────────────────────────────────

def prompt_raw(field_name, description=None, allowed=None, type_hint="str",
               default=None, optional=True):
    """
    Single-field prompt. Returns the typed/coerced value, or SENTINEL_SKIP,
    or raises SystemExit on !quit.

    Special inputs:
      enter          → skip (leave as null) if optional=True, else re-prompt
      null / none    → explicitly set None
      !undo          → return SENTINEL_UNDO
      !quit          → raise SystemExit
    """
    print()
    if description:
        print(wrap(description))
    if allowed:
        opts = "  " + "  ".join(clr(f"[{i+1}] {v}", DIM) for i, v in enumerate(allowed))
        print(opts)
    type_label = {"str":"text","int":"integer","num":"decimal","bool":"true/false","tri":"yes/no/partial/unknown"}.get(type_hint, type_hint)
    suffix = hint(f"  type:{type_label}")
    if default is not None:
        suffix += hint(f"  default:{default!r}")
    if optional:
        if default is not None:
            suffix += hint("  [enter=keep  null=set null  !undo  !quit]")
        else:
            suffix += hint("  [enter=skip  null=set null  !undo  !quit]")
    else:
        suffix += hint("  [null=set null  !undo  !quit]")

    while True:
        try:
            raw = input(f"  {label(field_name)} > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise SystemExit(0)

        if raw in ("!quit", "!q"):
            raise SystemExit(0)
        if raw in ("!undo", "!u"):
            return SENTINEL_UNDO
        if raw.lower() in ("null", "none"):
            return None
        if raw == "" and optional:
            return SENTINEL_SKIP
        if raw == "" and not optional:
            if default is not None:
                return _coerce(str(default), type_hint)
            print(warn("  Required — please enter a value (or null to leave empty)"))
            continue

        # Numeric shortcut for allowed lists
        if allowed and raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(allowed):
                raw = allowed[idx]
            else:
                print(warn(f"  Choose 1–{len(allowed)}"))
                continue

        # Validate against allowed list (lenient for bools)
        if allowed and raw not in allowed:
            if type_hint == "bool" and raw.lower() in ("true","false","yes","no","t","f","y","n","1","0"):
                pass
            else:
                print(warn(f"  Not in allowed values. Enter number or exact string."))
                continue

        try:
            return _coerce(raw, type_hint)
        except (ValueError, TypeError) as e:
            print(err(f"  Cannot parse as {type_hint}: {e}"))


def _coerce(raw, type_hint):
    if raw is None:
        return None
    raw = str(raw).strip()
    if raw.lower() in ("null", "none", ""):
        return None
    if type_hint == "int":
        return int(raw)
    if type_hint == "num":
        return float(raw)
    if type_hint == "bool":
        return raw.lower() in ("true", "yes", "1", "t", "y")
    return raw


SENTINEL_SKIP = object()
SENTINEL_UNDO = object()


def ask_yn(question, default=None):
    """Simple yes/no gate. Returns True/False. Raises SystemExit on !quit."""
    opts = "[y/n]" if default is None else ("[Y/n]" if default else "[y/N]")
    while True:
        try:
            raw = input(f"\n  {clr('?', BOLD, YELLOW)} {question} {hint(opts)} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            raise SystemExit(0)
        if raw in ("!quit", "!q"):
            raise SystemExit(0)
        if raw in ("y", "yes"): return True
        if raw in ("n", "no"):  return False
        if raw == "" and default is not None: return default
        print(warn("  Please enter y or n"))


def multiselect(field_name, description, options):
    """
    Numbered multi-select for array fields (failure_modes, barriers_to_attempt).
    Returns a list. Enter with empty = empty list.
    """
    print()
    print(f"  {label(field_name)}")
    if description:
        print(wrap(description))
    print()
    for i, opt in enumerate(options):
        print(f"    {clr(str(i+1), CYAN)}  {opt}")
    print()
    print(hint("  Enter numbers separated by spaces/commas, or enter to leave empty."))
    print(hint("  Example: 1 3 5   or   1,3,5"))

    while True:
        try:
            raw = input(f"  {label(field_name)} > ").strip()
        except (EOFError, KeyboardInterrupt):
            raise SystemExit(0)
        if raw in ("!quit", "!q"):
            raise SystemExit(0)
        if raw in ("!undo", "!u"):
            return SENTINEL_UNDO
        if raw == "":
            return []

        # Parse numbers or direct names
        tokens = re.split(r"[\s,]+", raw)
        result = []
        bad = False
        for tok in tokens:
            if not tok:
                continue
            if tok.isdigit():
                idx = int(tok) - 1
                if 0 <= idx < len(options):
                    result.append(options[idx])
                else:
                    print(warn(f"  {tok!r} out of range (1–{len(options)})"))
                    bad = True
                    break
            elif tok in options:
                result.append(tok)
            else:
                print(warn(f"  Unknown option {tok!r}"))
                bad = True
                break
        if bad:
            continue

        # Deduplicate preserving order
        seen = set()
        result = [x for x in result if not (x in seen or seen.add(x))]
        print(f"  → {result}")
        try:
            confirm = input(hint("  Confirm? [y/n] ")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            raise SystemExit(0)
        if confirm in ("", "y", "yes"):
            return result


def field(doc, key_path, field_name, description, type_hint="str",
          allowed=None, optional=True, default=None, undo_stack=None,
          out_path=None):
    """
    Prompt for a single field, store it in doc at key_path, save, record undo.
    key_path: tuple of keys/ints to navigate to the parent dict.
    Returns True normally, False if user hit !undo (caller should handle).
    """
    # Peek at the current value so it can be shown as the default when resuming
    try:
        _parent = doc
        for k in key_path:
            _parent = _parent[k]
        current = _parent.get(field_name) if isinstance(_parent, dict) else None
    except (KeyError, TypeError):
        current = None
    effective_default = current if current is not None else default

    value = prompt_raw(field_name, description, allowed, type_hint, effective_default, optional)

    if value is SENTINEL_UNDO:
        return "undo"
    if value is SENTINEL_SKIP:
        return "skip"

    # Navigate to parent
    parent = doc
    for k in key_path:
        if parent is None:
            return "skip"
        parent = parent[k]

    old = parent.get(field_name) if isinstance(parent, dict) else None
    if isinstance(parent, dict):
        parent[field_name] = value
    if out_path:
        save(doc, out_path)
    if undo_stack is not None:
        snapshot = deepcopy(doc)
        undo_stack.push(f"{'.'.join(str(k) for k in key_path)}.{field_name}", snapshot)

    status = f"  {ok('✓')} {label(field_name)} = {clr(repr(value), WHITE)}"
    print(status)
    return "done"


def array_field(doc, key_path, field_name, description, options,
                undo_stack=None, out_path=None):
    """Prompt for an array field with multi-select UX."""
    value = multiselect(field_name, description, options)
    if value is SENTINEL_UNDO:
        return "undo"
    parent = doc
    for k in key_path:
        parent = parent[k]
    parent[field_name] = value
    if out_path:
        save(doc, out_path)
    if undo_stack is not None:
        undo_stack.push(f"{field_name}", deepcopy(doc))
    print(f"  {ok('✓')} {label(field_name)} = {clr(repr(value), WHITE)}")
    return "done"


def save(doc, path):
    Path(path).write_text(json.dumps(doc, indent=2) + "\n")


def do_undo(doc, undo_stack, out_path):
    entry = undo_stack.pop()
    if entry is None:
        print(warn("  Nothing to undo."))
        return doc
    label_str, snapshot = entry
    save(snapshot, out_path)
    print(ok(f"  Undone: {label_str}"))
    return snapshot


# ─── Template ─────────────────────────────────────────────────────────────────

def blank_template(model_name):
    return {
        "schema_version": SCHEMA_VERSION,
        "model_name": model_name,
        "literature": {
            "title": None,
            "year": None,
            "journal": None,
            "doi": None,
            "volume": None,
            "issue": None,
            "data_linked": None,
            "code_linked": None,
            "training_set": None,
            "casf_benchmark": {
                "year": None,
                "n_complexes": None,
                "target": None,
                "target_unit": None,
                "target_normalized": None,
            },
            "reported_scoring_power": {
                "pearson_r": None,
                "rmse": None,
                "rmse_unit": None,
                "notes": None,
            },
            "reported_scoring_power_md": None,
        },
        "artifacts": {
            "data_repo": None,
            "code_repo": None,
        },
        "environment": None,
        "reproducibility": {
            "status": None,
            "troubleshooting_time": None,
            "barriers_to_attempt": [],
            "failure_modes": [],
            "failure_notes": None,
            "reproduced_metrics": None,
            "checkpoint_used": None,
        },
    }


# ─── Section fillers ──────────────────────────────────────────────────────────

def run_section(title, idx, total, fields_fn, doc, undo_stack, out_path):
    """
    Run a section. fields_fn receives (doc, undo_stack, out_path) and fills fields.
    Handles undo by re-calling fields_fn from the restored snapshot.
    Returns the (possibly updated) doc.
    """
    section_header(title, idx, total)
    while True:
        result = fields_fn(doc, undo_stack, out_path)
        if result == "undo":
            doc = do_undo(doc, undo_stack, out_path)
            print(hint("  Re-entering section after undo...\n"))
            continue
        if result == "quit":
            raise SystemExit(0)
        return doc


def fill_field(doc, key_path, name, desc, type_hint="str", allowed=None,
               optional=True, default=None, undo_stack=None, out_path=None):
    """Wrapper that handles the undo return signal at call site."""
    while True:
        r = field(doc, key_path, name, desc, type_hint, allowed, optional,
                  default, undo_stack, out_path)
        if r == "undo":
            doc = do_undo(doc, undo_stack, out_path)
            print(hint("  Re-prompting after undo...\n"))
            continue
        return doc, r


# ─── The interview ────────────────────────────────────────────────────────────

N_SECTIONS = 7

def section_literature(doc, undo_stack, out_path):
    kp = ("literature",)
    for name, desc, th, allowed, opt in [
        ("title",        "Full paper title.", "str", None, False),
        ("year",         "Publication year.", "int", None, False),
        ("journal",      "Journal name.", "str", None, False),
        ("doi",          "DOI string, e.g. '10.1021/acs.jcim.x'", "str", None, True),
        ("volume",       "Journal volume.", "str", None, True),
        ("issue",        "Journal issue.", "str", None, True),
        ("data_linked",  "Are training/evaluation datasets publicly linked from the paper or repo?",
         "tri", TRISTATES, True),
        ("code_linked",  "Is source code publicly linked?", "tri", TRISTATES, True),
        ("training_set", "Training dataset, e.g. 'PDBbind v.2016 refined'.", "str", None, True),
    ]:
        doc, _ = fill_field(doc, kp, name, desc, th, allowed, opt,
                            undo_stack=undo_stack, out_path=out_path)
    return doc


def section_casf(doc, undo_stack, out_path):
    kp = ("literature", "casf_benchmark")
    for name, desc, th, allowed in [
        ("year",      "CASF benchmark year (usually 2016).", "int", None),
        ("n_complexes","Number of complexes (usually 285).", "int", None),
        ("target",    "Target label as stated in paper, e.g. 'pKd', 'pKi', 'pK', 'binding affinity'.",
         "str", None),
        ("target_unit","Unit as stated in paper, e.g. 'pK units', 'kcal/mol'.", "str", None),
        ("target_normalized",
         "Normalized target type for cross-model comparison.\n"
         "  Use 'pK_unspecified' when paper writes 'pK' or 'binding affinity' without distinguishing Kd/Ki/Ka.",
         "str", TARGET_NORMALIZED),
    ]:
        doc, _ = fill_field(doc, kp, name, desc, th, allowed,
                            undo_stack=undo_stack, out_path=out_path)

    divider()
    print(f"\n  {bold('Reported scoring power')} {hint('(crystal structures)')}\n")
    kp2 = ("literature", "reported_scoring_power")
    for name, desc, th in [
        ("pearson_r", "Pearson R (PCC) as reported in the paper.", "num"),
        ("rmse",      "RMSE as reported in the paper.", "num"),
        ("rmse_unit", "Unit for RMSE, e.g. 'pK units', 'kcal/mol'.", "str"),
        ("notes",     "Any notes on the reported metrics.", "str"),
    ]:
        doc, _ = fill_field(doc, kp2, name, desc, th, undo_stack=undo_stack, out_path=out_path)

    existing_md = doc["literature"].get("reported_scoring_power_md")
    if isinstance(existing_md, dict) or ask_yn("Did the paper also report MD-trajectory scoring power?", default=False):
        if not isinstance(doc["literature"].get("reported_scoring_power_md"), dict):
            doc["literature"]["reported_scoring_power_md"] = {
                "pearson_r": None, "rmse": None, "rmse_unit": None, "notes": None
            }
            save(doc, out_path)
        kp3 = ("literature", "reported_scoring_power_md")
        for name, desc, th in [
            ("pearson_r", "MD-ensemble PCC as reported.", "num"),
            ("rmse",      "MD-ensemble RMSE as reported.", "num"),
            ("rmse_unit", "Unit.", "str"),
            ("notes",     "Notes.", "str"),
        ]:
            doc, _ = fill_field(doc, kp3, name, desc, th, undo_stack=undo_stack, out_path=out_path)

    return doc


def section_code_repo(doc, undo_stack, out_path):
    existing_repo = doc["artifacts"].get("code_repo")
    if not isinstance(existing_repo, dict):
        if not ask_yn("Is there a public code repository for this model?", default=True):
            doc["artifacts"]["code_repo"] = None
            save(doc, out_path)
            print(hint("  code_repo set to null — skipping.\n"))
            return doc
        doc["artifacts"]["code_repo"] = {
            "availability_type": None,
            "link": None,
            "license": None,
            "last_commit_date": None,
            "has_readme": None,
            "readme_description": None,
            "install_instructions": None,
            "explicit_versions": None,
            "environment_file": None,
            "install_script": None,
            "preprocessing_scripts": None,
            "inference_scripts": None,
            "training_scripts": None,
            "pretrained_weights": None,
            "notebook": None,
            "known_issues": None,
            "study_fork": None,
        }
        save(doc, out_path)
    kp = ("artifacts", "code_repo")

    for name, desc, th, allowed, opt in [
        ("availability_type",
         "How the code is made available.",
         "str", AVAILABILITY_TYPES, False),
        ("link",             "Repository URL.", "str", None, True),
        ("license",          "License string, e.g. 'MIT', 'GPL-3.0', 'None'.", "str", None, True),
        ("last_commit_date", "ISO date of last upstream commit, e.g. '2024-05-16'.", "str", None, True),
        ("has_readme",       "Does the repo contain a README?", "bool", ["true","false"], True),
        ("readme_description","One-sentence summary of what the README says.", "str", None, True),
    ]:
        doc, _ = fill_field(doc, kp, name, desc, th, allowed, opt,
                            undo_stack=undo_stack, out_path=out_path)

    divider()
    print(f"\n  {bold('Artifact availability flags')}\n")
    for name, desc in [
        ("install_instructions",  "README includes usable installation steps."),
        ("explicit_versions",     "Dependencies are version-pinned (not just 'pip install x')."),
        ("environment_file",      "A conda env YAML or requirements.txt is provided."),
        ("install_script",        "Is there an install script?"),
        ("preprocessing_scripts", "Scripts to go from raw PDB files to model-ready inputs."),
        ("inference_scripts",     "Scripts to run the pretrained model and generate predictions."),
        ("training_scripts",      "Training scripts are provided."),
        ("pretrained_weights",    "Pretrained model checkpoint(s) are publicly available."),
        ("notebook",              "A runnable Jupyter notebook demonstrating usage is provided."),
    ]:
        doc, _ = fill_field(doc, kp, name, desc, "bool", ["true","false"],
                            undo_stack=undo_stack, out_path=out_path)

    doc, _ = fill_field(doc, kp, "known_issues",
                        "Known issues or caveats documented by authors in the README.",
                        "str", undo_stack=undo_stack, out_path=out_path)

    existing_fork = doc["artifacts"]["code_repo"].get("study_fork")
    if isinstance(existing_fork, dict) or ask_yn("Did you create a study fork of this repo?", default=False):
        if not isinstance(doc["artifacts"]["code_repo"].get("study_fork"), dict):
            doc["artifacts"]["code_repo"]["study_fork"] = {"link": None, "changes_summary": None}
            save(doc, out_path)
        kp2 = ("artifacts", "code_repo", "study_fork")
        doc, _ = fill_field(doc, kp2, "link", "URL of the study fork.", "str",
                            undo_stack=undo_stack, out_path=out_path)
        doc, _ = fill_field(doc, kp2, "changes_summary",
                            "Free-text summary of all modifications made to achieve a runnable pipeline.",
                            "str", undo_stack=undo_stack, out_path=out_path)

    return doc


def section_data_repo(doc, undo_stack, out_path):
    existing_data = doc["artifacts"].get("data_repo")
    if not isinstance(existing_data, dict):
        if not ask_yn("Is there a separate public data repository (Zenodo, Figshare, etc.)?",
                      default=False):
            doc["artifacts"]["data_repo"] = None
            save(doc, out_path)
            print(hint("  data_repo set to null — skipping.\n"))
            return doc
        doc["artifacts"]["data_repo"] = {"link": None, "doi": None, "license": None, "description": None}
        save(doc, out_path)
    kp = ("artifacts", "data_repo")
    for name, desc in [
        ("link",        "URL of the data repository."),
        ("doi",         "DOI of the data repository."),
        ("license",     "Data license, e.g. 'CC BY 4.0'."),
        ("description", "What this repository contains."),
    ]:
        doc, _ = fill_field(doc, kp, name, desc, undo_stack=undo_stack, out_path=out_path)
    return doc


def section_environment(doc, status, undo_stack, out_path):
    existing_env = doc.get("environment")
    if not isinstance(existing_env, dict):
        attempted = status not in (None, "Not attempted")
        if not attempted:
            if not ask_yn("No attempt was made — still record environment details?", default=False):
                doc["environment"] = None
                save(doc, out_path)
                print(hint("  environment set to null — skipping.\n"))
                return doc
        doc["environment"] = {
            "python_version": None,
            "conda_env_name": None,
            "conda_env_file": None,
            "cuda_toolkit":   None,
            "hardware":       None,
        }
        save(doc, out_path)
    kp = ("environment",)
    for name, desc in [
        ("python_version", "Python version, e.g. '3.9.13'."),
        ("conda_env_name", "Conda environment name."),
        ("conda_env_file", "Path to the env YAML committed in the study fork."),
        ("cuda_toolkit",   "CUDA version, e.g. '11.3'."),
        ("hardware",       "GPU/node description, e.g. 'MSU HPCC amd24-H200'."),
    ]:
        doc, _ = fill_field(doc, kp, name, desc, undo_stack=undo_stack, out_path=out_path)
    return doc


def section_reproducibility(doc, undo_stack, out_path):
    kp = ("reproducibility",)

    # status first — drives the rest of the section
    doc, _ = fill_field(doc, kp, "status",
                        "Overall reproducibility classification.",
                        "str", STATUSES, optional=False,
                        undo_stack=undo_stack, out_path=out_path)
    status = doc["reproducibility"]["status"]
    attempted = status not in (None, "Not attempted")

    if attempted:
        doc, _ = fill_field(doc, kp, "troubleshooting_time",
                            "Active troubleshooting time spent.",
                            "str", TIMES, optional=True,
                            undo_stack=undo_stack, out_path=out_path)

    divider()
    if not attempted:
        print(f"\n  {bold('Barriers to attempt')} {hint('(why was no attempt made?)')}\n")
        while True:
            result = array_field(doc, kp, "barriers_to_attempt",
                                 "Select all structural reasons an attempt was not made.",
                                 BARRIERS, undo_stack=undo_stack, out_path=out_path)
            if result == "undo":
                doc = do_undo(doc, undo_stack, out_path)
                continue
            break
    else:
        doc["reproducibility"]["barriers_to_attempt"] = []
        save(doc, out_path)

    print(f"\n  {bold('Failure modes')} {hint('(what went wrong during the attempt?)')}\n")
    while True:
        result = array_field(doc, kp, "failure_modes",
                             "Select all failure modes encountered. Leave empty if successful.",
                             FAILURE_MODES, undo_stack=undo_stack, out_path=out_path)
        if result == "undo":
            doc = do_undo(doc, undo_stack, out_path)
            continue
        break

    doc, _ = fill_field(doc, kp, "failure_notes",
                        "Free-text explanation of barriers, failure modes, or unusual circumstances.",
                        "str", undo_stack=undo_stack, out_path=out_path)

    if attempted:
        divider()
        print(f"\n  {bold('Reproduced metrics')}\n")
        existing_metrics = doc["reproducibility"].get("reproduced_metrics")
        if isinstance(existing_metrics, dict):
            has_metrics = True
        else:
            has_metrics = ask_yn("Did the pipeline produce results to compare against reported metrics?",
                                 default=True)
            if has_metrics:
                doc["reproducibility"]["reproduced_metrics"] = {
                    "pearson_r": None, "rmse": None, "rmse_unit": None, "notes": None
                }
                save(doc, out_path)
            else:
                doc["reproducibility"]["reproduced_metrics"] = None
                save(doc, out_path)
        if has_metrics:
            kp2 = ("reproducibility", "reproduced_metrics")
            for name, desc, th in [
                ("pearson_r", "Reproduced PCC.", "num"),
                ("rmse",      "Reproduced RMSE.", "num"),
                ("rmse_unit", "RMSE unit.", "str"),
                ("notes",     "Notes on reproduced metrics.", "str"),
            ]:
                doc, _ = fill_field(doc, kp2, name, desc, th,
                                    undo_stack=undo_stack, out_path=out_path)

        doc, _ = fill_field(doc, kp, "checkpoint_used",
                            "Which model checkpoint was used (if multiple were available).",
                            "str", undo_stack=undo_stack, out_path=out_path)

    return doc


def _flatten_values(obj):
    """Yield all leaf values from a nested dict/list."""
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _flatten_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _flatten_values(v)
    else:
        yield obj


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Create a new PLBAP v2.1.0 JSON report interactively.")
    ap.add_argument("--out_dir", type=Path, default=Path("json_reports"),
                    help="Output directory for JSON files (default: ./json_reports/)")
    ap.add_argument("--resume", metavar="MODEL_NAME", default=None,
                    help="Resume an existing partial report by model name or filename")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    # ── Banner ────────────────────────────────────────────────────────────────
    os.system("clear" if os.name == "posix" else "cls")
    print(clr("═" * 54, BLUE))
    print(f"""
  {clr('PLBAP New Model Report', BOLD, CYAN)}
  {hint('Create a v2.1.0 JSON report from scratch')}

  {hint('Commands during any prompt:')}
  {hint('  enter       — skip field (leave as null)')}
  {hint('  null        — explicitly set field to null')}
  {hint('  1,2,3 …     — pick from numbered lists')}
  {hint('  !undo       — undo the last saved answer')}
  {hint('  !quit       — save current progress and exit')}
""")
    print(clr("═" * 54, BLUE))

    # ── Model name / resume ───────────────────────────────────────────────────
    if args.resume:
        slug = args.resume.lower().replace(" ", "_").replace("-", "_")
        slug = slug.removesuffix(".json")
        candidates = [
            args.out_dir / f"{slug}.json",
            args.out_dir / f"{args.resume}.json",
            Path(args.resume),
        ]
        out_path = next((p for p in candidates if p.exists()), None)
        if out_path is None:
            print(err(f"\n  Could not find a report to resume for '{args.resume}'."))
            print(hint(f"  Looked in: {[str(p) for p in candidates]}\n"))
            sys.exit(1)
        doc = json.loads(out_path.read_text())
        model_name = doc.get("model_name", args.resume)
        print(f"\n  {ok('Resuming')} {bold(model_name)}  ({out_path})\n")
    else:
        print()
        try:
            model_name = input(f"  {label('model_name')} > ").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
        if not model_name:
            print(err("  Model name is required."))
            sys.exit(1)

        slug = model_name.lower().replace(" ", "_").replace("-", "_")
        out_path = args.out_dir / f"{slug}.json"

        if out_path.exists():
            if ask_yn(f"  '{out_path}' already exists. Resume it?", default=True):
                doc = json.loads(out_path.read_text())
                print(ok(f"  Loaded existing report for {model_name}."))
            else:
                doc = blank_template(model_name)
                save(doc, out_path)
                print(ok(f"  Starting fresh: {out_path}"))
        else:
            doc = blank_template(model_name)
            save(doc, out_path)
            print(ok(f"  Created: {out_path}"))

    undo_stack = UndoStack()

    # ── Sections ──────────────────────────────────────────────────────────────
    try:
        # 1 — Literature
        doc = run_section("Literature", 1, N_SECTIONS,
                          lambda d, u, p: section_literature(d, u, p),
                          doc, undo_stack, out_path)

        # 2 — CASF benchmark + reported metrics
        doc = run_section("CASF Benchmark & Reported Metrics", 2, N_SECTIONS,
                          lambda d, u, p: section_casf(d, u, p),
                          doc, undo_stack, out_path)

        # 3 — Code repo
        doc = run_section("Code Repository", 3, N_SECTIONS,
                          lambda d, u, p: section_code_repo(d, u, p),
                          doc, undo_stack, out_path)

        # 4 — Data repo
        doc = run_section("Data Repository", 4, N_SECTIONS,
                          lambda d, u, p: section_data_repo(d, u, p),
                          doc, undo_stack, out_path)

        # 5 — Reproducibility (status first — needed for env section)
        doc = run_section("Reproducibility Outcome", 5, N_SECTIONS,
                          lambda d, u, p: section_reproducibility(d, u, p),
                          doc, undo_stack, out_path)

        # 6 — Environment (conditional on status)
        status = doc["reproducibility"].get("status")
        doc = run_section("Compute Environment", 6, N_SECTIONS,
                          lambda d, u, p: section_environment(d, status, u, p),
                          doc, undo_stack, out_path)

    except SystemExit:
        pass  # !quit or Ctrl-C — fall through to summary

    # ── Final summary ─────────────────────────────────────────────────────────
    doc = json.loads(out_path.read_text())   # reload final saved state

    null_count = sum(1 for v in _flatten_values(doc) if v is None)

    print()
    print(clr("═" * 54, BLUE))
    print(f"""
  {ok('Report saved')}  {clr(str(out_path), WHITE)}

  {label('Model:')}         {doc.get('model_name')}
  {label('Status:')}        {(doc.get('reproducibility') or {}).get('status') or hint('(not set)')}
  {label('Null fields:')}   {null_count}  {hint('← run fill_nulls.py to fill remaining') if null_count else ok('(complete!)')}
""")
    print(clr("═" * 54, BLUE))
    print()
    if null_count:
        print(hint(f"  python fill_nulls.py --file {out_path}\n"))


if __name__ == "__main__":
    main()
