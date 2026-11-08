#!/usr/bin/env python3
"""Source-bound lesson probe for generator d02691ffb818.

This is intentionally task-local.  It imports the selected generator bytes,
iterates the generator's *actual* CANONICAL_SHORTCUTS, LESSON_COMPETITORS,
SEMANTIC_WITNESSES and schedule declarations, and scores complete three-demo
lessons with an independent Python implementation of the written X-stencil.
It does not replace the Racket-authority battery; it supplies the larger
100-lessons-per-band curriculum measurement requested by review policy.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "d02691ffb818"
BANDS = ("easy", "medium", "hard")
LESSON_SAMPLE_STRIDE = 11
HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
DEFAULT_GENERATOR = HOME / "generator.py"
DEFAULT_CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _norm_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list):
        raise TypeError(f"expected list grid, got {type(grid).__name__}")
    if grid and all(isinstance(row, str) for row in grid):
        return [[int(ch) for ch in row.strip()] for row in grid]
    return [[int(value) for value in row] for row in grid]


def _canonical_pairs(path: Path) -> list[dict[str, list[list[int]]]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        pairs = list(row.get("train") or []) + list(row.get("test") or [])
        return [
            {"input": _norm_grid(pair["input"]), "output": _norm_grid(pair["output"])}
            for pair in pairs
        ]
    raise RuntimeError(f"canonical record {TASK_ID} not found in {path}")


def stamp_x(grid: list[list[int]]) -> list[list[int]]:
    """Independent mirror used only for this source-bound measurement."""
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 1:
                continue
            for dr, dc in ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = 7
    return out


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _seed_for(band: str, lesson_index: int) -> int:
    digest = hashlib.sha256(
        f"{TASK_ID}|review-probe-v1|{band}|{lesson_index}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big")


def _marker_count(grid: list[list[int]]) -> int:
    return sum(value == 1 for row in grid for value in row)


def _call_reasons(fn, *args) -> list[str]:
    value = fn(*copy.deepcopy(args))
    if value is True or value == []:
        return []
    if value is False:
        return ["predicate returned False"]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return [f"invalid hook return {type(value).__name__}: {value!r}"]


def run_probe(
    *,
    lessons_per_band: int = 100,
    generator_path: Path | str = DEFAULT_GENERATOR,
    canonical_path: Path | str = DEFAULT_CANONICAL,
) -> dict[str, Any]:
    if lessons_per_band <= 0:
        raise ValueError("lessons_per_band must be positive")

    generator_path = Path(generator_path).resolve()
    canonical_path = Path(canonical_path).resolve()
    gen = _load_module(generator_path)
    pairs = _canonical_pairs(canonical_path)
    source_hash = hashlib.sha256(generator_path.read_bytes()).hexdigest()

    failures: list[str] = []
    oracle_canonical_matches = sum(stamp_x(pair["input"]) == pair["output"] for pair in pairs)
    if oracle_canonical_matches != len(pairs):
        failures.append(
            f"independent oracle matched {oracle_canonical_matches}/{len(pairs)} canonical pairs"
        )

    shortcuts: dict[str, dict[str, Any]] = {}
    for name, rival in dict(getattr(gen, "CANONICAL_SHORTCUTS", {})).items():
        matched = sum(rival(copy.deepcopy(pair["input"])) == pair["output"] for pair in pairs)
        shortcuts[name] = {
            "canonical_pairs_matched": matched,
            "canonical_pairs_total": len(pairs),
        }
        if matched != len(pairs):
            failures.append(
                f"declared canonical shortcut {name!r} fits only {matched}/{len(pairs)} pairs"
            )

    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    examples_needed = int(getattr(gen, "EXAMPLES_NEEDED", 3))
    schedule_profiles = tuple(getattr(gen, "SCHEDULE_PROFILES", ()))
    schedule_fn = getattr(gen, "schedule_profile", None)
    lesson_hook = getattr(gen, "lesson_identifiable", None)
    self_check = getattr(gen, "self_check", None)
    strict_hook = getattr(gen, "strict_canonical_like", None)

    competitor_stats = {
        name: {
            "lessons_survived": 0,
            "demo_disagreements": 0,
            "query_disagreements": 0,
        }
        for name in competitors
    }
    witness_hits = Counter()
    profile_hits = Counter()
    cyclic = {
        str(residue): {"lessons": 0, "unidentifiable": 0}
        for residue in range(max(1, len(schedule_profiles)))
    }
    per_band: dict[str, Any] = {}
    unique_demo_inputs: set[str] = set()
    unique_all_inputs: set[str] = set()
    all_heights: list[int] = []
    all_widths: list[int] = []
    all_markers: list[int] = []
    selfcheck_failures = 0
    strict_hits = 0
    strict_draws = 0
    unidentifiable = 0
    lesson_hook_errors = 0

    for band in BANDS:
        band_unique_demo: set[str] = set()
        band_unique_all: set[str] = set()
        band_profiles = Counter()
        band_witnesses = Counter()
        band_unidentifiable = 0
        band_selfcheck_failures = 0
        for lesson_index in range(lessons_per_band):
            seed = _seed_for(band, lesson_index)
            start = lesson_index * LESSON_SAMPLE_STRIDE
            modulus = max(1, len(schedule_profiles))
            residue = start % modulus
            cyclic[str(residue)]["lessons"] += 1

            rows: list[dict[str, list[list[int]]]] = []
            for offset in range(examples_needed + 1):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                grid = _norm_grid(grid)
                output = stamp_x(grid)
                row = {"input": grid, "output": output}
                rows.append(row)

                key = _grid_key(grid)
                unique_all_inputs.add(key)
                band_unique_all.add(key)
                if offset < examples_needed:
                    unique_demo_inputs.add(key)
                    band_unique_demo.add(key)

                all_heights.append(len(grid))
                all_widths.append(len(grid[0]))
                all_markers.append(_marker_count(grid))

                if callable(self_check):
                    reasons = _call_reasons(self_check, grid)
                    if reasons:
                        selfcheck_failures += 1
                        band_selfcheck_failures += 1
                        if selfcheck_failures <= 5:
                            failures.append(
                                f"self_check rejected band={band} lesson={lesson_index} "
                                f"offset={offset}: {reasons}"
                            )
                if callable(strict_hook):
                    strict_draws += 1
                    if not _call_reasons(strict_hook, grid):
                        strict_hits += 1
                if callable(schedule_fn):
                    profile = schedule_fn(seed, sample_index, band)
                    profile_key = profile if isinstance(profile, str) else repr(profile)
                    profile_hits[profile_key] += 1
                    band_profiles[profile_key] += 1
                for name, witness in witnesses.items():
                    if bool(witness(copy.deepcopy(grid))):
                        witness_hits[name] += 1
                        band_witnesses[name] += 1

            demos, query = rows[:examples_needed], rows[examples_needed]
            reasons: list[str]
            if callable(lesson_hook):
                try:
                    reasons = _call_reasons(lesson_hook, demos, query)
                except Exception as exc:  # retained as counted probe evidence
                    reasons = [f"lesson hook raised {type(exc).__name__}: {exc}"]
                    lesson_hook_errors += 1
            else:
                reasons = ["lesson_identifiable is not declared"]
            if reasons:
                unidentifiable += 1
                band_unidentifiable += 1
                cyclic[str(residue)]["unidentifiable"] += 1
                if unidentifiable <= 5:
                    failures.append(
                        f"unidentifiable band={band} lesson={lesson_index} start={start}: {reasons}"
                    )

            for name, rival in competitors.items():
                demo_outputs = [rival(copy.deepcopy(row["input"])) for row in demos]
                disagreements = sum(
                    candidate != row["output"]
                    for candidate, row in zip(demo_outputs, demos)
                )
                competitor_stats[name]["demo_disagreements"] += disagreements
                if disagreements == 0:
                    competitor_stats[name]["lessons_survived"] += 1
                if rival(copy.deepcopy(query["input"])) != query["output"]:
                    competitor_stats[name]["query_disagreements"] += 1

        per_band[band] = {
            "lessons": lessons_per_band,
            "demo_draws": lessons_per_band * examples_needed,
            "all_draws_including_queries": lessons_per_band * (examples_needed + 1),
            "unique_demo_inputs": len(band_unique_demo),
            "unique_all_inputs": len(band_unique_all),
            "unidentifiable": band_unidentifiable,
            "selfcheck_failures": band_selfcheck_failures,
            "schedule_profiles": dict(sorted(band_profiles.items())),
            "witness_hits": dict(sorted(band_witnesses.items())),
        }

    for name, row in competitor_stats.items():
        if row["lessons_survived"]:
            failures.append(
                f"competitor {name!r} survived {row['lessons_survived']} complete lessons"
            )
    for name in witnesses:
        if witness_hits[name] == 0:
            failures.append(f"declared witness {name!r} never fired")
    for profile in schedule_profiles:
        key = profile if isinstance(profile, str) else repr(profile)
        if profile_hits[key] == 0:
            failures.append(f"declared schedule profile {key!r} never appeared")
    for residue, row in cyclic.items():
        if row["lessons"] == 0:
            failures.append(f"cyclic lesson start residue {residue} was not tested")
        if row["unidentifiable"]:
            failures.append(
                f"cyclic start residue {residue} had {row['unidentifiable']} unidentifiable lessons"
            )

    total_lessons = lessons_per_band * len(BANDS)
    total_demo_draws = total_lessons * examples_needed
    total_all_draws = total_lessons * (examples_needed + 1)
    report: dict[str, Any] = {
        "schema": "d02691ffb818-source-bound-lesson-probe-v1",
        "status": "pass" if not failures else "fail",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": source_hash,
        "generator_version": getattr(gen, "VERSION", None),
        "rule_hash_pin": getattr(gen, "RULE_HASH", None),
        "canonical_path": str(canonical_path),
        "independent_oracle": "center plus four in-bounds diagonal cells -> color 7 on fresh zero grid",
        "oracle_canonical_matches": oracle_canonical_matches,
        "oracle_canonical_total": len(pairs),
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "examples_needed": examples_needed,
            "query_examples_per_lesson": 1,
            "seed_formula": "uint64_be(sha256(task|review-probe-v1|band|lesson_index)[:8])",
            "sample_index_start": f"lesson_index * {LESSON_SAMPLE_STRIDE}",
            "lesson_layout": "EXAMPLES_NEEDED consecutive demos followed by one query",
            "overlapping_windows": False,
            "actual_generator_entrypoint": "generate(seed, sample_index, difficulty=band)",
        },
        "totals": {
            "lessons": total_lessons,
            "demo_draws": total_demo_draws,
            "all_draws_including_queries": total_all_draws,
            "unique_demo_inputs": len(unique_demo_inputs),
            "unique_all_inputs": len(unique_all_inputs),
            "selfcheck_failures": selfcheck_failures,
            "unidentifiable_lessons": unidentifiable,
            "lesson_hook_errors": lesson_hook_errors,
            "strict_hits": strict_hits,
            "strict_draws": strict_draws,
            "strict_rate": strict_hits / strict_draws if strict_draws else None,
        },
        "observed_domain": {
            "grid_h_min": min(all_heights),
            "grid_h_max": max(all_heights),
            "grid_w_min": min(all_widths),
            "grid_w_max": max(all_widths),
            "markers_min": min(all_markers),
            "markers_max": max(all_markers),
            "declared_axes": getattr(gen, "AXES", None),
            "teaching_boundary": (
                "2..14 markers; exact singleton, solid 2x2 block and four-cell straight line excluded; "
                "border clipping and nearby-marker overlap retained"
            ),
        },
        "per_band": per_band,
        "schedule_profiles": dict(sorted(profile_hits.items())),
        "witness_hits": dict(sorted(witness_hits.items())),
        "cyclic_starts": cyclic,
        "canonical_shortcuts": shortcuts,
        "lesson_competitors": competitor_stats,
        "failures": failures,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--generator", type=Path, default=DEFAULT_GENERATOR)
    parser.add_argument("--canonical", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(
        lessons_per_band=args.lessons_per_band,
        generator_path=args.generator,
        canonical_path=args.canonical,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
