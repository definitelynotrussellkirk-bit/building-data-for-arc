#!/usr/bin/env python3
"""Rebuild the 6f6c567e365b identity-rival lesson counterexample.

Uses only the selected public generator loader and the retained public
`arcpuzzles apply` receipt. It never imports private runner functions.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Callable

TASK = "6f6c567e365b"
EXPECTED_GENERATOR_SHA256 = "dfe1929d624acbda751ee7a494252ffb4fb678c439002c82adc619fee0db7e1a"
SEED = 367
DIFFICULTY = "easy"
DEMONSTRATION_INDICES = [0, 1, 2]
QUERY_INDEX = 3
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"


def load_generator():
    helper = REPO / "shared/runtime/reviewer_support.py"
    spec = importlib.util.spec_from_file_location("selected_support_6f6c", helper)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {helper}")
    support = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = support
    spec.loader.exec_module(support)
    return support.load_selected_generator(TASK, root=REPO)


def crop_to_content(grid: list[list[int]]) -> list[list[int]]:
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not points:
        return [[0]]
    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid[::-1]]


def transform(grid: list[list[int]], key: int) -> list[list[int]]:
    transforms: dict[int, Callable[[list[list[int]]], list[list[int]]]] = {
        1: rotate_cw,
        2: rotate_180,
        3: flip_lr,
        4: flip_ud,
    }
    return transforms.get(key, lambda value: [row[:] for row in value])(grid)


def gallery(crops: list[list[list[int]]]) -> list[list[int]]:
    height = max(len(item) for item in crops)
    width = sum(len(item[0]) for item in crops) + len(crops) - 1
    out = [[0] * width for _ in range(height)]
    left = 0
    for item in crops:
        for r, row in enumerate(item):
            for c, value in enumerate(row):
                if value:
                    out[r][left + c] = value
        left += len(item[0]) + 1
    return out


def canonical_mirror(grid: list[list[int]]) -> list[list[int]]:
    keys = [value for value in grid[0] if value]
    current = crop_to_content(grid[1:])
    states = [current]
    for key in keys:
        current = transform(current, key)
        states.append(current)
    return gallery(states)


def identity_rival(grid: list[list[int]]) -> list[list[int]]:
    """Plausible shortcut: ignore every key and repeat the original crop."""
    keys = [value for value in grid[0] if value]
    original = crop_to_content(grid[1:])
    return gallery([original] * (len(keys) + 1))


def sha_json(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    module, source_path, source_sha = load_generator()
    if source_sha != EXPECTED_GENERATOR_SHA256:
        raise RuntimeError(f"selected source changed: {source_sha}")

    indices = DEMONSTRATION_INDICES + [QUERY_INDEX]
    inputs = [module.generate(SEED, index, difficulty=DIFFICULTY) for index in indices]
    validator = [module.self_check(grid, difficulty=DIFFICULTY, meta={}) for grid in inputs]
    if any(validator):
        raise RuntimeError(f"generated input left documented domain: {validator}")

    racket_path = HERE / "racket.json"
    racket = json.loads(racket_path.read_text())
    if racket["generator_sha256"] != source_sha or racket["executed_rule_hash"] != "33361398d469":
        raise RuntimeError("retained apply receipt is not bound to the expected source/rule")
    if [row["input"] for row in racket["results"]] != inputs:
        raise RuntimeError("retained apply inputs differ from regenerated inputs")

    actual = [row["output"] for row in racket["results"]]
    mirror = [canonical_mirror(grid) for grid in inputs]
    rival = [identity_rival(grid) for grid in inputs]
    if actual != mirror:
        raise RuntimeError("independent Python mirror disagrees with protected Racket")

    demo_fits = [actual[i] == rival[i] for i in DEMONSTRATION_INDICES]
    query_differs = actual[QUERY_INDEX] != rival[QUERY_INDEX]
    if demo_fits != [True, True, True] or not query_differs:
        raise RuntimeError("counterexample no longer demonstrates the claimed ambiguity")

    payload = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK,
        "generator_path": str(source_path.relative_to(REPO)),
        "generator_sha256": source_sha,
        "rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "seed": SEED,
        "difficulty": DIFFICULTY,
        "sample_indices": indices,
        "lesson_policy": {
            "demonstrations": DEMONSTRATION_INDICES,
            "query": QUERY_INDEX,
            "ordering": "sample_index 0,1,2 -> demonstrations; 3 -> query",
        },
        "domain_validation": {
            "self_check_errors": validator,
            "all_inputs_pass": True,
            "documented_generator_domain": True,
        },
        "rival": {
            "name": "ignore_all_keys_repeat_initial_crop",
            "description": "Keep the required gallery shape but treat every transform key as identity.",
            "fits_demonstrations": demo_fits,
            "changes_query": query_differs,
        },
        "inputs": inputs,
        "actual_racket_outputs": actual,
        "rival_outputs": rival,
        "input_sha256": [sha_json(value) for value in inputs],
        "actual_output_sha256": [sha_json(value) for value in actual],
        "rival_output_sha256": [sha_json(value) for value in rival],
        "apply_receipt": "checks/audit/6f6c567e365b/racket.json",
        "reproduction": {
            "cwd": "packet_root",
            "argv": [
                "python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", TASK,
                "--input", "../checks/audit/6f6c567e365b/input.json",
                "--out", "../checks/audit/6f6c567e365b/racket.json",
            ],
        },
    }
    (HERE / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
    (HERE / "counterexample.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({
        "task_id": TASK,
        "generator_sha256": source_sha,
        "demo_fits": demo_fits,
        "query_differs": query_differs,
        "counterexample": str(HERE / "counterexample.json"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
