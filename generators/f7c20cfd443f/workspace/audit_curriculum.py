"""Racket-free audit for the f7c20cfd443f teaching curriculum.

This is intentionally task-local.  It pins the Python mirror to every canonical
pair, measures the default distribution, checks scheduled lesson windows, and
verifies that each named competitor is falsified.  It is useful on review hosts
where the protected Racket runtime is unavailable; it does not replace the
canonical Racket execution gates.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


TASK_ID = "f7c20cfd443f"
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    path = REPO / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [pair for split in ("train", "test") for pair in row[split]]
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _signature(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def audit(per_band: int, lesson_starts: int) -> dict[str, Any]:
    gen = _load_generator()
    failures: list[str] = []
    canonical_results = []
    for index, pair in enumerate(_canonical_pairs()):
        self_errors = gen.self_check(pair["input"])
        mirror_ok = gen.rule_mirror(pair["input"]) == pair["output"]
        canonical_results.append(
            {"index": index, "self_check": self_errors, "mirror_ok": mirror_ok}
        )
        if self_errors or not mirror_ok:
            failures.append(f"canonical pair {index} rejected or mismatched")

    bands: dict[str, Any] = {}
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(900_000 + i, i, difficulty=band) for i in range(per_band)]
        strict_failures = [
            {"index": i, "errors": gen.strict_canonical_like(grid)}
            for i, grid in enumerate(grids)
            if gen.strict_canonical_like(grid)
        ]
        dimensions = Counter((len(grid), len(grid[0])) for grid in grids)
        seed_counts = Counter(
            sum(value == 5 for row in grid for value in row) for grid in grids
        )
        profiles = Counter(
            gen.schedule_profile(900_000 + i, i, band) for i in range(per_band)
        )
        witness_hits = {
            name: sum(bool(predicate(grid)) for grid in grids)
            for name, predicate in gen.SEMANTIC_WITNESSES.items()
        }
        profile_contract_failures: list[dict[str, Any]] = []
        for index, grid in enumerate(grids):
            profile = gen.schedule_profile(900_000 + index, index, band)
            cells = [
                (row, col)
                for row, values in enumerate(grid)
                for col, value in enumerate(values)
                if value == 5
            ]
            on_edge = any(
                row in (0, len(grid) - 1) or col in (0, len(grid[0]) - 1)
                for row, col in cells
            )
            overlap = any(
                max(abs(a[0] - b[0]), abs(a[1] - b[1])) == 2
                for left, a in enumerate(cells)
                for b in cells[left + 1 :]
            )
            off_lattice = any(
                row % 3 != 1 or col % 3 != 1 for row, col in cells
            )
            violated = (
                (profile == "canonical_anchor" and (off_lattice or on_edge or overlap))
                or (profile == "off_lattice" and (not off_lattice or on_edge or overlap))
                or (profile == "edge_clip" and (not on_edge or overlap))
                or (profile == "overlap" and (on_edge or not overlap))
            )
            if violated:
                profile_contract_failures.append(
                    {"index": index, "profile": profile, "seeds": cells}
                )
        unique = len({_signature(grid) for grid in grids})
        bands[band] = {
            "draws": per_band,
            "strict_failures": strict_failures,
            "dimensions": {f"{h}x{w}": count for (h, w), count in dimensions.items()},
            "seed_counts": dict(sorted(seed_counts.items())),
            "profiles": dict(profiles),
            "witness_hits": witness_hits,
            "profile_contract_failures": profile_contract_failures,
            "unique": unique,
        }
        if strict_failures:
            failures.append(f"{band}: {len(strict_failures)} strict failures")
        expected_dimensions = Counter(
            gen.PROFILE_DIMENSIONS[band][index % len(gen.SCHEDULE_PROFILES)]
            for index in range(per_band)
        )
        if dimensions != expected_dimensions:
            failures.append(
                f"{band}: dimensions differ from the declared controlled schedule"
            )
        if dimensions[(9, 9)] < per_band // len(gen.SCHEDULE_PROFILES):
            failures.append(f"{band}: fewer than one canonical 9x9 anchor per cycle")
        if any(count not in (3, 4) for count in seed_counts):
            failures.append(f"{band}: ordinary seed count outside 3..4")
        if set(profiles) != set(gen.SCHEDULE_PROFILES):
            failures.append(f"{band}: missing schedule profile")
        if any(hit == 0 for hit in witness_hits.values()):
            failures.append(f"{band}: declared witness never fired")
        if profile_contract_failures:
            failures.append(
                f"{band}: {len(profile_contract_failures)} profile-isolation failures"
            )
        if unique < max(1, int(per_band * 0.9)):
            failures.append(f"{band}: uniqueness below 90% ({unique}/{per_band})")

    lesson_results: list[dict[str, Any]] = []
    for band in ("easy", "medium", "hard"):
        for start in range(lesson_starts):
            grids = [
                gen.generate(777_777, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            demos = [
                {"input": grid, "output": gen.rule_mirror(grid)}
                for grid in grids[: gen.EXAMPLES_NEEDED]
            ]
            reasons = gen.lesson_identifiable(demos, {"input": grids[-1]})
            survivors = [
                name
                for name, competitor in gen.LESSON_COMPETITORS.items()
                if all(competitor(demo["input"]) == demo["output"] for demo in demos)
            ]
            lesson_results.append(
                {
                    "band": band,
                    "start": start,
                    "profiles": [
                        gen.schedule_profile(777_777, start + offset, band)
                        for offset in range(gen.EXAMPLES_NEEDED)
                    ],
                    "reasons": reasons,
                    "survivors": survivors,
                }
            )
            if reasons or survivors:
                failures.append(
                    f"{band} lesson start {start}: reasons={reasons}, survivors={survivors}"
                )

    return {
        "schema": "f7c20cfd443f-curriculum-audit-v1",
        "task_id": TASK_ID,
        "version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "status": "PASS" if not failures else "FAIL",
        "canonical": canonical_results,
        "bands": bands,
        "lessons": lesson_results,
        "failures": failures,
        "limitation": (
            "Uses a Python mirror pinned to canonical pairs; run the protected "
            "Racket gates before approval when a Racket runtime is available."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=60)
    parser.add_argument("--lesson-starts", type=int, default=16)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(args.per_band, args.lesson_starts)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
    print(
        f"{report['status']} {TASK_ID} v{report['version']}: "
        f"{sum(v['draws'] for v in report['bands'].values())} draws, "
        f"{len(report['lessons'])} lessons, {len(report['failures'])} failures"
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
