"""Independent oracle and curriculum probe for d57b7deebba2.

This module deliberately does not import production-generator helpers when it
computes outputs.  It is test/review tooling, not an alternative label
authority.  The canonical Racket program remains authoritative; the Python
geometry oracle is separately checked against every public canonical pair and
can be batch-checked against Racket by the packet's supported ``arcpuzzles
apply`` command.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
TASK = "d57b7deebba2"
GENERATOR_PATH = ROOT / "generators" / TASK / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
RUNTIME_PATH = ROOT / "shared" / "runtime"
if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or GENERATOR_PATH).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_d57b7deebba2_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical() -> dict[str, Any]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs() -> list[dict[str, Any]]:
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def _rectangular_copy(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    out = [list(row) for row in grid]
    if not out or not out[0] or any(len(row) != len(out[0]) for row in out):
        raise ValueError("expected a nonempty rectangular grid")
    return out


def intended_output(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    """Independent transcription of the authority's color+anti-diagonal rule."""
    source = _rectangular_copy(grid)
    out = deepcopy(source)
    groups: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for r, row in enumerate(source):
        for c, color in enumerate(row):
            if color != 0:
                groups.setdefault((color, r + c), []).append((r, c))
    for (color, diag), cells in groups.items():
        if len(cells) < 2:
            continue
        lo = min(r for r, _ in cells)
        hi = max(r for r, _ in cells)
        for r in range(lo, hi + 1):
            c = diag - r
            if 0 <= c < len(source[0]):
                out[r][c] = color
    return out


def distinct_color_pairs_only(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    """Plausible wrong rule: fill only colors occurring exactly twice globally."""
    source = _rectangular_copy(grid)
    out = deepcopy(source)
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(source):
        for c, color in enumerate(row):
            if color != 0:
                by_color.setdefault(color, []).append((r, c))
    for color, cells in by_color.items():
        if len(cells) != 2:
            continue
        (r0, c0), (r1, c1) = sorted(cells)
        if r0 + c0 != r1 + c1:
            continue
        for r in range(r0, r1 + 1):
            out[r][r0 + c0 - r] = color
    return out


def span_groups(grid: Iterable[Iterable[int]]) -> list[tuple[int, int, tuple[tuple[int, int], ...]]]:
    source = _rectangular_copy(grid)
    groups: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for r, row in enumerate(source):
        for c, color in enumerate(row):
            if color:
                groups.setdefault((color, r + c), []).append((r, c))
    return [
        (color, diag, tuple(sorted(cells)))
        for (color, diag), cells in sorted(groups.items())
        if len(cells) >= 2
    ]


def observed(grid: Iterable[Iterable[int]]) -> dict[str, int]:
    source = _rectangular_copy(grid)
    return {
        "grid_h": len(source),
        "grid_w": len(source[0]),
        "n_pairs": len(span_groups(source)),
    }


def has_reused_color(grid: Iterable[Iterable[int]]) -> bool:
    groups = span_groups(grid)
    counts = Counter(color for color, _diag, _cells in groups)
    return any(count >= 2 for count in counts.values())


def witness_input() -> list[list[int]]:
    grid = [[0] * 10 for _ in range(7)]
    # Two separate anti-diagonals deliberately reuse color 4.
    grid[0][4] = grid[2][2] = 4
    grid[3][8] = grid[6][5] = 4
    return grid


def grid_hash(grid: Iterable[Iterable[int]]) -> str:
    payload = json.dumps([list(row) for row in grid], separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def source_sha256(path: Path = GENERATOR_PATH) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pinned_seed(task_id: str, scope: str, index: int) -> int:
    # Exact derivation imported by the generic semantic gate from
    # canonical_profile_gate._pinned_seed, copied here so this task-local probe
    # is source-bound and runnable without importing review scripts.
    digest = hashlib.sha256(f"{task_id}|{scope}|{index}".encode()).digest()
    return int.from_bytes(digest[:8], "big") & 0x7FFFFFFF


def audit_lessons(*, lessons_per_band: int = 100, n_demos: int = 3) -> dict[str, Any]:
    """Audit the real generator sampler with the gate's stride-11 policy.

    Outputs are computed by the independent geometry oracle.  This routine
    measures curriculum identifiability; it does not replace Racket authority
    verification, which is recorded separately by the review packet.
    """
    gen = load_generator()
    bands = ("easy", "medium", "hard")
    report: dict[str, Any] = {
        "schema": "d57b7deebba2-lesson-probe-v1",
        "task_id": TASK,
        "generator_sha256": source_sha256(),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "sampler": {
            "bands": list(bands),
            "lessons_per_band": lessons_per_band,
            "examples_needed": n_demos,
            "queries_per_lesson": 1,
            "seed_rule": "sha256(task_id|lesson:BAND|k), first 8 bytes, 31-bit",
            "start_rule": "sample_index = k * 11",
            "assembly": "n_demos consecutive indices, then one consecutive query",
            "overlap_between_windows": False,
            "output_oracle": "independent Python transcription; Racket checked separately",
        },
        "bands": {},
    }
    all_inputs: set[str] = set()
    for band in bands:
        identifiable = 0
        witness_lessons = 0
        rival_refuted = 0
        rival_survived_demos = 0
        unique_inputs: set[str] = set()
        profile_counts: Counter[str] = Counter()
        shape_counts: Counter[str] = Counter()
        pair_counts: Counter[int] = Counter()
        failures: list[dict[str, Any]] = []
        for k in range(lessons_per_band):
            seed = _pinned_seed(TASK, f"lesson:{band}", k)
            start = k * 11
            grids = [gen.generate(seed, start + offset, difficulty=band) for offset in range(n_demos + 1)]
            demos = [(grid, intended_output(grid)) for grid in grids[:n_demos]]
            query_grid = grids[n_demos]
            witness = any(has_reused_color(grid) for grid, _ in demos)
            survives = all(distinct_color_pairs_only(grid) == out for grid, out in demos)
            query_differs = distinct_color_pairs_only(query_grid) != intended_output(query_grid)
            identified = not (survives and query_differs)
            identifiable += int(identified)
            witness_lessons += int(witness)
            rival_refuted += int(not survives)
            rival_survived_demos += int(survives)
            if not identified and len(failures) < 8:
                failures.append({"k": k, "seed": seed, "start": start, "query_differs": query_differs})
            for offset, grid in enumerate(grids):
                digest = grid_hash(grid)
                unique_inputs.add(digest)
                all_inputs.add(digest)
                shape_counts[f"{len(grid)}x{len(grid[0])}"] += 1
                pair_counts[observed(grid)["n_pairs"]] += 1
                try:
                    profile = gen.schedule_profile(seed, start + offset, difficulty=band)
                except Exception:
                    profile = "unavailable"
                profile_counts[str(profile)] += 1
        report["bands"][band] = {
            "lessons": lessons_per_band,
            "identifiable": identifiable,
            "witness_lessons": witness_lessons,
            "rival_refuted": rival_refuted,
            "rival_survived_demos": rival_survived_demos,
            "unique_inputs": len(unique_inputs),
            "draws": lessons_per_band * (n_demos + 1),
            "profile_counts": dict(sorted(profile_counts.items())),
            "shape_counts": dict(sorted(shape_counts.items())),
            "pair_counts": {str(k): v for k, v in sorted(pair_counts.items())},
            "failures": failures,
        }
    report["total_unique_inputs"] = len(all_inputs)
    report["total_draws"] = lessons_per_band * len(bands) * (n_demos + 1)
    report["canonical_shortcut_fit"] = all(
        distinct_color_pairs_only(pair["input"]) == pair["output"]
        for pair in canonical_pairs()
    )
    report["canonical_oracle_match"] = all(
        intended_output(pair["input"]) == pair["output"]
        for pair in canonical_pairs()
    )
    witness = witness_input()
    report["fixed_counterexample"] = {
        "input": witness,
        "intended_output": intended_output(witness),
        "rival_output": distinct_color_pairs_only(witness),
        "differing_cells": [
            [r, c]
            for r in range(len(witness))
            for c in range(len(witness[0]))
            if intended_output(witness)[r][c] != distinct_color_pairs_only(witness)[r][c]
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--examples-needed", type=int, default=3)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = audit_lessons(lessons_per_band=args.lessons_per_band, n_demos=args.examples_needed)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    print(text)
    bad = any(row["identifiable"] != row["lessons"] for row in report["bands"].values())
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
