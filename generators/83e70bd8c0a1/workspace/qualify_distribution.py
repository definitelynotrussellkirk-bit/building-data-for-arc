#!/usr/bin/env python3
"""Task-local qualification probe for the anti-diagonal reflection sampler.

The shared lesson census intentionally keeps one query position.  This probe
complements it by rotating every member of each four-item lesson into the query
position, checking all declared rivals against the remaining three demos, and
reporting joint semantic-axis support plus canonical-profile coverage.

Run from anywhere::

    python3 generators/83e70bd8c0a1/workspace/qualify_distribution.py \
        --per-band 100 --out /tmp/83e70bd8c0a1-qualification.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

TASK_ID = "83e70bd8c0a1"
HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs  # noqa: E402

SOURCE = HERE.parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"qualification_{TASK_ID}", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

BANDS = ("easy", "medium", "hard")


def _seed(band: str, lesson_index: int) -> int:
    digest = hashlib.sha256(
        f"cyclic-qualification:v1:{TASK_ID}:{band}:{lesson_index}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big")


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _axis_key(observed: dict[str, Any]) -> str:
    return ",".join(f"{name}={observed[name]}" for name in sorted(observed))


def _boundary_override_failures() -> list[dict[str, Any]]:
    domains = {
        "grid_size": (5, 7),
        "diagonal_marks": (1, 3),
        "mirror_pairs": (1, 2),
        "singletons": (4, 5),
    }
    names = tuple(domains)
    failures: list[dict[str, Any]] = []
    case = 0
    for band in BANDS:
        for values in itertools.product(*(domains[name] for name in names)):
            requested = dict(zip(names, values))
            try:
                grid = GEN.generate(
                    7_000_000 + case,
                    case,
                    difficulty=band,
                    **requested,
                )
                observed = GEN.observe_overrides(grid)
                findings = GEN.self_check(grid, meta={"overrides": requested})
            except Exception as exc:  # pragma: no cover - diagnostic path
                failures.append(
                    {
                        "band": band,
                        "requested": requested,
                        "error": repr(exc),
                    }
                )
            else:
                if observed != requested or findings:
                    failures.append(
                        {
                            "band": band,
                            "requested": requested,
                            "observed": observed,
                            "self_check": findings,
                        }
                    )
            case += 1
    return failures


def qualify(per_band: int) -> dict[str, Any]:
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    canonical_profiles = {
        _profile(pair["input"])
        for pair in pairs
    }

    report: dict[str, Any] = {
        "schema": "task-local-cyclic-qualification-v1",
        "task_id": TASK_ID,
        "generator_version": GEN.VERSION,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "per_band": per_band,
        "items_per_lesson": GEN.EXAMPLES_NEEDED + 1,
        "query_rotations_per_lesson": GEN.EXAMPLES_NEEDED + 1,
        "canonical_profiles": [list(profile) for profile in sorted(canonical_profiles)],
        "bands": {},
        "override_boundary_failures": _boundary_override_failures(),
        "failures": [],
        "limits": [
            "Finite declared-rival probe, not a proof of universal induction.",
            "Outputs use the independently canonical-tested Python rule mirror; "
            "the shared Racket census remains the source-bound authority check.",
            "Joint-axis support is observational over this pinned sample.",
        ],
    }

    all_hashes: set[str] = set()
    for band in BANDS:
        profile_counts: Counter[str] = Counter()
        axis_counts: Counter[str] = Counter()
        witness_counts: Counter[str] = Counter()
        rival_refutations: Counter[str] = Counter()
        rotation_failures: list[dict[str, Any]] = []
        generated = 0

        for lesson_index in range(per_band):
            seed = _seed(band, lesson_index)
            items: list[dict[str, list[list[int]]]] = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                sample_index = lesson_index * (GEN.EXAMPLES_NEEDED + 1) + offset
                grid = GEN.generate(seed, sample_index, difficulty=band)
                findings = GEN.self_check(grid, difficulty=band)
                if findings:
                    report["failures"].append(
                        {
                            "kind": "self_check",
                            "band": band,
                            "lesson_index": lesson_index,
                            "offset": offset,
                            "findings": findings,
                        }
                    )
                generated += 1
                all_hashes.add(_grid_hash(grid))
                profile_counts[str(_profile(grid))] += 1
                axis_counts[_axis_key(GEN.observe_overrides(grid))] += 1
                for name, witness in GEN.SEMANTIC_WITNESSES.items():
                    if witness(grid):
                        witness_counts[name] += 1
                intended = GEN.rule_mirror(grid)
                for name, rival in GEN.SEMANTIC_RIVALS.items():
                    if rival(grid) != intended:
                        rival_refutations[name] += 1
                items.append({"input": grid, "output": intended})

            for query_index, query in enumerate(items):
                demos = [
                    item for index, item in enumerate(items)
                    if index != query_index
                ]
                reasons = GEN.lesson_identifiable(demos, query)
                surviving = [
                    name
                    for name, rival in GEN.LESSON_COMPETITORS.items()
                    if all(
                        rival(demo["input"]) == demo["output"]
                        for demo in demos
                    )
                ]
                if reasons or surviving:
                    rotation_failures.append(
                        {
                            "lesson_index": lesson_index,
                            "query_index": query_index,
                            "reasons": reasons,
                            "surviving_rivals": surviving,
                        }
                    )

        exact_hits = sum(
            count
            for text, count in profile_counts.items()
            if tuple(int(part.strip()) for part in text.strip("()").split(","))
            in canonical_profiles
        )
        report["bands"][band] = {
            "generated_items": generated,
            "unique_axis_combinations": len(axis_counts),
            "axis_counts": dict(sorted(axis_counts.items())),
            "profile_counts": dict(sorted(profile_counts.items())),
            "canonical_exact_hits": exact_hits,
            "witness_hits": dict(sorted(witness_counts.items())),
            "rival_refutations": dict(sorted(rival_refutations.items())),
            "rotations_checked": per_band * (GEN.EXAMPLES_NEEDED + 1),
            "rotation_failures": rotation_failures,
        }
        report["failures"].extend(
            {
                "kind": "cyclic_query_rotation",
                "band": band,
                **failure,
            }
            for failure in rotation_failures
        )

    report["unique_inputs"] = len(all_hashes)
    report["status"] = (
        "PASS"
        if not report["failures"] and not report["override_boundary_failures"]
        else "FAIL"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.per_band <= 0:
        parser.error("--per-band must be positive")

    report = qualify(args.per_band)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(
        f"{TASK_ID}: {report['status']} — "
        f"{report['unique_inputs']} unique inputs; "
        f"{sum(v['rotations_checked'] for v in report['bands'].values())} "
        "cyclic query rotations"
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
