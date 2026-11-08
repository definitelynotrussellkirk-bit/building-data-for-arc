#!/usr/bin/env python3
"""Audit the repeated-cell beam shortcut for task e005c30bc59a.

The canonical demonstrations permit a plausible shortcut: trace mirrors and
walls correctly, but stop as soon as the beam reaches any cell it has already
visited.  One canonical path revisits a cell, but its very next cell is a wall,
so the shortcut remains output-equivalent there.  This probe independently
executes both rules and measures whether every cyclic four-example generated
lesson contains a visible continuation after a revisit.

Example, from the repository root::

    PYTHONPATH=shared/runtime python3 \
      generators/e005c30bc59a/workspace/crossing_revisit_probe.py \
      --repo . --lessons-per-band 100 \
      --out ../checks/crossing_revisit_100_lessons.json
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_ID = "e005c30bc59a"
SOURCE_COLORS = {3, 4, 6, 7, 8, 9}
BANDS = ("easy", "medium", "hard")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_generator(repo: Path):
    runtime = repo / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    path = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("crossing_revisit_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def _canonical_row(repo: Path) -> tuple[dict[str, Any], Path]:
    path = repo / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row, path
    raise KeyError(f"canonical task {TASK_ID} missing from {path}")


def _inward(source: tuple[int, int], h: int, w: int) -> tuple[int, int]:
    r, c = source
    if r == 0 and c not in (0, w - 1):
        return (1, 0)
    if r == h - 1 and c not in (0, w - 1):
        return (-1, 0)
    if c == 0 and r not in (0, h - 1):
        return (0, 1)
    if c == w - 1 and r not in (0, h - 1):
        return (0, -1)
    raise ValueError(f"source is not on a non-corner border cell: {source}")


def _bounce(direction: tuple[int, int], kind: int) -> tuple[int, int]:
    dr, dc = direction
    if kind == 1:
        return (-dc, -dr)
    if kind == 2:
        return (dc, dr)
    raise ValueError(f"invalid mirror kind {kind!r}")


def trace(
    grid: list[list[int]], *, stop_on_revisited_cell: bool
) -> tuple[list[list[int]], dict[str, Any]]:
    """Execute the beam rule independently and return output plus path facts."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be non-empty and rectangular")
    h, w = len(grid), len(grid[0])
    sources = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in SOURCE_COLORS
    ]
    if len(sources) != 1:
        raise ValueError(f"expected exactly one source-colored cell, got {len(sources)}")
    sr, sc, color = sources[0]
    direction = _inward((sr, sc), h, w)
    r, c = sr + direction[0], sc + direction[1]
    out = deepcopy(grid)
    states: set[tuple[int, int, int, int]] = set()
    visited_cells: set[tuple[int, int]] = set()
    path: list[tuple[int, int]] = []
    first_revisit: tuple[int, int] | None = None
    continued_new_cells: list[tuple[int, int]] = []
    revisit_seen = False
    termination = "fuel"

    for _ in range(5 * h * w + 8):
        if not (0 <= r < h and 0 <= c < w):
            termination = "boundary"
            break
        position = (r, c)
        was_visited = position in visited_cells
        if stop_on_revisited_cell and was_visited:
            termination = "revisited_cell"
            break
        if was_visited and first_revisit is None:
            first_revisit = position
            revisit_seen = True
        state = (r, c, direction[0], direction[1])
        if state in states:
            termination = "directional_loop"
            break
        states.add(state)
        visited_cells.add(position)

        value = grid[r][c]
        if value == 0:
            out[r][c] = color
            path.append(position)
            if revisit_seen and not was_visited:
                continued_new_cells.append(position)
        elif value == 5:
            termination = "wall"
            break
        elif value in (1, 2):
            direction = _bounce(direction, value)
        else:
            termination = f"unexpected_{value}"
            break
        r += direction[0]
        c += direction[1]

    return out, {
        "source": [sr, sc],
        "source_color": color,
        "termination": termination,
        "path_length_with_repeats": len(path),
        "unique_path_cells": len(set(path)),
        "revisit_count": len(path) - len(set(path)),
        "first_revisit": list(first_revisit) if first_revisit is not None else None,
        "continued_new_cells_after_first_revisit": [list(p) for p in continued_new_cells],
    }


def _diff_cells(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    return [
        [r, c, a[r][c], b[r][c]]
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]


def _canonical_report(row: dict[str, Any]) -> dict[str, Any]:
    train = list(row.get("train", []))
    public_pairs = train + list(row.get("test", []))
    intended_match: list[bool] = []
    rival_fit: list[bool] = []
    facts: list[dict[str, Any]] = []
    for index, pair in enumerate(public_pairs):
        intended, intended_facts = trace(pair["input"], stop_on_revisited_cell=False)
        rival, rival_facts = trace(pair["input"], stop_on_revisited_cell=True)
        intended_match.append(intended == pair["output"])
        rival_fit.append(rival == pair["output"])
        facts.append(
            {
                "pair_index": index,
                "split": "train" if index < len(train) else "test",
                "intended_facts": intended_facts,
                "rival_facts": rival_facts,
                "rival_matches_output": rival == pair["output"],
            }
        )
    return {
        "train_demonstration_count": len(train),
        "public_pair_count": len(public_pairs),
        "intended_matches_each_public_pair": intended_match,
        "intended_matches_all_public_pairs": bool(intended_match) and all(intended_match),
        "rival_fits_each_public_pair": rival_fit,
        "rival_fits_all_train_demonstrations": bool(train)
        and all(rival_fit[: len(train)]),
        "rival_fits_all_public_pairs": bool(public_pairs) and all(rival_fit),
        "pair_facts": facts,
    }


def _band_report(module, *, band: str, lessons: int, seed_prefix: str) -> dict[str, Any]:
    lesson_rows: list[dict[str, Any]] = []
    input_serializations: set[str] = set()
    requested_inputs = 0
    witness_inputs = 0
    crossing_inputs = 0
    generator_rule_matches = True
    first_witness: dict[str, Any] | None = None
    errors: list[dict[str, Any]] = []
    cyclic_starts = {str(i): {"lessons": 0, "refuted": 0} for i in range(4)}

    for lesson_index in range(lessons):
        start_mod = lesson_index % 4
        start_index = lesson_index * 8 + start_mod
        seed = f"{seed_prefix}:{band}:{lesson_index}"
        lesson_refutes = False
        lesson_inputs: list[dict[str, Any]] = []
        cyclic_starts[str(start_mod)]["lessons"] += 1
        for offset in range(4):
            sample_index = start_index + offset
            requested_inputs += 1
            try:
                grid = module.generate(seed, sample_index, difficulty=band)
                validation = list(module.self_check(grid))
                if validation:
                    raise ValueError("generator self_check: " + "; ".join(validation))
                intended, intended_facts = trace(grid, stop_on_revisited_cell=False)
                rival, rival_facts = trace(grid, stop_on_revisited_cell=True)
                mirrored = module.rule_mirror(grid)
                generator_rule_matches &= mirrored == intended
                serialized = json.dumps(grid, separators=(",", ":"))
                input_serializations.add(serialized)
                differs = rival != intended
                if intended_facts["revisit_count"]:
                    crossing_inputs += 1
                if differs:
                    witness_inputs += 1
                    lesson_refutes = True
                    if first_witness is None:
                        first_witness = {
                            "seed": seed,
                            "sample_index": sample_index,
                            "difficulty": band,
                            "input": grid,
                            "intended_output": intended,
                            "rival_output": rival,
                            "different_cells": _diff_cells(intended, rival),
                            "intended_facts": intended_facts,
                            "rival_facts": rival_facts,
                        }
                lesson_inputs.append(
                    {
                        "sample_index": sample_index,
                        "rival_differs": differs,
                        "revisit_count": intended_facts["revisit_count"],
                        "continued_new_cell_count": len(
                            intended_facts["continued_new_cells_after_first_revisit"]
                        ),
                    }
                )
            except Exception as exc:
                errors.append(
                    {
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": sample_index,
                        "error": repr(exc),
                    }
                )
        if lesson_refutes:
            cyclic_starts[str(start_mod)]["refuted"] += 1
        lesson_rows.append(
            {
                "lesson_index": lesson_index,
                "seed": seed,
                "start_modulo_four": start_mod,
                "sample_indices": [start_index + i for i in range(4)],
                "refutes_rival": lesson_refutes,
                "inputs": lesson_inputs,
            }
        )

    failed_lessons = [row for row in lesson_rows if not row["refutes_rival"]]
    return {
        "lesson_policy": (
            "four consecutive default draws; disjoint index blocks; starts cycle "
            "through all four schedule residues"
        ),
        "lesson_count": lessons,
        "requested_input_count": requested_inputs,
        "unique_input_count": len(input_serializations),
        "crossing_input_count": crossing_inputs,
        "rival_witness_input_count": witness_inputs,
        "failed_lesson_count": len(failed_lessons),
        "all_lessons_refute_rival": not failed_lessons and not errors,
        "generator_rule_matches_independent_trace": generator_rule_matches,
        "cyclic_starts": cyclic_starts,
        "generation_or_validation_errors": errors,
        "first_failed_lessons": failed_lessons[:10],
        "first_witness": first_witness,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--seed-prefix", default="crossing-revisit-probe-v1")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.lessons_per_band < 1:
        parser.error("--lessons-per-band must be positive")

    repo = args.repo.resolve()
    module, generator_path = _load_generator(repo)
    row, canonical_path = _canonical_row(repo)
    report = {
        "schema": "e005c30bc59a-crossing-revisit-probe-v1",
        "task_id": TASK_ID,
        "rival_name": "stop_on_revisited_cell",
        "rival_description": (
            "Trace source color, mirrors, and walls correctly, but stop before "
            "processing the first cell whose coordinate was already visited."
        ),
        "generator": {
            "path": str(generator_path),
            "source_sha256": _sha256(generator_path),
            "version": getattr(module, "VERSION", None),
            "rule_hash": getattr(module, "RULE_HASH", None),
        },
        "canonical_source": {
            "path": str(canonical_path),
            "sha256": _sha256(canonical_path),
        },
        "seed_prefix": args.seed_prefix,
        "lessons_per_band": args.lessons_per_band,
        "canonical": _canonical_report(row),
        "bands": {
            band: _band_report(
                module,
                band=band,
                lessons=args.lessons_per_band,
                seed_prefix=args.seed_prefix,
            )
            for band in BANDS
        },
        "command": [
            "python3",
            "generators/e005c30bc59a/workspace/crossing_revisit_probe.py",
            "--repo",
            ".",
            "--lessons-per-band",
            str(args.lessons_per_band),
            "--seed-prefix",
            args.seed_prefix,
            "--out",
            str(args.out),
        ],
        "cwd": "repo",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
