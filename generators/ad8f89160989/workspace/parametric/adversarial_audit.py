#!/usr/bin/env python3
"""Bounded adversarial audit for the overlap-count parametric family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import find_root, public_challenge_bytes

TASK_ID = "ad8f89160989"
HERE = Path(__file__).resolve().parent


def load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_ad8f89160989_audit_prototype", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def opposite_only(module, value):
    source = module._grid(value)
    counts = module.coverage_counts(source)
    output = module._render(source, counts, "union")
    height, width = len(source), len(source[0])
    for r in range(height):
        for c in range(width):
            if source[r][c] != 0:
                continue
            north = r > 0 and source[r - 1][c] != 0
            south = r + 1 < height and source[r + 1][c] != 0
            west = c > 0 and source[r][c - 1] != 0
            east = c + 1 < width and source[r][c + 1] != 0
            if (north and south) or (west and east):
                output[r][c] = 1
    return output


def mixed_axis_only(module, value):
    source = module._grid(value)
    counts = module.coverage_counts(source)
    output = module._render(source, counts, "union")
    height, width = len(source), len(source[0])
    for r in range(height):
        for c in range(width):
            if source[r][c] != 0:
                continue
            vertical = (r > 0 and source[r - 1][c] != 0) or (r + 1 < height and source[r + 1][c] != 0)
            horizontal = (c > 0 and source[r][c - 1] != 0) or (c + 1 < width and source[r][c + 1] != 0)
            if vertical and horizontal:
                output[r][c] = 1
    return output


def maximum_only(module, value):
    source = module._grid(value)
    counts = module.coverage_counts(source)
    maximum = max(max(row) for row in counts)
    output = module._render(source, counts, "union")
    for r, row in enumerate(counts):
        for c, count in enumerate(row):
            if source[r][c] == 0 and count >= 2 and count == maximum:
                output[r][c] = 1
    return output


def color_pair_only(module, value):
    """Wrong shortcut: highlight overlap only when adjacent colors differ."""
    source = module._grid(value)
    counts = module.coverage_counts(source)
    output = module._render(source, counts, "union")
    height, width = len(source), len(source[0])
    for r, row in enumerate(counts):
        for c, count in enumerate(row):
            if source[r][c] != 0 or count < 2:
                continue
            colors = {
                source[r + dr][c + dc]
                for dr, dc in module.DIRS4
                if 0 <= r + dr < height and 0 <= c + dc < width and source[r + dr][c + dc] != 0
            }
            if len(colors) >= 2:
                output[r][c] = 1
    return output


def rival_survivors(module, episode):
    selected = episode["settings"]["coverage_mode"]
    rivals = {
        "union": lambda value: module.apply_python(value, {"coverage_mode": "union"}),
        "overlap_highlight": lambda value: module.apply_python(value, {"coverage_mode": "overlap_highlight"}),
        "binary_intermediate": module.apply_binary_intermediate,
        "opposite_only": lambda value: opposite_only(module, value),
        "mixed_axis_only": lambda value: mixed_axis_only(module, value),
        "maximum_only": lambda value: maximum_only(module, value),
        "color_pair_only": lambda value: color_pair_only(module, value),
        "all_halo_blue": lambda value: module._rival_output(value, "all_halo_blue"),
        "exactly_two": lambda value: module._rival_output(value, "exactly_two"),
        "at_least_three": lambda value: module._rival_output(value, "at_least_three"),
        "diagonal_overlap": lambda value: module._rival_output(value, "diagonal_overlap"),
        "fixed_center": lambda value: module._rival_output(value, "fixed_center"),
    }
    survivors = []
    for name, predict in rivals.items():
        if all(predict(pair["input"]) == pair["output"] for pair in episode["train"]):
            survivors.append(name)
    # Binary coverage is behaviorally identical to canonical union, so it is a
    # causal ablation only for the alternative rather than a distinct union rule.
    expected = ["union", "binary_intermediate"] if selected == "union" else ["overlap_highlight"]
    return survivors, expected


def malformed_checks(module, episode):
    checks = {}
    duplicate = deepcopy(episode)
    duplicate["test"][0]["input"] = deepcopy(duplicate["train"][0]["input"])
    duplicate["test"][0]["output"] = module.apply_python(duplicate["test"][0]["input"], duplicate["settings"])
    checks["duplicate_input_rejected"] = any("duplicates" in error for error in module.episode_errors(duplicate))

    wrong = deepcopy(episode)
    wrong["train"][0]["output"][0][0] = (wrong["train"][0]["output"][0][0] + 1) % 10
    checks["wrong_label_rejected"] = any("does not match" in error for error in module.episode_errors(wrong))

    boolean = deepcopy(episode)
    boolean["train"][0]["input"][0][0] = True
    checks["boolean_cell_rejected"] = any("invalid input" in error for error in module.episode_errors(boolean))

    missing = deepcopy(episode)
    del missing["train"][0]["output"]
    checks["missing_output_rejected"] = any("exactly input and output" in error for error in module.episode_errors(missing))

    forged = deepcopy(episode)
    forged["program"] += "\n; forged"
    checks["forged_program_rejected"] = any("program" in error for error in module.episode_errors(forged))
    return checks


def audit(output: Path, seeds: int) -> dict:
    module = load_prototype()
    settings = tuple(module.SETTINGS)
    failures = []
    episodes_checked = 0
    pairs_checked = 0
    rival_records = []
    first_turn_records = []
    source_hash = hashlib.sha256((HERE / "prototype.py").read_bytes()).hexdigest()

    global_state = random.getstate()
    for seed in range(seeds):
        built = [module.generate_episode(seed, setting, demos=3, queries=4) for setting in settings]
        episodes_checked += len(built)
        pairs_checked += sum(len(ep["train"]) + len(ep["test"]) for ep in built)
        left_inputs = [pair["input"] for pair in [*built[0]["train"], *built[0]["test"]]]
        right_inputs = [pair["input"] for pair in [*built[1]["train"], *built[1]["test"]]]
        if left_inputs != right_inputs:
            failures.append({"seed": seed, "kind": "setting_leaks_into_inputs"})
        for episode in built:
            errors = module.episode_errors(episode)
            if errors:
                failures.append({"seed": seed, "kind": "episode_errors", "errors": errors})
            survivors, expected = rival_survivors(module, episode)
            rival_records.append({"seed": seed, "mode": episode["settings"]["coverage_mode"], "survivors": survivors})
            if survivors != expected:
                failures.append({"seed": seed, "kind": "rival_survivors", "mode": episode["settings"]["coverage_mode"], "observed": survivors, "expected": expected})
            histograms = [module.coverage_histogram(pair["input"]) for pair in episode["train"]]
            for required in ("2", "3", "4"):
                if not any(histogram.get(required, 0) for histogram in histograms):
                    failures.append({"seed": seed, "kind": "missing_teaching_coverage", "coverage": required})
            all_inputs = [pair["input"] for pair in [*episode["train"], *episode["test"]]]
            if len({json.dumps(value, separators=(",", ":")) for value in all_inputs}) != len(all_inputs):
                failures.append({"seed": seed, "kind": "duplicate_input"})
            if not any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30 for pair in episode["test"]):
                failures.append({"seed": seed, "kind": "missing_30x30_query"})
            for pair in [*episode["train"], *episode["test"]]:
                counts = module.coverage_counts(pair["input"])
                expected_blue = {
                    (r, c)
                    for r, row in enumerate(counts)
                    for c, count in enumerate(row)
                    if count >= 2 and pair["input"][r][c] == 0
                }
                actual_blue = {
                    (r, c)
                    for r, row in enumerate(pair["output"])
                    for c, value in enumerate(row)
                    if value == 1
                }
                if episode["settings"]["coverage_mode"] == "overlap_highlight" and actual_blue != expected_blue:
                    failures.append({"seed": seed, "kind": "wrong_blue_mask"})
                if episode["settings"]["coverage_mode"] == "union" and actual_blue:
                    failures.append({"seed": seed, "kind": "canonical_blue_leak"})

        one = module.generate_episode(seed, settings[1], demos=3, queries=1)
        four = built[1]
        one_bytes = public_challenge_bytes(module.public_turn(one, 0))
        four_bytes = public_challenge_bytes(module.public_turn(four, 0))
        first_turn_records.append({"seed": seed, "sha256": hashlib.sha256(four_bytes).hexdigest()})
        if one_bytes != four_bytes:
            failures.append({"seed": seed, "kind": "first_turn_prefix_drift"})
        if any(token in four_bytes for token in (b"coverage_mode", b"program", b"answer", b"source_index", b"query_count")):
            failures.append({"seed": seed, "kind": "private_public_leak"})

    if random.getstate() != global_state:
        failures.append({"kind": "global_random_state_changed"})

    boundary = []
    for seed in range(min(16, seeds)):
        for demos, queries in ((3, 1), (6, 8)):
            episode = module.generate_episode(10_000 + seed, settings[1], demos=demos, queries=queries)
            boundary.append({"seed": 10_000 + seed, "demos": demos, "queries": queries, "pairs": demos + queries})
            if len(episode["train"]) != demos or len(episode["test"]) != queries:
                failures.append({"seed": seed, "kind": "count_boundary"})

    control = module.crossed_controls()
    if not all(control.values()):
        failures.append({"kind": "crossed_control", "observed": control})
    reference = module.generate_episode(424242, settings[1], demos=3, queries=4)
    malformed = malformed_checks(module, reference)
    if not all(malformed.values()):
        failures.append({"kind": "malformed_rejection", "observed": malformed})

    report = {
        "schema": "ad8f89160989-adversarial-audit-v1",
        "task_id": TASK_ID,
        "prototype_source_sha256": source_hash,
        "seed_count": seeds,
        "episodes_checked": episodes_checked,
        "labeled_pairs_checked": pairs_checked,
        "boundary_episodes": len(boundary),
        "crossed_controls": control,
        "malformed_checks": malformed,
        "rival_bank": [
            "declared settings", "binary intermediate", "opposite-only", "mixed-axis-only",
            "maximum-only", "color-pair-only", "all-halo-blue", "exactly-two",
            "at-least-three", "diagonal-overlap", "fixed-center",
        ],
        "rival_records_sha256": hashlib.sha256(raw(rival_records)).hexdigest(),
        "first_turn_records_sha256": hashlib.sha256(raw(first_turn_records)).hexdigest(),
        "failures": failures,
        "passed": not failures,
        "limits": "Finite declared rivals and bounded fresh seeds; not a proof of universal lesson uniqueness or learning benefit.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=64)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 1000:
        raise ValueError("seeds must be in 1..1000")
    report = audit(args.out, args.seeds)
    print(json.dumps({k: report[k] for k in ("passed", "seed_count", "episodes_checked", "labeled_pairs_checked", "failures")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
