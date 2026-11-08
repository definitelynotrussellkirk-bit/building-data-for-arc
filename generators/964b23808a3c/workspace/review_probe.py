#!/usr/bin/env python3
"""Source-bound authoring probe for generator 964b23808a3c.

Checks canonical parity, exact scheduled profiles, declared shortcut fit, rival
counterexamples, and every query rotation in consecutive four-pair windows.
This reads canonical answers and must not be used during solve episodes.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "964b23808a3c"
BANDS = (None, "easy", "medium", "hard")


def load_generator():
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def oracle(grid):
    out = copy.deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for column in range(width):
        marks = [row for row in range(height) if grid[row][column] != 0]
        if not marks or grid[marks[-1]][column] != 5:
            continue
        previous = -1
        for row in marks:
            color = grid[row][column]
            for fill_row in range(previous + 1, row + 1):
                out[fill_row][column] = color
            previous = row
    return out


def profile(grid):
    return [len(grid), len(grid[0]), len({value for row in grid for value in row})]


def competitors(gen):
    result = {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        for name, rule in getattr(gen, namespace, {}).items():
            result.setdefault(name, rule)
    return result


def run_probe(seed_count: int, window_count: int) -> dict[str, Any]:
    gen, source = load_generator()
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    root = find_root(__file__)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    failures: list[str] = []

    canonical_shortcut_fit = {name: 0 for name in gen.CANONICAL_SHORTCUTS}
    for pair in pairs:
        expected = oracle(pair["input"])
        label = f"{pair['split']}[{pair['pair_index']}]"
        if expected != pair["output"]:
            failures.append(f"independent oracle mismatch on {label}")
        if gen.rule_mirror(pair["input"]) != expected:
            failures.append(f"generator mirror mismatch on {label}")
        if gen.self_check(pair["input"]):
            failures.append(f"self_check rejects canonical {label}")
        for name, rule in gen.CANONICAL_SHORTCUTS.items():
            if rule(pair["input"]) == pair["output"]:
                canonical_shortcut_fit[name] += 1
            else:
                failures.append(f"declared canonical shortcut {name} misses {label}")

    sampled_profiles: dict[str, dict[str, int]] = {}
    rival_refutations = {name: 0 for name in competitors(gen)}
    rotation_cases = rotation_failures = 0
    unique_inputs: set[str] = set()
    for band in BANDS:
        band_name = band or "none"
        sampled_profiles[band_name] = {}
        for seed in range(seed_count):
            grids = [gen.generate(seed, index, difficulty=band) for index in range(window_count + 3)]
            outputs = [oracle(grid) for grid in grids]
            for grid in grids:
                key = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
                unique_inputs.add(key)
                p = "x".join(map(str, profile(grid)))
                sampled_profiles[band_name][p] = sampled_profiles[band_name].get(p, 0) + 1
                for name, rule in competitors(gen).items():
                    if rule(grid) != oracle(grid):
                        rival_refutations[name] += 1
            for start in range(window_count):
                window = [
                    {"input": grids[index], "output": outputs[index]}
                    for index in range(start, start + 4)
                ]
                for query_index in range(4):
                    rotation_cases += 1
                    query = window[query_index]
                    demos = [pair for index, pair in enumerate(window) if index != query_index]
                    findings = gen.lesson_identifiable(demos, query)
                    if findings:
                        rotation_failures += 1
                        failures.append(
                            f"band={band_name} seed={seed} start={start} query={query_index}: "
                            + "; ".join(findings)
                        )

    expected_canonical = len(pairs)
    for name, count in canonical_shortcut_fit.items():
        if count != expected_canonical:
            failures.append(f"shortcut {name} fits {count}/{expected_canonical} canonical pairs")
    for name, count in rival_refutations.items():
        if count == 0:
            failures.append(f"declared rival {name} has no generated counterexample")

    return {
        "schema": "964b23808a3c-review-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "seed_count": seed_count,
        "window_count_per_seed_band": window_count,
        "canonical_pairs": len(pairs),
        "canonical_shortcut_fit": canonical_shortcut_fit,
        "sampled_profiles": sampled_profiles,
        "declared_rival_refutations": rival_refutations,
        "rotation_cases": rotation_cases,
        "rotation_failures": rotation_failures,
        "unique_inputs": len(unique_inputs),
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--windows", type=int, default=9)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1 or args.windows < 1:
        parser.error("--seeds and --windows must be positive")
    report = run_probe(args.seeds, args.windows)
    text = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
