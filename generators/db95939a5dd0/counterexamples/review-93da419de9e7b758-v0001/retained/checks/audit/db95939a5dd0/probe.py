#!/usr/bin/env python3
"""Findings-only audit: unknown overrides and one-direction-per-color rival.

Run from WORK via run_with_racket.py; --out must name a fresh directory.
Exit 1 means a completed audit reproduced a finding; 2 means execution blocked.
Canonical pairs and Racket answers are authoring evidence, never solve inputs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "db95939a5dd0"


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def parts(grid):
    """Independent row-major four-connected component and color-role reader."""
    h, w = len(grid), len(grid[0])
    bg = Counter(v for row in grid for v in row if v).most_common(1)[0][0]
    seen, components = set(), []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == bg:
                continue
            stack, cells = [(r, c)], []
            seen.add((r, c))
            while stack:
                p, q = stack.pop()
                cells.append((p, q))
                for nr, nc in ((p-1, q), (p+1, q), (p, q-1), (p, q+1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] != bg):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            colors = sorted({grid[p][q] for p, q in cells},
                            key=lambda color: min(p for p, q in cells if grid[p][q] == color))
            if len(colors) != 2:
                raise ValueError("rival domain requires two colors per compound")
            components.append((cells, colors))
    return bg, components


def transform(grid, *, global_color=False):
    bg, components = parts(grid)
    out = [[bg] * len(grid[0]) for _ in grid]
    directions = {}
    for cells, (top, bottom) in components:
        # The rival learns one direction per color from its first compound,
        # then reuses it globally even if that color takes the opposite role.
        directions.setdefault(top, -1)
        directions.setdefault(bottom, 1)
        for r, c in cells:
            color = grid[r][c]
            shift = directions[color] if global_color else (-1 if color == top else 1)
            out[r][c + shift] = color
    return out


def one_direction_per_color(grid):
    return transform(grid, global_color=True)


def differences(expected, actual):
    return [[r, c] for r, row in enumerate(expected)
            for c, value in enumerate(row) if value != actual[r][c]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("choose a fresh output directory; preserve earlier findings")
    args.out.mkdir(parents=True)
    root = find_root(__file__)
    module, source, source_hash = load_selected_generator(TASK, root=root)
    report = {"schema": "db95939a5dd0-adversarial-audit-v1", "task_id": TASK,
              "generator_sha256": source_hash, "generator_version": module.VERSION,
              "declared_rule_hash": module.RULE_HASH,
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
              "failures": [], "findings": [], "completed": False}
    inputs, identities = [], []

    def add(grid, identity):
        index = len(inputs)
        inputs.append(grid)
        identities.append({**identity, "input_index": index, "input_sha256": digest(grid),
                           "self_check": module.self_check(deepcopy(grid))})
        return index

    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    for pair in canonical:
        add(pair["input"], {"kind": "canonical", "variant": pair["variant"],
                            "split": pair["split"], "pair_index": pair["pair_index"]})

    # Nine paired coordinates independently recheck the old key-acceptance lead.
    control_records = []
    for band in ("easy", "medium", "hard"):
        for seed in range(3):
            record = {"seed": seed, "sample_index": 0, "difficulty": band}
            generated = {}
            for kind, controls in (("base", {}), ("unknown", {"typo_axis": 123}),
                                   ("known_none", {"grid_h": None})):
                call = dict(seed=seed, sample_index=0, difficulty=band, **controls)
                try:
                    grid = module.generate(**call)
                    generated[kind] = grid
                    record[kind] = {"accepted": True, "input_index": add(grid,
                                    {"kind": f"control_{kind}", "call": call})}
                except Exception as exc:
                    record[kind] = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}
            record["unknown_changed_vs_base"] = (generated.get("unknown") != generated.get("base"))
            record["known_none_changed_vs_base"] = (generated.get("known_none") != generated.get("base"))
            control_records.append(record)
    report["control_records"] = control_records

    # Hand-made lawful input: color 3 is bottom in the first compound and top
    # in the second. Its correct displacement therefore depends on compound.
    handmade = [[1] * 12 for _ in range(12)]
    for row, cols, color in ((2, (3, 4), 2), (3, (3, 4), 3),
                             (7, (7, 8), 3), (8, (7, 8), 4)):
        for col in cols:
            handmade[row][col] = color
    handmade_index = add(handmade, {"kind": "handmade_cross_role_color",
                                    "emitted_claim": False})

    # Cheap source scan selects an adversarial candidate. The retained native
    # generation below, not this mirror, adjudicates its real teaching failure.
    candidates, candidate_seed = [], None
    for seed in range(64):
        calls, mirrors_fit, valid = [], [], True
        for index in range(4):
            call = dict(seed=seed, sample_index=index, difficulty="medium")
            try:
                grid = module.generate(**call)
                errors = module.self_check(grid)
                calls.append({"call": call, "input_sha256": digest(grid), "self_check": errors})
                valid = valid and not errors
                mirrors_fit.append(one_direction_per_color(grid) == transform(grid))
            except Exception as exc:
                calls.append({"call": call, "error": f"{type(exc).__name__}: {exc}"})
                valid = False
        row = {"seed": seed, "draws": calls, "python_mirror_rival_fit": mirrors_fit,
               "candidate": valid and mirrors_fit == [True, True, True, False]}
        candidates.append(row)
        if row["candidate"]:
            candidate_seed = seed
            break
    report["candidate_scan"] = {"seed_start": 0, "maximum_seed": 63,
                                 "difficulty": "medium", "sample_indices": [0, 1, 2, 3],
                                 "stop_policy": "first mirror-selected candidate; not a frequency estimate",
                                 "records": candidates}

    episode = None
    if candidate_seed is not None:
        options = dict(seed=candidate_seed, count=1, n_train=3, n_test=1,
                       sample_index=0, difficulty="medium", allow_unapproved=True, timeout=120)
        report["native_generation_options"] = options
        try:
            episode, = Catalog(root=root).generate(TASK, **options)
            (args.out / "native-episode.json").write_text(json.dumps(episode, indent=1) + "\n")
            report["native_pair_indices"] = [add(pair["input"], {"kind": "native_episode",
                "seed": episode["seed"], "position": i,
                "sample_index": episode["sample_indices"][i], "split": "train" if i < 3 else "test"})
                for i, pair in enumerate(episode["train"] + episode["test"])]
        except Exception as exc:
            report["failures"].append({"phase": "native_generation", "error": f"{type(exc).__name__}: {exc}",
                                       "run": getattr(exc, "run", None)})
    else:
        report["findings"].append({"status": "not_reproduced", "topic": "production_lesson_ambiguity",
                                   "limit": "No candidate in the bounded source scan"})

    input_path, applied_path = args.out / "racket-inputs.json", args.out / "racket-applied.json"
    input_path.write_text(json.dumps({"inputs": inputs}) + "\n")
    argv = [sys.executable, "-m", "arcpuzzles", "apply", TASK, "--input", str(input_path),
            "--check-generator-domain", "--timeout", "120", "--out", str(applied_path)]
    process = subprocess.run(argv, text=True, capture_output=True, timeout=180)
    (args.out / "racket-apply.log").write_text(process.stdout + process.stderr)
    report["racket_command"], report["racket_exit_code"] = argv, process.returncode
    applied = json.loads(applied_path.read_text()) if applied_path.is_file() else {}
    results = applied.get("results", [])
    report["executed_rule_hash"] = applied.get("executed_rule_hash")
    report["rule_text_sha256"] = applied.get("rule_text_sha256")
    report["inputs"] = identities
    report["racket_input_count"] = len(inputs)
    report["racket_unique_inputs"] = len({digest(grid) for grid in inputs})
    report["canonical_pair_count"] = len(canonical)
    report["canonical_unique_pairs"] = len({digest(p) for p in canonical})
    report["canonical_unique_grid_pairs"] = len({digest({"input": p["input"], "output": p["output"]}) for p in canonical})
    if process.returncode or len(results) != len(inputs):
        report["failures"].append({"phase": "racket_apply", "exit_code": process.returncode})
    else:
        report["reference_checks"] = [{"input_index": i,
            "racket_error": row.get("error"), "valid_output": row.get("valid_output"),
            "matches_independent_per_compound_transform": row.get("output") == transform(inputs[i]),
            "rival_matches": row.get("output") == one_direction_per_color(inputs[i])}
            for i, row in enumerate(results)]
        report["canonical_rival_fit"] = [{"input_index": i, "split": p["split"],
            "matches_retained_label": results[i]["output"] == p["output"],
            "rival_matches": one_direction_per_color(p["input"]) == results[i]["output"]}
            for i, p in enumerate(canonical)]
        witness_indices = [handmade_index] + report.get("native_pair_indices", [])[3:]
        report["rival_witnesses"] = [{"input_index": i, "input": inputs[i],
            "racket_output": results[i]["output"], "rival_output": one_direction_per_color(inputs[i]),
            "differing_cells": differences(results[i]["output"], one_direction_per_color(inputs[i])),
            "self_check": identities[i]["self_check"]} for i in witness_indices]
        if episode is not None:
            native_indices = report["native_pair_indices"]
            fits = [one_direction_per_color(inputs[i]) == results[i]["output"] for i in native_indices]
            report["native_rival_fit"] = fits
            report["native_reference_parity"] = all(results[i]["output"] == pair["output"]
                for i, pair in zip(native_indices, episode["train"] + episode["test"]))
            if fits == [True, True, True, False]:
                report["findings"].append({"status": "reproduced", "id": "A-db-1",
                    "topic": "production_lesson_ambiguity", "seed": candidate_seed,
                    "demos": 3, "queries": 1, "sample_indices": episode["sample_indices"],
                    "rival": "one_direction_per_color", "rival_fit": fits})
    accepted = sum(row["unknown"]["accepted"] for row in control_records)
    unknown_changed = sum(row["unknown_changed_vs_base"] for row in control_records)
    none_changed = sum(row["known_none_changed_vs_base"] for row in control_records)
    if accepted:
        report["findings"].append({"status": "reproduced", "id": "A-db-2",
            "topic": "unknown_override_accepted", "denominator": len(control_records),
            "accepted": accepted, "changed": unknown_changed, "known_none_changed": none_changed,
            "prior_leads": ["review-0a0a7f531c095e30:v0001", "review-b0bc4d5df8dac99b:v0001",
                            "review-ef42e4cc11a0332d:v0001"]})
    report["source_unchanged"] = hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    report["completed"] = not report["failures"] and report["source_unchanged"]
    report["exit_code"] = (2 if not report["completed"] else
                           1 if any(f["status"] == "reproduced" for f in report["findings"]) else 0)
    (args.out / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"completed": report["completed"], "exit_code": report["exit_code"],
        "generator_sha256": source_hash, "source_scan_candidates": len(candidates),
        "racket_inputs": len(inputs), "findings": report["findings"]}))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
