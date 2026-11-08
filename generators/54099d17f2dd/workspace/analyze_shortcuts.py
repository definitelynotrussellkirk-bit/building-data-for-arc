#!/usr/bin/env python3
"""Reproduce canonical ambiguity and find exact emitted counterexamples.

This is a durable reviewer tool rather than a one-off note. It verifies that
all task-declared shortcuts fit every canonical pair, searches ordinary
scheduled generator draws for the first disagreement, and records exact inputs,
outputs, differing cells, override observations, and optional Racket parity.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "54099d17f2dd"
HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _differences(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        return [[-1, -1, len(left), len(right)]]
    return [
        [r, c, left[r][c], right[r][c]]
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] != right[r][c]
    ]


def analyze(*, use_racket: bool = True) -> dict[str, Any]:
    gen = _load(HOME / "generator.py", f"generator_{TASK_ID}")
    probe = _load(HOME / "workspace" / "reference_probe.py", f"probe_{TASK_ID}")
    canonical = probe.canonical_pairs()

    report: dict[str, Any] = {
        "task_id": TASK_ID,
        "rule_hash": gen.RULE_HASH,
        "canonical_pair_count": len(canonical),
        "shortcuts": {},
        "all_declared_shortcuts_fit_canonical": True,
        "generator_emits_counterexamples": True,
        "racket_checked": False,
    }

    counterexample_grids: list[list[list[int]]] = []
    counterexample_refs: list[tuple[str, dict[str, Any]]] = []

    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        canonical_checks = []
        for index, pair in enumerate(canonical):
            rival_output = rival(pair["input"])
            fits = rival_output == pair["output"]
            canonical_checks.append({"pair_index": index, "fits": fits})
        fits_all = all(item["fits"] for item in canonical_checks)

        first: dict[str, Any] | None = None
        for difficulty in ("easy", "medium", "hard"):
            if first is not None:
                break
            for sample_index in range(32):
                seed = 5409900 + sample_index
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                authority = probe.reference_output(grid)
                rival_output = rival(grid)
                if authority == rival_output:
                    continue
                first = {
                    "seed": seed,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                    "schedule_profile": gen.schedule_profile(seed, sample_index, difficulty),
                    "observed_axes": gen.observe_overrides(grid),
                    "self_check_errors": gen.self_check(grid),
                    "input": grid,
                    "authority_output": authority,
                    "rival_output": rival_output,
                    "difference_cells": _differences(authority, rival_output),
                    "racket_matches_authority": None,
                }
                counterexample_grids.append(grid)
                counterexample_refs.append((name, first))
                break

        report["shortcuts"][name] = {
            "fits_all_canonical_pairs": fits_all,
            "canonical_checks": canonical_checks,
            "first_generated_counterexample": first,
        }
        report["all_declared_shortcuts_fit_canonical"] &= fits_all
        report["generator_emits_counterexamples"] &= first is not None

    if use_racket:
        grids = [pair["input"] for pair in canonical] + counterexample_grids
        racket = probe.racket_outputs(grids)
        python = [probe.reference_output(grid) for grid in grids]
        if racket != python:
            raise AssertionError("independent Python oracle disagrees with canonical Racket authority")
        report["racket_checked"] = True
        offset = len(canonical)
        for index, (_, finding) in enumerate(counterexample_refs):
            finding["racket_matches_authority"] = racket[offset + index] == finding["authority_output"]

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    parser.add_argument(
        "--no-racket",
        action="store_true",
        help="skip canonical Racket parity (the independent Python oracle remains active)",
    )
    parser.add_argument("--out", type=Path, help="also write JSON to this path")
    args = parser.parse_args()
    report = analyze(use_racket=not args.no_racket)
    text = json.dumps(report, sort_keys=True, indent=None if args.compact else 2)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
