#!/usr/bin/env python3
"""Source-bound lesson audit for generator ``b3bfd59c2c43``.

This task-local tool materializes consecutive demonstration windows, labels
those grids with an independent occupancy-boundary oracle, and measures every
declared lesson competitor.  It is intentionally runnable against an arbitrary
candidate source via ``--source``/``GENERATOR_UNDER_TEST`` so a future reviewer
can bind evidence to an exact generator hash rather than an installed module.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
BANDS = ("easy", "medium", "hard")
HOME = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))


def sha256_file(path: Path | str) -> str:
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_generator(source: Path):
    source = source.resolve()
    name = f"lesson_probe_generator_{sha256_file(source)[:16]}"
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator source {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if type(grid[r][c]) is int and grid[r][c] not in (0, 9)
    }
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)
        result.append(frozenset(component))
    return tuple(sorted(result, key=lambda comp: min(comp)))


def independent_oracle(grid):
    """Mirror the selected Racket occupancy-component boundary semantics."""
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for component in _components(grid):
        for r, c in component:
            if any(
                not (0 <= r + dr < h and 0 <= c + dc < w)
                or (r + dr, c + dc) not in component
                for dr, dc in CARDINAL
            ):
                out[r][c] = 8
    return out


def _seed(task_id: str, band: str, lesson: int) -> int:
    raw = f"{task_id}|{band}|lesson-probe|{lesson}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _grid_digest(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def audit(
    source: Path | str = DEFAULT_SOURCE,
    *,
    lessons_per_band: int = 100,
    bands: tuple[str, ...] = BANDS,
) -> dict[str, Any]:
    source = Path(source).resolve()
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")
    gen = _load_generator(source)
    n_demos = int(getattr(gen, "EXAMPLES_NEEDED", 3))
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))

    report: dict[str, Any] = {
        "schema": "b3bfd59c2c43-lesson-probe-v1",
        "generator_id": getattr(gen, "GENERATOR_ID", None),
        "version": getattr(gen, "VERSION", None),
        "source": str(source),
        "generator_sha256": sha256_file(source),
        "lessons_per_band": lessons_per_band,
        "bands": list(bands),
        "examples_needed": n_demos,
        "lessons": 0,
        "generated_grids": 0,
        "invalid_grids": 0,
        "oracle_mismatches": 0,
        "ambiguous_lessons": 0,
        "declared_identifiability_failures": 0,
        "competitor_survivals": {name: 0 for name in competitors},
        "competitor_query_disagreements": {name: 0 for name in competitors},
        "schedule_profiles": {band: {} for band in bands},
        "witness_hits": {
            band: {name: 0 for name in witnesses} for band in bands
        },
        "unique_inputs": 0,
        "corpus_sha256": None,
        "examples": [],
    }

    input_digests: set[str] = set()
    corpus_rows = []
    for band in bands:
        profile_counts: Counter[str] = Counter()
        for lesson in range(lessons_per_band):
            report["lessons"] += 1
            seed = _seed(getattr(gen, "TASK_ID", "b3bfd59c2c43"), band, lesson)
            start = lesson * 11
            pairs = []
            for offset in range(n_demos + 1):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                report["generated_grids"] += 1
                input_digest = _grid_digest(grid)
                input_digests.add(input_digest)
                output = independent_oracle(grid)
                corpus_rows.append(
                    {
                        "band": band,
                        "lesson": lesson,
                        "sample_index": sample_index,
                        "input_sha256": input_digest,
                        "output_sha256": _grid_digest(output),
                    }
                )

                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    report["invalid_grids"] += 1
                    if len(report["examples"]) < 12:
                        report["examples"].append(
                            f"{band} lesson {lesson} sample {sample_index}: "
                            f"self_check={errors}"
                        )
                mirror = getattr(gen, "rule_mirror", None)
                if callable(mirror) and mirror(grid) != output:
                    report["oracle_mismatches"] += 1
                    if len(report["examples"]) < 12:
                        report["examples"].append(
                            f"{band} lesson {lesson} sample {sample_index}: "
                            "rule_mirror disagrees with independent oracle"
                        )

                schedule = getattr(gen, "schedule_profile", None)
                if callable(schedule):
                    profile_counts[str(schedule(seed, sample_index, difficulty=band))] += 1
                for name, witness in witnesses.items():
                    if witness(grid):
                        report["witness_hits"][band][name] += 1
                pairs.append({"input": grid, "output": output})

            demos, query = pairs[:-1], pairs[-1]
            for name, rival in competitors.items():
                survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
                if not survives:
                    continue
                report["competitor_survivals"][name] += 1
                if rival(query["input"]) != query["output"]:
                    report["competitor_query_disagreements"][name] += 1
                    report["ambiguous_lessons"] += 1
                    if len(report["examples"]) < 12:
                        report["examples"].append(
                            f"{band} lesson {lesson}: competitor {name} survives "
                            "all demos and disagrees on the query"
                        )

            identifiability = getattr(gen, "lesson_identifiable", None)
            if callable(identifiability):
                reasons = identifiability(demos, query)
                if reasons:
                    report["declared_identifiability_failures"] += 1
                    if len(report["examples"]) < 12:
                        report["examples"].append(
                            f"{band} lesson {lesson}: lesson_identifiable={reasons}"
                        )
        report["schedule_profiles"][band] = dict(sorted(profile_counts.items()))

    report["unique_inputs"] = len(input_digests)
    report["corpus_sha256"] = hashlib.sha256(
        json.dumps(corpus_rows, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return report


def _failed(report: dict[str, Any]) -> bool:
    return any(
        (
            report["invalid_grids"],
            report["oracle_mismatches"],
            report["ambiguous_lessons"],
            report["declared_identifiability_failures"],
            sum(report["competitor_survivals"].values()),
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    report = audit(args.source, lessons_per_band=args.lessons_per_band)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    return 1 if _failed(report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
