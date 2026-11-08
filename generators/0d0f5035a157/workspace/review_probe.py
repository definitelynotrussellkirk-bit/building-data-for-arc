#!/usr/bin/env python3
"""Source-bound probes for the 0d0f5035a157 teaching distribution.

This companion intentionally reads rival and witness declarations from the
selected generator instead of maintaining a second name list.  It checks:

* every declared canonical shortcut against every usable canonical pair;
* every cyclic schedule start and every query rotation in a four-pair window;
* exact realization of representative joint override boundaries in every band;
* deterministic materialization and input uniqueness statistics.

It is finite evidence against the declared rivals, not a proof of unique
induction over all possible rules.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "0d0f5035a157"
HERE = Path(__file__).resolve()
TASK_HOME = HERE.parents[1]
REPO = HERE.parents[3]


def _load_generator(path: Path | None = None):
    source = path or (TASK_HOME / "generator.py")
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}_probe", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    try:
        from reviewer_support import canonical_pairs, find_root
    except ImportError:
        rows = []
        with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
        if len(rows) != 1:
            raise RuntimeError(f"expected one canonical row for {TASK_ID}, found {len(rows)}")
        return [*rows[0]["train"], *rows[0]["test"]]
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _grid_key(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _pair(generator, seed: int, sample_index: int, band):
    grid = generator.generate(seed, sample_index, difficulty=band)
    replay = generator.generate(seed, sample_index, difficulty=band)
    if grid != replay:
        raise AssertionError(
            f"nondeterministic draw: seed={seed} index={sample_index} band={band!r}"
        )
    errors = generator.self_check(grid, difficulty=band)
    if errors:
        raise AssertionError(
            f"self_check rejected draw seed={seed} index={sample_index} "
            f"band={band!r}: {errors}"
        )
    return {"input": grid, "output": generator.rule_mirror(grid)}


def run_probe(generator, canonical_pairs: list[dict[str, Any]], *, seeds_per_band: int = 16) -> dict[str, Any]:
    shortcuts = dict(getattr(generator, "CANONICAL_SHORTCUTS", {}))
    competitors = dict(getattr(generator, "LESSON_COMPETITORS", {}))
    canonical_failures: list[dict[str, Any]] = []
    for name, rival in sorted(shortcuts.items()):
        for index, pair in enumerate(canonical_pairs):
            if rival(pair["input"]) != pair["output"]:
                canonical_failures.append({"rival": name, "pair_index": index})

    bands = (None, "easy", "medium", "hard")
    period = len(getattr(generator, "SCHEDULE_PROFILES", ())) or 1
    window_size = int(getattr(generator, "EXAMPLES_NEEDED", 3)) + 1
    ambiguous: list[dict[str, Any]] = []
    hook_failures: list[dict[str, Any]] = []
    input_keys: set[str] = set()
    windows = 0
    rotations = 0

    for band_index, band in enumerate(bands):
        for seed_offset in range(seeds_per_band):
            seed = 910_000 + band_index * 10_000 + seed_offset
            for cyclic_start in range(period):
                base = seed_offset * period + cyclic_start
                pairs = [
                    _pair(generator, seed, base + offset, band)
                    for offset in range(window_size)
                ]
                windows += 1
                input_keys.update(_grid_key(pair["input"]) for pair in pairs)
                for query_index, query in enumerate(pairs):
                    rotations += 1
                    demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    reasons = generator.lesson_identifiable(demos, query)
                    if reasons:
                        hook_failures.append(
                            {
                                "band": band,
                                "seed": seed,
                                "cyclic_start": cyclic_start,
                                "query_index": query_index,
                                "reasons": reasons,
                            }
                        )
                    surviving = [
                        name
                        for name, rival in sorted(competitors.items())
                        if all(rival(pair["input"]) == pair["output"] for pair in demos)
                    ]
                    if surviving:
                        ambiguous.append(
                            {
                                "band": band,
                                "seed": seed,
                                "cyclic_start": cyclic_start,
                                "query_index": query_index,
                                "surviving_rivals": surviving,
                            }
                        )

    override_cases = (
        {
            "grid_h": 5,
            "grid_w": 8,
            "palette_size": 1,
            "max_cells_per_row": 3,
            "n_empty_rows": 0,
            "n_packed_rows": 0,
        },
        {
            "grid_h": 10,
            "grid_w": 14,
            "palette_size": 9,
            "max_cells_per_row": 7,
            "n_empty_rows": 2,
            "n_packed_rows": 2,
        },
        {
            "grid_h": 6,
            "grid_w": 9,
            "palette_size": 8,
            "max_cells_per_row": 5,
            "n_empty_rows": 1,
            "n_packed_rows": 1,
        },
    )
    override_failures: list[dict[str, Any]] = []
    for band in bands:
        for case_index, expected in enumerate(override_cases):
            try:
                grid = generator.generate(
                    812_000 + case_index,
                    case_index,
                    difficulty=band,
                    **expected,
                )
                observed = generator.observe_overrides(grid)
                errors = generator.self_check(grid, difficulty=band)
            except Exception as exc:  # Report, do not obscure which joint case failed.
                override_failures.append(
                    {
                        "band": band,
                        "case_index": case_index,
                        "exception": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            if observed != expected or errors:
                override_failures.append(
                    {
                        "band": band,
                        "case_index": case_index,
                        "expected": expected,
                        "observed": observed,
                        "self_check": errors,
                    }
                )

    failures = bool(canonical_failures or ambiguous or hook_failures or override_failures)
    source_path = Path(generator.__file__).resolve()
    return {
        "schema": "0d0f5035a157_review_probe/1",
        "task_id": TASK_ID,
        "status": "fail" if failures else "pass",
        "generator_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "seeds_per_band": seeds_per_band,
        "bands": ["default" if band is None else band for band in bands],
        "schedule_period": period,
        "window_size": window_size,
        "windows_checked": windows,
        "rotations_checked": rotations,
        "unique_inputs": len(input_keys),
        "canonical_pairs_checked": len(canonical_pairs),
        "canonical_shortcuts_checked": sorted(shortcuts),
        "lesson_competitors_checked": sorted(competitors),
        "canonical_shortcut_failures": canonical_failures,
        "ambiguous_rotations": len(ambiguous),
        "ambiguities": ambiguous,
        "hook_failures": hook_failures,
        "override_cases_checked": len(bands) * len(override_cases),
        "override_failures": override_failures,
        "limitation": (
            "Finite check of source-declared rivals and representative exact joint "
            "override boundaries; not a proof of universal rule identifiability."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--seeds-per-band", type=int, default=16)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds_per_band < 1:
        parser.error("--seeds-per-band must be positive")
    report = run_probe(
        _load_generator(args.generator),
        _canonical_pairs(),
        seeds_per_band=args.seeds_per_band,
    )
    payload = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
