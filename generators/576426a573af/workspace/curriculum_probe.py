#!/usr/bin/env python3
"""Audit every requested cyclic lesson window for 576426a573af.

Unlike the production-shaped shared lesson census, this small task-local probe
cheaply enumerates *all* starts in a bounded deterministic schedule.  It checks
an independent Python oracle, canonical anchoring, declared semantic witnesses,
and every declared lesson competitor. The independently implemented retained
audit rival is also checked even when a source omits its declaration. Four-query
lessons use only their four demonstrations. Labels here use an independent
Python oracle; production Racket execution is a separate check.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Iterable

PROBE_PATH = Path(__file__).resolve()
PROBE_SHA256 = hashlib.sha256(PROBE_PATH.read_bytes()).hexdigest()
for parent in (PROBE_PATH.parent, *PROBE_PATH.parents):
    # Portable snapshots also carry shared/runtime mirrors. Execution-layout
    # dependencies must win so the selected-source loader sees one source tree.
    if (parent / "puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(parent))
        break
    if (parent / "shared/runtime/puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(parent / "shared/runtime"))
        break
else:  # pragma: no cover - packaging contract
    raise RuntimeError("No independent puzzle_generators runtime found")

from reviewer_support import find_root, load_selected_generator  # noqa: E402

gen, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(
    "576426a573af", root=find_root(PROBE_PATH),
)
HOME = GENERATOR_SOURCE.parent


def official(grid: list[list[int]]) -> list[list[int]]:
    """Independent implementation of overlay(flip_ud(grid), grid)."""
    h = len(grid)
    out = copy.deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 and grid[h - 1 - r][c] != 0:
                out[r][c] = grid[h - 1 - r][c]
    return out


def _hash_grid(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def conflicting_orbits(grid) -> list[tuple[int, int, int]]:
    h = len(grid)
    return [
        (r, h - 1 - r, c)
        for r in range(h // 2)
        for c in range(len(grid[0]))
        if grid[r][c] != 0 and grid[h - 1 - r][c] != 0
        and grid[r][c] != grid[h - 1 - r][c]
    ]


def preserve_first_conflict_only(grid) -> list[list[int]]:
    """Independent implementation of the count-limited retained audit rival."""
    out = official(grid)
    for top, bottom, col in conflicting_orbits(grid)[1:]:
        out[top][col], out[bottom][col] = grid[bottom][col], grid[top][col]
    return out


def audit(
    *,
    seed: int = 17,
    starts: Iterable[int] = range(32),
    bands: Iterable[str | None] = ("easy", "medium", "hard"),
) -> dict:
    starts = tuple(int(start) for start in starts)
    bands = tuple(bands)
    competitors = dict(gen.LESSON_COMPETITORS)
    # A missing declaration must not hide the original audited failure.
    competitors["preserve_first_conflict_only"] = preserve_first_conflict_only
    witnesses = dict(gen.SEMANTIC_WITNESSES)
    refuted_windows = {name: 0 for name in competitors}
    witness_windows = {name: 0 for name in witnesses}
    rotation_refuted = {name: 0 for name in competitors}
    failures: list[dict] = []
    rotation_failures: list[dict] = []
    rotations = 0
    unique_inputs: set[str] = set()
    four_query_inputs: set[str] = set()
    four_query_failures: list[dict] = []
    four_query_refuted = {name: 0 for name in competitors}
    four_query_checks = 0
    conflict_histogram: dict[int, int] = {}
    measured_inputs: set[tuple[str | None, int]] = set()
    profile_counts = {name: 0 for name in gen.SCHEDULE_PROFILES}

    for band in bands:
        for start in starts:
            episode_grids = [
                gen.generate(seed, index, difficulty=band)
                for index in range(start, start + gen.EXAMPLES_NEEDED + 4)
            ]
            grids = episode_grids[: gen.EXAMPLES_NEEDED + 1]
            demos = [{"input": grid, "output": official(grid)} for grid in grids[:-1]]
            query = {"input": grids[-1], "output": official(grids[-1])}
            unique_inputs.update(_hash_grid(grid) for grid in grids)
            for index in range(start, start + gen.EXAMPLES_NEEDED):
                profile_counts[gen.schedule_profile(seed, index, band)] += 1

            context = {"band": band, "start": start}
            for offset, grid in enumerate(episode_grids):
                errors = gen.self_check(grid)
                if errors:
                    failures.append({**context, "kind": "self_check", "offset": offset, "errors": errors})
                if gen.rule_mirror(grid) != official(grid):
                    failures.append({**context, "kind": "oracle_mismatch", "offset": offset})
                key = (band, start + offset)
                if key not in measured_inputs:
                    measured_inputs.add(key)
                    count = len(conflicting_orbits(grid))
                    conflict_histogram[count] = conflict_histogram.get(count, 0) + 1

            strict_count = sum(gen.strict_canonical_like(grid) == [] for grid in grids[:-1])
            if strict_count != 1:
                failures.append({**context, "kind": "strict_profile_count", "actual": strict_count})

            for name, predicate in witnesses.items():
                if any(predicate(grid) for grid in grids[:-1]):
                    witness_windows[name] += 1
                else:
                    failures.append({**context, "kind": "missing_witness", "name": name})

            for name, rival in competitors.items():
                if any(rival(pair["input"]) != pair["output"] for pair in demos):
                    refuted_windows[name] += 1
                else:
                    failures.append({**context, "kind": "surviving_competitor", "name": name})

            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                failures.append({**context, "kind": "lesson_identifiable", "reasons": reasons})

            pairs5 = [*demos, query]
            for query_index, rotated_query in enumerate(pairs5):
                rotations += 1
                rotated_demos = [
                    pair for pair_index, pair in enumerate(pairs5)
                    if pair_index != query_index
                ]
                rotation_context = {**context, "query_index": query_index}
                rotation_reasons = gen.lesson_identifiable(rotated_demos, rotated_query)
                if rotation_reasons:
                    rotation_failures.append({
                        **rotation_context,
                        "kind": "lesson_identifiable",
                        "reasons": rotation_reasons,
                    })
                for name, rival in competitors.items():
                    if any(
                        rival(pair["input"]) != pair["output"]
                        for pair in rotated_demos
                    ):
                        rotation_refuted[name] += 1
                    else:
                        rotation_failures.append({
                            **rotation_context,
                            "kind": "surviving_competitor",
                            "name": name,
                        })

            episode_hashes = [_hash_grid(grid) for grid in episode_grids]
            four_query_inputs.update(episode_hashes)
            if len(set(episode_hashes)) != len(episode_hashes):
                four_query_failures.append({**context, "kind": "duplicate_episode_input"})
            for query_index, grid in enumerate(episode_grids[gen.EXAMPLES_NEEDED:]):
                four_query_checks += 1
                query = {"input": grid, "output": official(grid)}
                query_context = {**context, "query_index": query_index}
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    four_query_failures.append({
                        **query_context, "kind": "lesson_identifiable", "reasons": reasons,
                    })
                for name, rival in competitors.items():
                    if any(rival(pair["input"]) != pair["output"] for pair in demos):
                        four_query_refuted[name] += 1
                    else:
                        four_query_failures.append({
                            **query_context, "kind": "surviving_competitor", "name": name,
                            "differs_on_query": rival(grid) != query["output"],
                        })

    return {
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "lesson_schedule_period": getattr(gen, "LESSON_SCHEDULE_PERIOD", None),
        "rule_hash": gen.RULE_HASH,
        "generator_sha256": GENERATOR_SHA256,
        "generator_source_path": str(GENERATOR_SOURCE),
        "probe_sha256": PROBE_SHA256,
        "sampler": "direct generate(seed, consecutive sample_index, difficulty); no resampling",
        "label_source": "independent Python oracle; not a Racket execution receipt",
        "seed": seed,
        "bands": list(bands),
        "starts": list(starts),
        "windows": len(bands) * len(starts),
        "unique_inputs": len(unique_inputs),
        "competitors": sorted(competitors),
        "witnesses": sorted(witnesses),
        "refuted_windows": refuted_windows,
        "witness_windows": witness_windows,
        "rotations": rotations,
        "rotation_refuted": rotation_refuted,
        "rotation_failures": rotation_failures,
        "four_query_checks": four_query_checks,
        "four_query_unique_inputs": len(four_query_inputs),
        "four_query_refuted": four_query_refuted,
        "four_query_failures": four_query_failures,
        "measured_inputs": len(measured_inputs),
        "conflicting_orbit_histogram": dict(sorted(conflict_histogram.items())),
        "profile_counts": profile_counts,
        "failures": failures,
    }


def _parse_band(token: str):
    return None if token in {"none", "default", "null"} else token


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--starts", type=int, default=32, help="audit starts 0..N-1")
    parser.add_argument("--bands", default="easy,medium,hard")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    bands = tuple(_parse_band(token.strip()) for token in args.bands.split(",") if token.strip())
    report = audit(seed=args.seed, starts=range(args.starts), bands=bands)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 1 if any(report[key] for key in (
        "failures", "rotation_failures", "four_query_failures",
    )) else 0


if __name__ == "__main__":
    raise SystemExit(main())
