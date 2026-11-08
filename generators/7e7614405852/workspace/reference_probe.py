#!/usr/bin/env python3
"""Source-bound semantic probe for task 7e7614405852.

This intentionally does not call the Racket rule or canonical-data helpers.  It
implements a tiny independent row scanner, samples the production generator in
every difficulty band, verifies exact axis recovery, and saves one concrete
counterexample for every declared lesson rival.  Future reviewers can rerun it
against a modified ``../generator.py`` and diff the JSON report.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Sequence

TASK_HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_HOME / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "task_7e7614405852_generator", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = _load_generator()


def reference_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent implementation of the written exact-horizontal-triple rule."""
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        col = 0
        while col < len(row):
            color = row[col]
            if color == 0:
                col += 1
                continue
            stop = col + 1
            while stop < len(row) and row[stop] == color:
                stop += 1
            if stop - col == 3:
                output[row_index][col + 1] = 8
            col = stop
    return output


def _sample_seed(band: str | None, index: int) -> int:
    digest = hashlib.sha256(
        f"7e7614405852:reference-probe:v1:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:14], 16)


def _grid_key(grid: Sequence[Sequence[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def audit(per_band: int = 32) -> dict[str, Any]:
    """Audit ordinary draws and retain executable rival counterexamples."""
    if type(per_band) is not int or per_band < 1:
        raise ValueError("per_band must be a positive integer")

    report: dict[str, Any] = {
        "task_id": generator.TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "samples_per_band": per_band,
        "bands": {},
        "counterexamples": {},
        "failures": [],
    }

    for band in (None, "easy", "medium", "hard"):
        band_name = "none" if band is None else band
        unique: set[str] = set()
        invalid = 0
        oracle_mismatches = 0
        witness_hits = {name: 0 for name in generator.SEMANTIC_WITNESSES}
        rival_refutations = {name: 0 for name in generator.LESSON_COMPETITORS}
        profiles: dict[str, int] = {}

        for index in range(per_band):
            seed = _sample_seed(band, index)
            grid = generator.generate(seed, index, difficulty=band)
            unique.add(_grid_key(grid))
            errors = generator.self_check(grid)
            if errors:
                invalid += 1
                report["failures"].append(
                    {
                        "band": band_name,
                        "index": index,
                        "kind": "self_check",
                        "errors": errors,
                    }
                )
                continue

            observed = generator.observe_overrides(grid)
            profile = f"{observed['grid_h']}x{observed['grid_w']}:colors={len({v for row in grid for v in row})}"
            profiles[profile] = profiles.get(profile, 0) + 1
            truth = reference_output(grid)
            if truth != generator._apply_rule(grid):
                oracle_mismatches += 1
                report["failures"].append(
                    {
                        "band": band_name,
                        "index": index,
                        "kind": "oracle_mismatch",
                    }
                )

            for name, predicate in generator.SEMANTIC_WITNESSES.items():
                if predicate(deepcopy(grid)):
                    witness_hits[name] += 1
                else:
                    report["failures"].append(
                        {
                            "band": band_name,
                            "index": index,
                            "kind": "missing_default_witness",
                            "name": name,
                        }
                    )

            for name, rival in generator.LESSON_COMPETITORS.items():
                rival_output = rival(deepcopy(grid))
                if rival_output != truth:
                    rival_refutations[name] += 1
                    report["counterexamples"].setdefault(
                        name,
                        {
                            "band": band_name,
                            "seed": seed,
                            "sample_index": index,
                            "observed_axes": observed,
                            "input": grid,
                            "reference_output": truth,
                            "rival_output": rival_output,
                        },
                    )
                else:
                    report["failures"].append(
                        {
                            "band": band_name,
                            "index": index,
                            "kind": "rival_survived_default_draw",
                            "name": name,
                        }
                    )

        report["bands"][band_name] = {
            "samples": per_band,
            "unique_inputs": len(unique),
            "invalid": invalid,
            "oracle_mismatches": oracle_mismatches,
            "witness_hits": witness_hits,
            "rival_refutations": rival_refutations,
            "profiles": dict(sorted(profiles.items())),
        }

    missing = set(generator.LESSON_COMPETITORS) - set(report["counterexamples"])
    for name in sorted(missing):
        report["failures"].append(
            {"kind": "no_counterexample_retained", "name": name}
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=32)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(args.per_band)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
