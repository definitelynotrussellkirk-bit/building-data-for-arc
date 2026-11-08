#!/usr/bin/env python3
"""Bounded, source-bound findings-only audit; labels use the public CLI.

Run from the packet's outer root:
  WORK/.venv/bin/python3 WORK/checks/audit/a674532f50ab/reproduce.py --out WORK/checks/audit/a674532f50ab/replay

The output directory must not already contain input.json or racket.json.
No selected generator, rule, tests or notes are modified.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
TASK = "a674532f50ab"
EXPECTED_SOURCE = "82228c185228ae9e291d7bd26681bbf1ae951a3afaf7a9d78bfbe0cfcf3f2c81"
SEED = 67453250


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(grid):
    """Color-renaming-invariant equality pattern, in row-major order."""
    seen = {}
    result = []
    for row in grid:
        for color in row:
            if color not in seen:
                seen[color] = len(seen)
            result.append(seen[color])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    outer = Path.cwd().resolve()
    repo = outer / "WORK/repo"
    if not (outer / "review.py").is_file() or not repo.is_dir():
        parser.error("Run from the outer packet root containing review.py and WORK/repo")
    out = args.out.resolve()
    allowed = (outer / "WORK/checks/audit" / TASK).resolve()
    if not out.is_relative_to(allowed):
        parser.error("This audit only writes beneath WORK/checks/audit/a674532f50ab")
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in ("input.json", "racket.json")):
        parser.error("Use a fresh --out directory; existing witnesses are retained")
    sys.path.insert(0, str(repo / "shared/runtime"))
    from reviewer_support import canonical_pairs, find_root, load_selected_generator
    root = find_root(__file__)
    module, source, source_hash = load_selected_generator(TASK, root=root)
    if source_hash != EXPECTED_SOURCE:
        raise RuntimeError(f"Source changed: expected {EXPECTED_SOURCE}, got {source_hash}")
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    cases = []
    generation_failures = []
    for pair in pairs:
        cases.append({"kind": "canonical", "variant": pair["variant"],
                      "split": pair["split"], "pair_index": pair["pair_index"],
                      "input": pair["input"], "canonical_output": pair["output"],
                      "seed": None, "sample_index": None, "overrides": {}})
    for index in range(48):
        grid = module.generate(SEED, index)
        cases.append({"kind": "default_generated", "input": grid,
                      "seed": SEED, "sample_index": index, "overrides": {}})
    for kind in module.TR_CORNER_KINDS:
        overrides = {"grid_h": 9, "grid_w": 9, "texture": "noise", "tr_corner_kind": kind}
        try:
            grid = module.generate(SEED, 100, **overrides)
        except Exception as exc:
            generation_failures.append({"kind": "corner_override", "corner_kind": kind,
                                        "seed": SEED, "sample_index": 100,
                                        "overrides": overrides, "exception_type": type(exc).__name__,
                                        "exception": str(exc)})
            continue
        cases.append({"kind": "corner_override", "corner_kind": kind,
                      "input": grid, "seed": SEED, "sample_index": 100, "overrides": overrides})
    for texture in module.DEGENERATE_TEXTURES:
        overrides = {"grid_h": 9, "grid_w": 9, "texture": texture}
        cases.append({"kind": "degenerate_override", "texture": texture,
                      "input": module.generate(SEED, 101, **overrides),
                      "seed": SEED, "sample_index": 101, "overrides": overrides})
    cases.append({"kind": "manual_three_color_witness", "seed": None,
                  "sample_index": None, "overrides": {},
                  "input": [[1, 2, 3], [1, 2, 3], [1, 2, 3], [0, 0, 0]]})
    assert 1 <= len(cases) <= 64
    for index, case in enumerate(cases):
        case["input_index"] = index
        case["self_check"] = module.self_check(case["input"])
    write_json(out / "cases.json", cases)
    write_json(out / "generation_failures.json", generation_failures)
    write_json(out / "input.json", [case["input"] for case in cases])
    rule = repo / "shared/data/base/solutions/training/5bd6f4ac__a674532f50ab.json"
    rule_data = json.loads(rule.read_text(encoding="utf-8"))
    rule_text = rule_data["racket_target"]["target_code"]
    provenance = {
        "task_id": TASK, "source_path": str(source.relative_to(repo)),
        "generator_sha256": source_hash, "generator_version": module.VERSION,
        "archival_rule_path": str(rule.relative_to(repo)),
        "archival_rule_file_sha256": digest(rule),
        "archival_rule_exact_text_sha256": hashlib.sha256(rule_text.encode()).hexdigest(),
        "archival_rule_text": rule_text,
        "default_seed": SEED, "default_sample_indices": list(range(48)),
        "case_count": len(cases),
        "review_index_exists": (source.parent / "evidence/review_index.json").is_file(),
        "focused_test_paths": sorted(str(p.relative_to(repo)) for p in (source.parent / "tests").glob("test*.py")),
        "notes_sha256": digest(source.parent / "notes.md"),
        "associated_notes_size_bytes": (source.parent / "evidence/associated_notes.jsonl").stat().st_size,
    }
    write_json(out / "provenance.json", provenance)
    input_relative = os.path.relpath(out / "input.json", repo)
    output_relative = os.path.relpath(out / "racket.json", repo)
    argv = ["WORK/.venv/bin/python3", "review.py", "run", "../.venv/bin/python3",
            "-m", "arcpuzzles", "apply", TASK, "--input", input_relative,
            "--check-generator-domain", "--out", output_relative]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    result = subprocess.run(argv, cwd=outer, env=env, capture_output=True, text=True)
    (out / "apply.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (out / "apply.stderr.txt").write_text(result.stderr, encoding="utf-8")
    commands_path = out / "commands.json"
    commands = json.loads(commands_path.read_text()) if commands_path.is_file() else []
    commands.append({"argv": argv, "cwd": str(outer), "effective_payload_cwd": str(repo),
                 "environment_override": {"PYTHONDONTWRITEBYTECODE": "1"},
                 "exit_code": result.returncode, "duration_seconds": round(time.monotonic() - started, 3),
                 "stdout_path": "apply.stdout.txt", "stderr_path": "apply.stderr.txt"})
    write_json(out / "commands.json", commands)
    if not (out / "racket.json").is_file():
        print(json.dumps({"apply_exit_code": result.returncode, "receipt_missing": True}))
        return 1
    receipt = json.loads((out / "racket.json").read_text(encoding="utf-8"))
    results = receipt["results"]
    if len(results) != len(cases):
        raise RuntimeError("Reference result count does not match cases")
    templates = {}
    for case, row in zip(cases, results):
        if row.get("output") is not None and case["kind"] == "corner_override":
            templates[case["corner_kind"]] = signature(row["output"])
    default_signatures = [templates[name] for name in module.HELPFUL_CORNER_KINDS]
    assessed = []
    for case, row in zip(cases, results):
        output = row.get("output")
        record = {"input_index": case["input_index"], "kind": case["kind"],
                  "seed": case["seed"], "sample_index": case["sample_index"],
                  "overrides": case["overrides"], "self_check": case["self_check"],
                  "racket_error": row.get("error"), "racket_output": output}
        if output is not None:
            sig = signature(output)
            record.update({"output_signature": sig, "distinct_output_colors": len(set(sig)),
                           "matches_default_template": sig in default_signatures})
        if case["kind"] == "canonical":
            record.update({"canonical_pair": {k: case[k] for k in ("variant", "split", "pair_index")},
                           "matches_canonical_label": output == case["canonical_output"]})
        assessed.append(record)
    canonical = [row for row in assessed if row["kind"] == "canonical"]
    defaults = [row for row in assessed if row["kind"] == "default_generated"]
    summary = {
        "task_id": TASK, "generator_sha256": source_hash,
        "apply_exit_code": result.returncode,
        "source_unchanged": digest(source) == source_hash,
        "case_count": len(cases), "racket_errors": sum(row["racket_error"] is not None for row in assessed),
        "default_template_signatures": {name: templates[name] for name in module.HELPFUL_CORNER_KINDS},
        "default_generated_count": len(defaults),
        "default_generated_matching_template_count": sum(row["matches_default_template"] for row in defaults),
        "canonical_count": len(canonical),
        "canonical_labels_matched": sum(row["matches_canonical_label"] for row in canonical),
        "canonical_matching_default_template_count": sum(row["matches_default_template"] for row in canonical),
        "canonical_distinct_output_colors": [row["distinct_output_colors"] for row in canonical],
        "generated_self_check_failures": [row for row in assessed if row["kind"] != "canonical" and row["self_check"]],
        "generation_failures": generation_failures,
        "reference_binding": {key: receipt.get(key) for key in (
            "generator_sha256", "catalog_rule_hash", "executed_rule_hash", "rule_hash_matches_catalog", "rule_text_sha256")},
        "all_cases": assessed,
    }
    write_json(out / "analysis.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "all_cases"}, indent=2))
    # Reporting a found issue is a successful audit execution. Retain the CLI's
    # result independently; do not turn a domain rejection into a passing claim.
    return 0 if summary["source_unchanged"] and len(results) == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
