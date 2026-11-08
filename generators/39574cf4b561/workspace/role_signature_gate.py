#!/usr/bin/env python3
"""Task-local canonical role-signature gate for generator 39574cf4b561.

The generic distribution gate compares coarse canvas/palette marginals.  That
was insufficient here: the baseline generator produced only colors occurring
three times, while every official input also has one singleton color.  This
probe compares the histogram of per-color multiplicities directly.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

TASK_ID = "39574cf4b561"
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
BANDS = ("easy", "medium", "hard")


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"role_gate_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_inputs():
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [
                    pair["input"]
                    for pair in row.get("train", []) + row.get("test", [])
                ]
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def role_signature(grid) -> tuple[tuple[int, int], ...]:
    """Return ``(cell multiplicity, number of colors)`` pairs.

    Background 0 is excluded.  For example, one singleton distractor and
    three rectangle colors occurring three times each is
    ``((1, 1), (3, 3))``.
    """
    if not grid or not grid[0]:
        return ()
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("ragged grid")
    color_counts = Counter(
        value for row in grid for value in row if value != 0
    )
    multiplicities = Counter(color_counts.values())
    return tuple(sorted(multiplicities.items()))


def _json_signature(signature):
    return [list(item) for item in signature]


def audit(*, draws_per_band: int = 20) -> dict:
    if draws_per_band < 1:
        raise ValueError("draws_per_band must be positive")
    generator = _load_generator()
    canonical = frozenset(role_signature(grid) for grid in canonical_inputs())
    bands = {}
    passed = True
    for band_index, band in enumerate(BANDS):
        observed = Counter()
        invalid = []
        for sample_index in range(draws_per_band):
            grid = generator.generate(
                880_000 + band_index * 10_000 + sample_index,
                sample_index,
                difficulty=band,
            )
            signature = role_signature(grid)
            observed[signature] += 1
            errors = generator.self_check(grid, difficulty=band)
            if errors:
                invalid.append(
                    {"sample_index": sample_index, "errors": list(errors)}
                )
        observed_set = set(observed)
        missing = sorted(canonical - observed_set)
        unexpected = sorted(observed_set - canonical)
        if missing or unexpected or invalid:
            passed = False
        bands[band] = {
            "draws": draws_per_band,
            "seen": [
                {
                    "signature": _json_signature(signature),
                    "count": count,
                }
                for signature, count in sorted(observed.items())
            ],
            "missing": [_json_signature(value) for value in missing],
            "unexpected": [_json_signature(value) for value in unexpected],
            "invalid": invalid,
        }
    return {
        "schema": "task_role_signature_gate/1",
        "task_id": TASK_ID,
        "status": "PASS" if passed else "FAIL",
        "canonical_signatures": [
            _json_signature(value) for value in sorted(canonical)
        ],
        "bands": bands,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws-per-band", type=int, default=20)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    report = audit(draws_per_band=args.draws_per_band)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
