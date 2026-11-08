#!/usr/bin/env python3
"""One-command qualification probe for bfef8519fe18.

This is intentionally task-local and declaration-driven.  It checks the final
source hash, canonical compatibility, exact schedule coverage, every cyclic
lesson start and query rotation, canonical-shortcut fit/counterexamples, and a
small distribution census.  ``--racket`` additionally labels generated inputs
with the selected canonical authority and compares those labels to rule_mirror.

Run from the packet repository through the supplied wrapper, for example:

    python3 review.py run python3 generators/bfef8519fe18/workspace/qualify.py \
        --per-band 32 --racket --out ../checks/bfef8519fe18_qualification.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time
from typing import Any

from reviewer_support import canonical_pairs, find_root


TASK_ID = "bfef8519fe18"
HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE.parent / "generator.py"


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"qualification_{TASK_ID}_{hashlib.sha256(path.read_bytes()).hexdigest()[:12]}",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator source at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _pair(module: Any, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": module.rule_mirror(grid)}


def _counter_to_dict(counter: Counter[Any]) -> dict[str, int]:
    return {
        json.dumps(key, sort_keys=True) if not isinstance(key, str) else key: value
        for key, value in sorted(counter.items(), key=lambda item: repr(item[0]))
    }


def qualify(
    source: Path,
    *,
    per_band: int,
    use_racket: bool,
    racket_samples: int,
) -> tuple[dict[str, Any], list[str]]:
    root = find_root(__file__)
    module = _load_generator(source)
    failures: list[str] = []
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)

    canonical_rows: list[dict[str, Any]] = []
    for index, pair in enumerate(canonical):
        check = list(module.self_check(deepcopy(pair["input"])))
        mirror = module.rule_mirror(deepcopy(pair["input"]))
        row = {
            "index": index,
            "profile": list(_profile(pair["input"])),
            "self_check_errors": check,
            "mirror_matches_label": mirror == pair["output"],
        }
        canonical_rows.append(row)
        if check:
            failures.append(f"canonical pair {index} rejected: {check}")
        if mirror != pair["output"]:
            failures.append(f"canonical pair {index} disagrees with rule_mirror")

    shortcut_rows: dict[str, Any] = {}
    shortcuts = dict(getattr(module, "CANONICAL_SHORTCUTS", {}))
    for name, solve in shortcuts.items():
        matches = [solve(deepcopy(pair["input"])) == pair["output"] for pair in canonical]
        shortcut_rows[name] = {
            "canonical_matches": matches,
            "fits_all_canonical": all(matches),
            "generated_counterexamples": 0,
            "first_counterexample": None,
        }
        if not all(matches):
            failures.append(f"declared canonical shortcut {name!r} does not fit all labels")

    bands = ("easy", "medium", "hard")
    layouts: Counter[str] = Counter()
    profiles: Counter[tuple[int, int, int]] = Counter()
    room_counts: Counter[int] = Counter()
    band_layouts: dict[str, Counter[str]] = {band: Counter() for band in bands}
    bad_grids: list[dict[str, Any]] = []
    generated: list[list[list[int]]] = []
    durations_ms: list[float] = []

    for band_index, band in enumerate(bands):
        for sample_index in range(per_band):
            seed = 1_000_000 + band_index * 100_000 + sample_index
            started = time.perf_counter()
            grid = module.generate(seed, sample_index, difficulty=band)
            durations_ms.append((time.perf_counter() - started) * 1000.0)
            errors = list(module.self_check(grid))
            if errors:
                bad_grids.append(
                    {
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "errors": errors,
                    }
                )
                continue
            observed = module.observe_overrides(grid)
            facts = module.scene_facts(grid)
            layout = str(observed["layout"])
            layouts[layout] += 1
            band_layouts[band][layout] += 1
            profiles[_profile(grid)] += 1
            room_counts[int(facts["room_count"])] += 1
            generated.append(grid)
            expected = module.rule_mirror(grid)
            if expected == grid:
                failures.append(
                    f"generated no-op at band={band} seed={seed} sample={sample_index}"
                )
            for name, solve in shortcuts.items():
                if solve(deepcopy(grid)) != expected:
                    entry = shortcut_rows[name]
                    entry["generated_counterexamples"] += 1
                    if entry["first_counterexample"] is None:
                        entry["first_counterexample"] = {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "layout": layout,
                            "profile": list(_profile(grid)),
                        }

    if bad_grids:
        failures.append(f"{len(bad_grids)} generated grids failed self_check")
    declared_layouts = set(getattr(module, "LAYOUTS", ()))
    raw_schedule = getattr(module, "_SCHEDULE", ())
    scheduled_layouts = {
        layout
        for row in raw_schedule
        if isinstance(row, (list, tuple)) and len(row) >= 4
        for layout in row[3]
    } or declared_layouts
    missing_scheduled = scheduled_layouts - set(layouts)
    unexpected_scheduled = set(layouts) - scheduled_layouts
    if missing_scheduled or unexpected_scheduled:
        failures.append(
            "default census schedule support mismatch: "
            f"missing={sorted(missing_scheduled)} "
            f"unexpected={sorted(unexpected_scheduled)}"
        )
    if set(room_counts) != {2, 3, 4}:
        failures.append(f"room-count support is {sorted(room_counts)}, expected [2, 3, 4]")
    for name, row in shortcut_rows.items():
        if row["generated_counterexamples"] == 0:
            failures.append(f"canonical shortcut {name!r} has no generated counterexample")

    examples_needed = int(getattr(module, "EXAMPLES_NEEDED", 3))
    lesson_size = examples_needed + 1
    period = int(getattr(module, "LESSON_SCHEDULE_PERIOD", 0))
    competitors = dict(getattr(module, "LESSON_COMPETITORS", {}))
    lesson_rows: list[dict[str, Any]] = []
    production_failures = 0
    rotation_failures = 0
    for start in range(period):
        pairs = [
            _pair(
                module,
                module.generate(
                    9_000_000 + start,
                    start + offset,
                    difficulty="medium",
                ),
            )
            for offset in range(lesson_size)
        ]
        production_reasons = list(
            module.lesson_identifiable(pairs[:examples_needed], pairs[examples_needed])
        )
        if production_reasons:
            production_failures += 1
        rotations: list[dict[str, Any]] = []
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            reasons = list(module.lesson_identifiable(demos, query))
            surviving = []
            for name, solve in competitors.items():
                if all(solve(deepcopy(pair["input"])) == pair["output"] for pair in demos):
                    if solve(deepcopy(query["input"])) != query["output"]:
                        surviving.append(name)
            if reasons or surviving:
                rotation_failures += 1
            rotations.append(
                {
                    "query_index": query_index,
                    "reasons": reasons,
                    "ambiguous_competitors": sorted(surviving),
                    "query_layout": module.observe_overrides(query["input"])["layout"],
                }
            )
        lesson_rows.append(
            {
                "start": start,
                "layouts": [
                    module.observe_overrides(pair["input"])["layout"] for pair in pairs
                ],
                "production_reasons": production_reasons,
                "rotations": rotations,
            }
        )
    if production_failures:
        failures.append(f"{production_failures}/{period} cyclic production lessons ambiguous")
    if rotation_failures:
        failures.append(
            f"{rotation_failures}/{period * lesson_size} cyclic query rotations ambiguous"
        )

    racket_report: dict[str, Any] | None = None
    if use_racket:
        from arcpuzzles import Catalog

        sample = generated[: min(racket_samples, len(generated))]
        receipt = Catalog(root).apply(
            TASK_ID,
            sample,
            reference="canonical",
            timeout=max(180, 15 * len(sample)),
        )
        outputs = [item["output"] for item in receipt["results"]]
        mirrors = [module.rule_mirror(grid) for grid in sample]
        racket_report = {
            "samples": len(sample),
            "rule_hash_matches_catalog": bool(receipt["rule_hash_matches_catalog"]),
            "mirror_matches": sum(left == right for left, right in zip(outputs, mirrors)),
        }
        if not racket_report["rule_hash_matches_catalog"]:
            failures.append("declared RULE_HASH does not match selected catalog authority")
        if racket_report["mirror_matches"] != len(sample):
            failures.append(
                f"Racket/Python mismatch on {len(sample) - racket_report['mirror_matches']} samples"
            )

    duration_summary = {
        "count": len(durations_ms),
        "mean_ms": statistics.fmean(durations_ms) if durations_ms else None,
        "p95_ms": (
            sorted(durations_ms)[max(0, int(0.95 * len(durations_ms)) - 1)]
            if durations_ms
            else None
        ),
        "max_ms": max(durations_ms) if durations_ms else None,
    }
    report = {
        "schema": "bfef8519fe18-qualification-v1",
        "task_id": TASK_ID,
        "generator": {
            "path": str(source),
            "sha256": _sha256(source),
            "version": getattr(module, "VERSION", None),
            "rule_hash": getattr(module, "RULE_HASH", None),
        },
        "settings": {
            "per_band": per_band,
            "bands": list(bands),
            "examples_needed": examples_needed,
            "lesson_size": lesson_size,
            "cyclic_starts": period,
            "racket": use_racket,
            "racket_samples": racket_samples if use_racket else 0,
        },
        "canonical": canonical_rows,
        "shortcuts": shortcut_rows,
        "distribution": {
            "draws": per_band * len(bands),
            "accepted": len(generated),
            "layouts": _counter_to_dict(layouts),
            "declared_layouts": sorted(declared_layouts),
            "scheduled_layouts": sorted(scheduled_layouts),
            "override_only_layouts": sorted(declared_layouts - scheduled_layouts),
            "layouts_by_band": {
                band: _counter_to_dict(counter) for band, counter in band_layouts.items()
            },
            "profiles": _counter_to_dict(profiles),
            "room_counts": _counter_to_dict(room_counts),
            "bad_grids": bad_grids,
            "generation_time": duration_summary,
        },
        "lessons": {
            "production_failures": production_failures,
            "rotation_failures": rotation_failures,
            "rows": lesson_rows,
        },
        "racket": racket_report,
        "failures": failures,
        "passed": not failures,
    }
    return report, failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--per-band", type=int, default=32)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--racket-samples", type=int, default=24)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.per_band < 8:
        parser.error("--per-band must be at least 8 to cover the schedule")
    if args.racket_samples < 1:
        parser.error("--racket-samples must be positive")

    report, failures = qualify(
        args.source.resolve(),
        per_band=args.per_band,
        use_racket=args.racket,
        racket_samples=args.racket_samples,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        out = args.out.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered)
    print(
        f"qualification {'PASS' if not failures else 'FAIL'}: "
        f"sha256={report['generator']['sha256']} "
        f"canonical={len(report['canonical'])} "
        f"draws={report['distribution']['draws']} "
        f"production_failures={report['lessons']['production_failures']} "
        f"rotation_failures={report['lessons']['rotation_failures']}"
    )
    for failure in failures:
        print(f"FAIL: {failure}")
    if args.out:
        print(f"report: {args.out.resolve()}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
