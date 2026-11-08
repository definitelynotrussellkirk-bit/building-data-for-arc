#!/usr/bin/env python3
"""Proposed episode-wide endpoint threshold; all labels execute in Racket.

This authoring prototype is separate from the selected generator and approval.
Its expanded input grammar permits incomplete boundary marker pairs, which are
inactive at the canonical threshold and active at the alternative threshold.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import sys

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "832404dc8a5c"
PROTOTYPE_VERSION = "1.0.0"
DEFAULT_THRESHOLD = 2
THRESHOLDS = (1, 2)
PROFILES = ("rows", "columns", "mixed", "mixed")
PARAMETER_SPEC = {
    "endpoint_threshold": {
        "allowed": list(THRESHOLDS),
        "default": DEFAULT_THRESHOLD,
        "meaning": "minimum number of opposing boundary 4 markers activating a row or column",
        "scope": "one choice for all demonstrations and the query in an episode",
    }
}
LIMITATIONS = [
    "Proposed prototype only; canonical generator behavior and approval are unchanged.",
    "Single boundary markers deliberately extend the canonical input grammar.",
    "Only endpoint_threshold 1 and 2 are declared parameter rivals; this is finite evidence, not universal identifiability.",
    "The retained episodes cover three demonstration profiles and one mixed query, not the full possible input space.",
]


def sha256(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_rule(root=None):
    root = find_root(__file__) if root is None else Path(root)
    with canonical_path(root).open(encoding="utf-8") as handle:
        programs = {
            row["program_solution"]
            for line in handle if line.strip()
            for row in [json.loads(line)] if row.get("task_id") == TASK_ID
        }
    if len(programs) != 1:
        raise ValueError("prototype requires exactly one canonical program")
    return programs.pop()


def select_threshold(seed, endpoint_threshold=DEFAULT_THRESHOLD):
    """Select once, using a stream independent of every input draw."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer")
    if endpoint_threshold == "sample":
        key = f"{TASK_ID}:endpoint_threshold:{PROTOTYPE_VERSION}:{seed}"
        return THRESHOLDS[hashlib.sha256(key.encode()).digest()[0] % len(THRESHOLDS)]
    if type(endpoint_threshold) is not int or endpoint_threshold not in THRESHOLDS:
        raise ValueError("endpoint_threshold must be integer 1 or 2, or 'sample'")
    return endpoint_threshold


def render_program(endpoint_threshold=DEFAULT_THRESHOLD, *, root=None):
    """Keep default canonical bytes; change only the two lane predicates for 1."""
    threshold = select_threshold(0, endpoint_threshold)
    source = canonical_rule(root)
    if threshold == DEFAULT_THRESHOLD:
        return source
    changes = {
        "(and (= 4 (at g r 0)) (= 4 (at g r (- w 1))))":
            "(>= (+ (if (= 4 (at g r 0)) 1 0) (if (= 4 (at g r (- w 1))) 1 0)) 1)",
        "(and (= 4 (at g 0 c)) (= 4 (at g (- h 1) c)))":
            "(>= (+ (if (= 4 (at g 0 c)) 1 0) (if (= 4 (at g (- h 1) c)) 1 0)) 1)",
    }
    for old, new in changes.items():
        if source.count(old) != 1:
            raise ValueError("canonical lane predicate changed; review the proposed mutation")
        source = source.replace(old, new)
    return source


def executed_expression(program):
    source = program.strip()
    if not source.startswith("(rule! (lambda (g)") or not source.endswith(")"):
        raise ValueError("expected this task's rule! wrapper around a grid callable")
    return source[len("(rule!"):-1].strip()


def execute_program(bridge, program, grid):
    """Use the public bridge; remove only the host registration marker."""
    bridge.define_grid("g", normalize_grid(grid))
    return normalize_grid(bridge.eval_text(f"({executed_expression(program)} g)"))


def validate_input(grid):
    try:
        normalized = normalize_grid(grid)
    except (ValueError, TypeError) as error:
        return [str(error)]
    h, w = len(normalized), len(normalized[0])
    if not (6 <= h <= 13 and 8 <= w <= 12):
        return ["prototype grid must be 6..13 rows and 8..12 columns"]
    errors = []
    paired_rows = {r for r in range(1, h - 1) if normalized[r][0] == normalized[r][-1] == 4}
    paired_cols = {c for c in range(1, w - 1) if normalized[0][c] == normalized[-1][c] == 4}
    for r, row in enumerate(normalized):
        for c, value in enumerate(row):
            if value not in (0, 4, 6, 7, 8):
                errors.append(f"foreign color at {r},{c}")
            elif value == 4 and not (
                (r in (0, h - 1) and 0 < c < w - 1)
                or (c in (0, w - 1) and 0 < r < h - 1)
            ):
                errors.append(f"4 must be a noncorner boundary marker at {r},{c}")
            elif value in (7, 8) and r not in paired_rows and c not in paired_cols:
                errors.append(f"swapped color outside complete paired lanes at {r},{c}")
    return errors


def build_input(seed, pair_index):
    select_threshold(seed)
    if type(pair_index) is not int or not 0 <= pair_index < len(PROFILES):
        raise ValueError("pair_index must be an integer in 0..3")
    stream = f"{TASK_ID}:input:{PROTOTYPE_VERSION}:{seed}:{pair_index}"
    rng = random.Random(int(sha256(stream), 16))
    h, w = rng.randint(7, 10), rng.randint(8, 11)
    grid = [[rng.choice((0, 6)) for _ in range(w)] for _ in range(h)]
    complete_rows, complete_cols = [], []
    singles = []
    profile = PROFILES[pair_index]
    if profile in ("rows", "mixed"):
        paired, single = rng.sample(range(1, h - 1), 2)
        complete_rows.append(paired)
        grid[paired][0] = grid[paired][-1] = 4
        singles.append((single, rng.choice((0, w - 1))))
    if profile in ("columns", "mixed"):
        paired, single = rng.sample(range(1, w - 1), 2)
        complete_cols.append(paired)
        grid[0][paired] = grid[-1][paired] = 4
        singles.append((rng.choice((0, h - 1)), single))
    palette = (7, 8) if pair_index == 0 else ((0, 6) if pair_index == 1 else (0, 6, 7, 8))
    lane_cells = [
        (r, c) for r in range(h) for c in range(w)
        if (r in complete_rows or c in complete_cols) and grid[r][c] != 4
    ]
    rng.shuffle(lane_cells)
    for index, (r, c) in enumerate(lane_cells):
        grid[r][c] = palette[index % len(palette)]
    for r, c in singles:
        grid[r][c] = 4
    errors = validate_input(grid)
    if errors:
        raise ValueError(f"prototype generated invalid input: {errors}")
    return grid


def generate_episode(seed, *, endpoint_threshold=DEFAULT_THRESHOLD, bridge=None, root=None):
    threshold = select_threshold(seed, endpoint_threshold)
    if bridge is None:
        with RacketBridge(timeout=15) as owned:
            return generate_episode(seed, endpoint_threshold=endpoint_threshold, bridge=owned, root=root)
    inputs = [build_input(seed, index) for index in range(4)]
    programs = {t: render_program(t, root=root) for t in THRESHOLDS}
    predictions = {
        t: [execute_program(bridge, programs[t], grid) for grid in inputs]
        for t in THRESHOLDS
    }
    pairs = [{"input": grid, "output": output} for grid, output in zip(inputs, predictions[threshold])]
    rivals = {}
    for alternative in THRESHOLDS:
        if alternative == threshold:
            continue
        mismatches = [i for i in range(3) if predictions[alternative][i] != pairs[i]["output"]]
        query_disagrees = predictions[alternative][3] != pairs[3]["output"]
        rivals[str(alternative)] = {
            "status": "refuted_by_demonstrations" if mismatches else (
                "ambiguous_query" if query_disagrees else "survived_all"
            ),
            "demo_mismatches": mismatches,
            "query_disagrees": query_disagrees,
        }
    rotations = []
    for query in range(4):
        demos = [index for index in range(4) if index != query]
        consistent = [t for t in THRESHOLDS if all(predictions[t][i] == pairs[i]["output"] for i in demos)]
        rotations.append({"query_index": query, "demo_indices": demos, "consistent_thresholds": consistent})
    if any(row["consistent_thresholds"] != [threshold] for row in rotations):
        raise ValueError("demonstrations fail to distinguish the declared parameter rivals")
    program = programs[threshold]
    return {
        "schema": "832404dc8a5c-parametric-episode-v1",
        "status": "proposed prototype",
        "seed": seed,
        "parameter_selection": "seeded" if endpoint_threshold == "sample" else "explicit",
        "parameters": {"endpoint_threshold": threshold},
        "parameter_spec": PARAMETER_SPEC,
        "prototype_version": PROTOTYPE_VERSION,
        "prototype_sha256": sha256(Path(__file__).read_bytes()),
        "program": program,
        "program_sha256": sha256(program),
        "executed_expression": executed_expression(program),
        "executed_expression_sha256": sha256(executed_expression(program)),
        "profiles": list(PROFILES),
        "train": pairs[:3],
        "test": pairs[3:],
        "parameter_predictions": {str(t): predictions[t] for t in THRESHOLDS},
        "parameter_rivals": rivals,
        "role_rotations": rotations,
        "limitations": LIMITATIONS,
    }


def public_challenge(episode):
    return copy.deepcopy({
        "train": episode["train"],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    })


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_evidence(out):
    root = find_root(__file__)
    if out.exists():
        raise FileExistsError("evidence destination exists; choose a new directory")
    (out / "private/programs").mkdir(parents=True)
    (out / "public").mkdir()
    programs = {t: render_program(t, root=root) for t in THRESHOLDS}
    for threshold, program in programs.items():
        (out / f"private/programs/endpoint-threshold-{threshold}.rkt").write_text(program, encoding="utf-8")
    canonical_checks = []
    episodes = []
    with RacketBridge(timeout=15) as bridge:
        for pair in canonical_pairs(TASK_ID, root=root):
            actual = execute_program(bridge, programs[DEFAULT_THRESHOLD], pair["input"])
            canonical_checks.append({**pair, "actual": actual, "equal": actual == pair["output"]})
        if len(canonical_checks) != 4 or not all(pair["equal"] for pair in canonical_checks):
            raise AssertionError("canonical default parity failed")
        for threshold in THRESHOLDS:
            seed = next(seed for seed in range(1000) if select_threshold(seed, "sample") == threshold)
            episode = generate_episode(seed, endpoint_threshold="sample", root=root, bridge=bridge)
            episodes.append(episode)
            write_json(out / f"private/episode-{threshold}.json", episode)
            write_json(out / f"public/challenge-{len(episodes):02d}.json", public_challenge(episode))
        witness_input = build_input(83, 2)
        witness_outputs = {str(t): execute_program(bridge, programs[t], witness_input) for t in THRESHOLDS}
        changed = [
            {"row": r, "column": c, "threshold_1": witness_outputs["1"][r][c], "threshold_2": witness_outputs["2"][r][c]}
            for r in range(len(witness_input)) for c in range(len(witness_input[0]))
            if witness_outputs["1"][r][c] != witness_outputs["2"][r][c]
        ]
        if not changed:
            raise AssertionError("parameter witness does not distinguish settings")
    write_json(out / "private/canonical-parity.json", canonical_checks)
    write_json(out / "private/distinguishing-witness.json", {
        "input": witness_input, "outputs": witness_outputs, "different_cells": changed,
        "input_validation": validate_input(witness_input), "labels": "executed by RacketBridge",
    })
    source_dir = Path(__file__).resolve().parent
    source_paths = [source_dir / "prototype.py", source_dir / "README.md", source_dir.parent.parent / "tests/test_parametric_endpoint_threshold.py"]
    source_hashes = {str(path.relative_to(root)): sha256(path.read_bytes()) for path in source_paths if path.is_file()}
    runtime = racket_runtime_status()
    runtime["bridge_sha256"] = sha256(Path(sys.modules[RacketBridge.__module__].__file__).read_bytes())
    runtime["prelude_sha256"] = sha256(Path(runtime["prelude_path"]).read_bytes())
    report = {
        "schema": "832404dc8a5c-parametric-evidence-v1",
        "status": "proposed prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter_spec": PARAMETER_SPEC,
        "source_hashes": source_hashes,
        "program_sha256": {str(t): sha256(p) for t, p in programs.items()},
        "canonical_parity": {"matched": 4, "total": 4, "default_text_is_canonical": True},
        "episodes": [{"seed": e["seed"], "parameters": e["parameters"], "parameter_rivals": e["parameter_rivals"], "role_rotations": e["role_rotations"]} for e in episodes],
        "distinguishing_witness_changed_cells": len(changed),
        "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "runtime": runtime,
        "limitations": LIMITATIONS,
    }
    write_json(out / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    evidence = commands.add_parser("evidence", help="retain both complete episodes and live Racket checks")
    evidence.add_argument("--out", type=Path, required=True)
    episode = commands.add_parser("episode", help="print one public challenge, optionally retain private labels")
    episode.add_argument("--seed", type=int, required=True)
    episode.add_argument("--endpoint-threshold", choices=("1", "2", "sample"), default="2")
    episode.add_argument("--private-out", type=Path)
    args = parser.parse_args(argv)
    if args.command == "evidence":
        report = build_evidence(args.out.resolve())
        print(json.dumps({"status": report["status"], "canonical_parity": report["canonical_parity"], "episodes": len(report["episodes"]), "out": str(args.out)}, sort_keys=True))
    else:
        threshold = args.endpoint_threshold if args.endpoint_threshold == "sample" else int(args.endpoint_threshold)
        result = generate_episode(args.seed, endpoint_threshold=threshold)
        if args.private_out:
            write_json(args.private_out, result)
        print(json.dumps(public_challenge(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
