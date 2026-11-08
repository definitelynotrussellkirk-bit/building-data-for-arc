"""Bounded adversarial audit for the 4b326abc33f4 parametric family.

This is intentionally task-local and reusable by later reviewers.  It attacks
the smallest two-demo lesson, matched-input sampling, count boundaries, the
30x30 profile, crossed controls, and the declared semantic rivals.  It does not
replace protected-Racket qualification or owner acceptance.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import adapter
import family


HERE = Path(__file__).resolve().parent
TARGET = HERE.parents[1]


def _load_base():
    path = TARGET / "generator.py"
    spec = importlib.util.spec_from_file_location("base_4b326abc33f4", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _quadrants(grid):
    h, w = len(grid), len(grid[0])
    result = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            result.add((0 if r < h / 2 else 1, 0 if c < w / 2 else 1))
    return result


def run(seed_count: int) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 4096:
        raise ValueError("seed_count must be an integer in 1..4096")
    findings = []
    counters = {
        "seeds": seed_count,
        "minimum_lessons": 0,
        "episodes": 0,
        "labelled_pairs": 0,
        "matched_input_comparisons": 0,
        "rival_checks": 0,
        "crossed_controls": 0,
        "base_draws": 0,
    }
    side_counts = {"left": 0, "right": 0}
    geometry_signatures = set()
    seed_sequences = set()

    for seed in range(seed_count):
        episodes = {
            mode: adapter.generate(seed, {"assignment_mode": mode}, 2, 4)
            for mode in family.MODES
        }
        counters["episodes"] += len(episodes)
        counters["minimum_lessons"] += len(episodes)
        local_inputs = [pair["input"] for pair in episodes["local"]["train"] + episodes["local"]["test"]]
        cyclic_inputs = [pair["input"] for pair in episodes["cyclic_next"]["train"] + episodes["cyclic_next"]["test"]]
        counters["matched_input_comparisons"] += len(local_inputs)
        if local_inputs != cyclic_inputs:
            findings.append({"seed": seed, "kind": "setting_input_confound"})
        if len({json.dumps(grid, separators=(",", ":")) for grid in local_inputs}) != len(local_inputs):
            findings.append({"seed": seed, "kind": "duplicate_input"})

        for mode, episode in episodes.items():
            counters["labelled_pairs"] += len(episode["train"]) + len(episode["test"])
            survivors = family.setting_survivors(episode["train"])
            if survivors != [mode]:
                findings.append({"seed": seed, "mode": mode, "kind": "setting_survivors", "survivors": survivors})
            rivals = family.rival_survivors(episode["train"], mode)
            counters["rival_checks"] += len(family.RIVALS)
            if rivals:
                findings.append({"seed": seed, "mode": mode, "kind": "rival_survivors", "survivors": rivals})
            for pair in episode["train"] + episode["test"]:
                if pair["output"] != family.apply_mode(pair["input"], mode):
                    findings.append({"seed": seed, "mode": mode, "kind": "python_label_mismatch"})
                frames = family.analyze_frames(pair["input"])
                for frame in frames:
                    side_counts[frame["seed_side"]] += 1
                geometry_signatures.add(family.geometry_signature(pair["input"]))
                seed_sequences.add(family.seed_sequence(pair["input"]))

        demos = episodes["cyclic_next"]["train"]
        for index, pair in enumerate(demos):
            sides = {frame["seed_side"] for frame in family.analyze_frames(pair["input"])}
            if sides != {"left", "right"}:
                findings.append({"seed": seed, "kind": "one_side_teaching_demo", "demo": index, "sides": sorted(sides)})
        if not family.has_reading_order_confound(demos[0]["input"]):
            findings.append({"seed": seed, "kind": "missing_left_to_right_confound"})

        queries = episodes["cyclic_next"]["test"]
        if [(len(pair["input"]), len(pair["input"][0])) for pair in queries] != [
            (12, 20), (20, 16), (24, 24), (30, 30)
        ]:
            findings.append({"seed": seed, "kind": "query_profile_dimensions"})
        if not any(frame["boundary_contacts"] for frame in family.analyze_frames(queries[0]["input"])):
            findings.append({"seed": seed, "kind": "missing_boundary_query"})
        if not family.has_reading_order_confound(queries[1]["input"]):
            findings.append({"seed": seed, "kind": "missing_query_order_confound"})
        if _quadrants(queries[3]["input"]) != {(0, 0), (0, 1), (1, 0), (1, 1)}:
            findings.append({"seed": seed, "kind": "large_query_quadrant_spread"})

        controls = family.crossed_controls(seed)
        counters["crossed_controls"] += 2
        a, b = controls["same_geometry_different_intermediate"]
        if not (family.geometry_signature(a) == family.geometry_signature(b)
                and family.seed_sequence(a) != family.seed_sequence(b)
                and family.apply_mode(a, "cyclic_next") != family.apply_mode(b, "cyclic_next")):
            findings.append({"seed": seed, "kind": "same_geometry_control"})
        c, d = controls["same_intermediate_different_geometry"]
        if not (family.seed_sequence(c) == family.seed_sequence(d)
                and family.geometry_signature(c) != family.geometry_signature(d)):
            findings.append({"seed": seed, "kind": "same_intermediate_control"})

    # Exercise independent request-count boundaries without multiplying the
    # expensive semantic loop above.
    for seed in range(min(seed_count, 16)):
        for mode in family.MODES:
            for demos, queries in ((2, 1), (2, 4), (6, 1), (6, 4)):
                episode = adapter.generate(seed + 9000, {"assignment_mode": mode}, demos, queries)
                counters["episodes"] += 1
                counters["labelled_pairs"] += demos + queries
                if len(episode["train"]) != demos or len(episode["test"]) != queries:
                    findings.append({"seed": seed, "mode": mode, "kind": "count_boundary", "demos": demos, "queries": queries})

    base = _load_base()
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(min(100, seed_count)):
            state = random.getstate()
            grid = base.generate(20000 + index, index, difficulty=difficulty)
            counters["base_draws"] += 1
            if random.getstate() != state:
                findings.append({"difficulty": difficulty, "seed": index, "kind": "base_global_rng_mutation"})
            errors = base.self_check(grid, difficulty=difficulty)
            if errors:
                findings.append({"difficulty": difficulty, "seed": index, "kind": "base_self_check", "errors": errors})
            if base.rule_mirror(grid) == grid:
                findings.append({"difficulty": difficulty, "seed": index, "kind": "base_identity_output"})

    source_paths = [
        TARGET / "generator.py",
        HERE / "adapter.py",
        HERE / "family.py",
        HERE / "promotion.json",
        HERE / "canonical.rkt",
        HERE / "cyclic-next.rkt",
        HERE / "audit.py",
    ]
    return {
        "schema": "arcpuzzles-4b326abc33f4-adversarial-audit-v1",
        "status": "passed" if not findings else "failed",
        "task_id": "4b326abc33f4",
        "scope": (
            "Finite Python mirror/sampler/base audit. Protected Racket, source-bound "
            "qualification, public projection, owner acceptance and universal lesson "
            "uniqueness remain separate."
        ),
        "counters": counters,
        "coverage": {
            "seed_sides": side_counts,
            "geometry_signatures": len(geometry_signatures),
            "seed_sequences": len(seed_sequences),
            "rivals": sorted(family.RIVALS),
            "query_dimensions": [[12, 20], [20, 16], [24, 24], [30, 30]],
        },
        "findings": findings[:100],
        "finding_count": len(findings),
        "source_sha256": {path.relative_to(TARGET).as_posix(): _sha(path) for path in source_paths},
        "training_admitted": False,
        "owner_accepted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=256)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.seeds)
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "status": report["status"],
        "finding_count": report["finding_count"],
        **report["counters"],
        **{k: report["coverage"][k] for k in ("geometry_signatures", "seed_sequences")},
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
