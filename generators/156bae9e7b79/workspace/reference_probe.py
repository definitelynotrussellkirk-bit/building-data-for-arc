#!/usr/bin/env python3
"""Portable semantic probe for generator 156bae9e7b79.

This tool deliberately reads rival names from the generator declarations rather
than copying a list.  It checks three finite claims:

1. every declared canonical shortcut fits every usable canonical labeled pair;
2. one exact lawful off-center/truncated input makes each named shortcut differ;
3. every four-pair query rotation over requested seeds/starts is unambiguous
   against all declared lesson competitors.

The Python mirror is a fast task-local diagnostic.  Use the shared Racket-backed
``arcpuzzles lesson-census`` for source-bound production evidence.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import canonical_pairs, find_root

TASK_ID = "156bae9e7b79"
TASK_HOME = Path(__file__).resolve().parents[1]
DEFAULT_GENERATOR = TASK_HOME / "generator.py"


def load_generator(path: Path | str | None = None):
    generator_path = Path(
        path or os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR)
    ).resolve()
    spec = importlib.util.spec_from_file_location(
        f"reference_probe_generator_{TASK_ID}", generator_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {generator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, generator_path


def _difference_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    differences: list[list[int]] = []
    if len(left) != len(right):
        return [[-1, -1]]
    for row, (a_row, b_row) in enumerate(zip(left, right, strict=True)):
        if len(a_row) != len(b_row):
            differences.append([row, -1])
            continue
        for col, (a, b) in enumerate(zip(a_row, b_row, strict=True)):
            if a != b:
                differences.append([row, col])
    return differences


def _canonical_report(gen) -> dict[str, Any]:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    if not pairs:
        raise RuntimeError(f"{TASK_ID}: no canonical labeled pairs")
    report: dict[str, Any] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        mismatch_indices: list[int] = []
        errors: list[str] = []
        for index, pair in enumerate(pairs):
            try:
                candidate = rival(deepcopy(pair["input"]))
            except Exception as exc:  # retained as evidence, never swallowed
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
                continue
            if candidate != pair["output"]:
                mismatch_indices.append(index)
        report[name] = {
            "canonical_pairs": len(pairs),
            "mismatch_indices": mismatch_indices,
            "errors": errors,
            "fits_all_canonical": not mismatch_indices and not errors,
        }
    return report


def _counterexample_report(gen) -> dict[str, Any]:
    request = {
        "grid_h": 12,
        "grid_w": 13,
        "n_colors": 9,
        "line_position": "left",
        "line_end": "truncated",
    }
    seed, sample_index = 44, 5
    grid = gen.generate(seed, sample_index, difficulty="medium", **request)
    truth = gen.rule_mirror(deepcopy(grid))
    rival_outputs: dict[str, list[list[int]]] = {}
    differences: dict[str, bool] = {}
    differing_cells: dict[str, list[list[int]]] = {}
    errors: dict[str, str] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        try:
            output = rival(deepcopy(grid))
        except Exception as exc:
            errors[name] = f"{type(exc).__name__}: {exc}"
            continue
        rival_outputs[name] = output
        cells = _difference_cells(output, truth)
        differing_cells[name] = cells
        differences[name] = bool(cells)
    return {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": "medium",
        "overrides": request,
        "observed": gen.observe_overrides(grid),
        "self_check": gen.self_check(deepcopy(grid)),
        "witnesses": {
            name: bool(predicate(deepcopy(grid)))
            for name, predicate in gen.SEMANTIC_WITNESSES.items()
        },
        "input": grid,
        "intended_output": truth,
        "rival_outputs": rival_outputs,
        "rival_differences": differences,
        "differing_cells": differing_cells,
        "rival_errors": errors,
    }


def _rotation_report(
    gen,
    *,
    seeds: Iterable[int],
    starts: Iterable[int],
    bands: Iterable[str] = ("easy", "medium", "hard"),
) -> dict[str, Any]:
    seed_values = list(seeds)
    start_values = list(starts)
    band_values = list(bands)
    ambiguities: list[dict[str, Any]] = []
    hook_failures: list[dict[str, Any]] = []
    competitor_errors: list[dict[str, Any]] = []
    lessons = 0
    rotations = 0
    unique_inputs: set[str] = set()

    for band in band_values:
        for seed in seed_values:
            for start in start_values:
                lessons += 1
                pairs: list[dict[str, Any]] = []
                for offset in range(4):
                    grid = gen.generate(seed, start + offset, difficulty=band)
                    unique_inputs.add(json.dumps(grid, separators=(",", ":")))
                    pairs.append({
                        "input": grid,
                        "output": gen.rule_mirror(deepcopy(grid)),
                    })

                for query_index in range(4):
                    rotations += 1
                    query = pairs[query_index]
                    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                    try:
                        reasons = gen.lesson_identifiable(deepcopy(demos), deepcopy(query))
                    except Exception as exc:
                        hook_failures.append({
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "query_index": query_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        })
                        reasons = []
                    if reasons:
                        hook_failures.append({
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "query_index": query_index,
                            "reasons": list(reasons),
                        })

                    for name, competitor in gen.LESSON_COMPETITORS.items():
                        try:
                            fits_demos = all(
                                competitor(deepcopy(pair["input"])) == pair["output"]
                                for pair in demos
                            )
                            changes_query = (
                                competitor(deepcopy(query["input"])) != query["output"]
                            )
                        except Exception as exc:
                            competitor_errors.append({
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "competitor": name,
                                "error": f"{type(exc).__name__}: {exc}",
                            })
                            continue
                        if fits_demos and changes_query:
                            ambiguities.append({
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "competitor": name,
                            })

    return {
        "bands": band_values,
        "seeds": seed_values,
        "starts": start_values,
        "lessons": lessons,
        "rotations": rotations,
        "unique_inputs": len(unique_inputs),
        "ambiguities": ambiguities,
        "hook_failures": hook_failures,
        "competitor_errors": competitor_errors,
        "status": (
            "PASS"
            if not ambiguities and not hook_failures and not competitor_errors
            else "FAIL"
        ),
    }


def run_probe(
    *,
    generator_path: Path | str | None = None,
    seeds: Iterable[int] = range(10),
    starts: Iterable[int] = range(12),
) -> dict[str, Any]:
    gen, resolved_path = load_generator(generator_path)
    return {
        "schema": "arc-projection-reference-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(resolved_path),
        "generator_version": getattr(gen, "VERSION", None),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "canonical_shortcuts": _canonical_report(gen),
        "counterexample": _counterexample_report(gen),
        "rotations": _rotation_report(gen, seeds=seeds, starts=starts),
    }


def _parse_range(text: str) -> range:
    parts = text.split(":")
    if len(parts) not in (2, 3):
        raise argparse.ArgumentTypeError("range must be START:STOP or START:STOP:STEP")
    try:
        values = [int(part) for part in parts]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    result = range(*values)
    if len(result) == 0:
        raise argparse.ArgumentTypeError("range must contain at least one integer")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=None)
    parser.add_argument("--seeds", type=_parse_range, default=range(10), metavar="START:STOP[:STEP]")
    parser.add_argument("--starts", type=_parse_range, default=range(12), metavar="START:STOP[:STEP]")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = run_probe(generator_path=args.generator, seeds=args.seeds, starts=args.starts)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["rotations"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
