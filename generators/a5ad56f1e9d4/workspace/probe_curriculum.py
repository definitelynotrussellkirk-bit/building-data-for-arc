#!/usr/bin/env python3
"""Replayable, Python-only curriculum probe for a5ad56f1e9d4.

This checks generator ownership, exact-axis construction, and every held-out
query rotation in consecutive four-pair windows.  Generated labels come from
the task's Python mirror, so this is a fast authoring diagnostic rather than
independent Racket-authority evidence; pair it with the source-bound battery
and lesson-census before making acceptance claims.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from typing import Any


TASK_ID = "a5ad56f1e9d4"
BANDS = ("easy", "medium", "hard")
AXIS_VALUES = {
    "rect_h": (2, 3, 4),
    "rect_w": (2, 3, 4),
    "contact_mode": ("touching", "gapped"),
    "tie_mode": ("avoid", "include"),
    "marker_order": ("lower_first", "lower_second"),
}


def _bootstrap() -> None:
    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        candidates = (
            parent,
            parent / "shared" / "runtime",
            parent / "repo" / "src",
            parent / "repo" / "shared" / "runtime",
        )
        for candidate in candidates:
            if candidate.is_dir() and str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))


_bootstrap()
from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    local = Path(__file__).resolve().parents[1] / "generator.py"
    if local.is_file():
        spec = importlib.util.spec_from_file_location(f"probe_generator_{TASK_ID}", local)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load generator from {local}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def run_probe(samples_per_band: int) -> dict[str, Any]:
    if samples_per_band < 4:
        raise ValueError("samples-per-band must be at least 4")

    gen = _load_generator()
    source = Path(gen.__file__).resolve()
    root = find_root(__file__)
    canonical = canonical_pairs(TASK_ID, root=root)

    canonical_failures: list[dict[str, Any]] = []
    for index, pair in enumerate(canonical):
        problems = list(gen.self_check(pair["input"]))
        if gen.rule_mirror(pair["input"]) != pair["output"]:
            problems.append("Python mirror differs from canonical output")
        if problems:
            canonical_failures.append({"pair": index, "problems": problems})

    rival_fit = {
        name: sum(rival(pair["input"]) == pair["output"] for pair in canonical)
        for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }

    exact_failures: list[dict[str, Any]] = []
    exact_requested = 0
    for sample_index, values in enumerate(itertools.product(*AXIS_VALUES.values())):
        requested = dict(zip(AXIS_VALUES, values))
        exact_requested += 1
        try:
            grid = gen.generate(
                81173,
                sample_index,
                difficulty=BANDS[sample_index % len(BANDS)],
                **requested,
            )
            problems = list(gen.self_check(grid))
            observed = gen.observe_overrides(grid)
            if observed != requested:
                problems.append(f"observed {observed!r}, requested {requested!r}")
        except Exception as exc:  # retained in the report for authoring diagnosis
            problems = [f"{type(exc).__name__}: {exc}"]
        if problems:
            exact_failures.append({"requested": requested, "problems": problems})

    checked_windows = 0
    checked_rotations = 0
    ambiguous: list[dict[str, Any]] = []
    witness_counts = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for band_index, band in enumerate(BANDS):
        pairs = []
        for sample_index in range(samples_per_band):
            grid = gen.generate(20261006 + band_index, sample_index, difficulty=band)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                witness_counts[name] += bool(witness(grid))
        for start in range(samples_per_band - 3):
            window = pairs[start : start + 4]
            checked_windows += 1
            for query_index in range(4):
                checked_rotations += 1
                demos = [pair for index, pair in enumerate(window) if index != query_index]
                reasons = gen.lesson_identifiable(demos, window[query_index])
                if reasons:
                    ambiguous.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                        }
                    )

    failures = len(canonical_failures) + len(exact_failures) + len(ambiguous)
    return {
        "schema": "a5ad56f1e9d4-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "diagnostic_scope": (
            "Python mirror and declared rivals only; use the source-bound Racket "
            "battery/census for authority evidence."
        ),
        "canonical": {
            "owned_and_mirrored": f"{len(canonical) - len(canonical_failures)}/{len(canonical)}",
            "failures": canonical_failures,
            "declared_rival_fit": rival_fit,
        },
        "exact_axes": {
            "requested": exact_requested,
            "passed": exact_requested - len(exact_failures),
            "failures": exact_failures,
        },
        "lessons": {
            "samples_per_band": samples_per_band,
            "demonstrations": 3,
            "checked_windows": checked_windows,
            "checked_rotations": checked_rotations,
            "ambiguous_rotations": len(ambiguous),
            "ambiguities": ambiguous,
            "witness_counts": witness_counts,
        },
        "status": "pass" if failures == 0 else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-band", type=int, default=15)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = run_probe(args.samples_per_band)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"{report['status']}: {report['exact_axes']['passed']}/"
        f"{report['exact_axes']['requested']} exact products; "
        f"{report['lessons']['ambiguous_rotations']}/"
        f"{report['lessons']['checked_rotations']} ambiguous rotations"
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
