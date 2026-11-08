#!/usr/bin/env python3
"""Audit a demonstration-adaptive raw-shape shortcut for 155fb684795d.

The rival never performs plus-growth. It learns the raw singleton common motif
from labelled demonstrations, then resolves the query using raw dihedral keys.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
SOURCE = REPO / "generators" / "155fb684795d" / "generator.py"
sys.path.insert(0, str(REPO / "shared" / "runtime"))

spec = importlib.util.spec_from_file_location("audit_155fb684795d", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {SOURCE}")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

Cell = tuple[int, int]
Grid = list[list[int]]


def norm(cells: Iterable[Cell]) -> tuple[Cell, ...]:
    items = list(cells)
    if not items:
        return ()
    r0 = min(r for r, _ in items)
    c0 = min(c for _, c in items)
    return tuple(sorted((r - r0, c - c0) for r, c in items))


def rot(cells: Iterable[Cell]) -> tuple[Cell, ...]:
    return norm((c, -r) for r, c in cells)


def raw_key(cells: Iterable[Cell]) -> tuple[Cell, ...]:
    forms: set[tuple[Cell, ...]] = set()
    cur = norm(cells)
    for _ in range(4):
        forms.add(cur)
        forms.add(norm((r, -c) for r, c in cur))
        cur = rot(cur)
    return min(forms)


def panel_cells(grid: Grid) -> list[tuple[Cell, ...]]:
    h, w = len(grid), len(grid[0])
    separators = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    bounds = [-1, *separators, w]
    panels: list[tuple[Cell, ...]] = []
    for idx in range(len(bounds) - 1):
        left, right = bounds[idx] + 1, bounds[idx + 1]
        cells = [(r, c - left) for r in range(h) for c in range(left, right) if grid[r][c] != 0]
        panels.append(norm(cells))
    if len(panels) != 4:
        raise ValueError(f"expected four panels, got {len(panels)}")
    return panels


def output_cells(grid: Grid) -> tuple[Cell, ...]:
    return norm((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8)


def crop_as_eight(cells: Iterable[Cell]) -> Grid:
    cells = norm(cells)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in cells:
        out[r][c] = 8
    return out


def rival_solve(demos: list[dict[str, Grid]], query_input: Grid) -> tuple[Grid, dict]:
    learned_singleton_common: set[tuple[Cell, ...]] = set()
    learned_from: list[dict] = []

    for demo_index, demo in enumerate(demos):
        panels = panel_cells(demo["input"])
        keys = [raw_key(cells) for cells in panels]
        answer_key = raw_key(output_cells(demo["output"]))
        answer_indices = [i for i, key in enumerate(keys) if key == answer_key]
        if len(answer_indices) != 1:
            raise ValueError(f"demo {demo_index}: output does not identify one raw panel")
        answer_index = answer_indices[0]
        common_keys = [key for i, key in enumerate(keys) if i != answer_index]
        counts = Counter(common_keys)
        singleton_keys = {key for key, count in counts.items() if count == 1}
        learned_singleton_common.update(singleton_keys)
        learned_from.append({
            "demo_index": demo_index,
            "answer_index": answer_index,
            "singleton_common_count": len(singleton_keys),
        })

    query_panels = panel_cells(query_input)
    query_keys = [raw_key(cells) for cells in query_panels]
    counts = Counter(query_keys)
    unique_indices = [i for i, key in enumerate(query_keys) if counts[key] == 1]

    if len(unique_indices) == 1:
        chosen = unique_indices[0]
        branch = "single_raw_unique"
    else:
        remaining = [i for i in unique_indices if query_keys[i] not in learned_singleton_common]
        if len(remaining) != 1:
            raise ValueError(
                "raw-vocabulary rival is ambiguous: "
                f"unique={unique_indices}, remaining={remaining}, learned={len(learned_singleton_common)}"
            )
        chosen = remaining[0]
        branch = "exclude_learned_singleton_common"

    return crop_as_eight(query_panels[chosen]), {
        "learned_singleton_common_count": len(learned_singleton_common),
        "unique_query_indices": unique_indices,
        "chosen_index": chosen,
        "branch": branch,
        "learned_from": learned_from,
    }


bands = ("easy", "medium", "hard")
seed_start = 0
seed_count = 100
passes = 0
failures: list[dict] = []
unique_inputs: set[str] = set()
branch_counts: Counter[str] = Counter()
first_witness = None

for band in bands:
    for seed in range(seed_start, seed_start + seed_count):
        block = []
        for sample_index in range(4):
            inp = gen.generate(seed, sample_index, difficulty=band)
            out = gen.rule_mirror(inp)
            unique_inputs.add(hashlib.sha256(json.dumps(inp, separators=(",", ":")).encode()).hexdigest())
            block.append({"input": inp, "output": out})
        for query_position in range(4):
            demos = [pair for i, pair in enumerate(block) if i != query_position]
            query = block[query_position]
            try:
                rival, trace = rival_solve(demos, query["input"])
                ok = rival == query["output"]
            except Exception as exc:  # retain exact failures if behavior changes
                rival = None
                trace = {"error": f"{type(exc).__name__}: {exc}"}
                ok = False
            if ok:
                passes += 1
                branch_counts[trace["branch"]] += 1
            else:
                failures.append({
                    "band": band,
                    "seed": seed,
                    "sample_indices": [0, 1, 2, 3],
                    "query_position": query_position,
                    "trace": trace,
                    "expected": query["output"],
                    "rival": rival,
                })
            if first_witness is None and band == "medium" and seed == 0 and query_position == 3:
                first_witness = {
                    "band": band,
                    "seed": seed,
                    "sample_indices": [0, 1, 2, 3],
                    "query_position": query_position,
                    "demos": demos,
                    "query": query,
                    "rival_output": rival,
                    "trace": trace,
                }

requested = len(bands) * seed_count * 4
report = {
    "schema": "audit-raw-vocabulary-shortcut-v1",
    "task_id": gen.TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rule_hash": gen.RULE_HASH,
    "rival": (
        "Never plus-grow. From labelled demos, record any raw dihedral shape that is "
        "a singleton among the three non-answer panels. In the query, choose the sole "
        "raw-unique panel; when two panels are raw-unique, exclude the learned singleton "
        "common shape and choose the other."
    ),
    "bands": list(bands),
    "seed_range": [seed_start, seed_start + seed_count - 1],
    "sample_indices_per_lesson": [0, 1, 2, 3],
    "query_policy": "all four rotations; remaining three pairs are labelled demonstrations",
    "lessons_requested": requested,
    "lessons_matched": passes,
    "lessons_failed": len(failures),
    "unique_inputs": len(unique_inputs),
    "branch_counts": dict(sorted(branch_counts.items())),
    "failures": failures[:20],
    "command": ["python3", "checks/audit/155fb684795d/raw_vocabulary_shortcut_probe.py"],
    "cwd": "packet_root",
}

HERE.with_name("raw_vocabulary_shortcut_probe.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
if first_witness is None:
    raise RuntimeError("failed to retain witness")
HERE.with_name("witness_lesson.json").write_text(
    json.dumps(first_witness, indent=2, sort_keys=True) + "\n"
)
HERE.with_name("witness_inputs.json").write_text(
    json.dumps(
        [pair["input"] for pair in first_witness["demos"]] + [first_witness["query"]["input"]],
        indent=2,
    ) + "\n"
)
HERE.with_name("witness_rival_outputs.json").write_text(
    json.dumps(
        [pair["output"] for pair in first_witness["demos"]] + [first_witness["rival_output"]],
        indent=2,
    ) + "\n"
)
print(json.dumps(report, indent=2, sort_keys=True))
if failures:
    raise SystemExit(1)
