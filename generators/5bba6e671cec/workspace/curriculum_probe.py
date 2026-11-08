#!/usr/bin/env python3
"""Source-bound finite-rival curriculum probe for generator 5bba6e671cec.

The probe is intentionally task-local. It reads the generator's live
``CANONICAL_SHORTCUTS`` and ``LESSON_COMPETITORS`` declarations, checks the
shortcut premise on every canonical pair, then holds out every pair of every
four-pair lesson in a deterministic band/seed/start grid. Labels come from an
independent Python transcription anchored against the canonical pairs; Racket
remains the production label authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

TASK_ID = "5bba6e671cec"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from src.core.canonical_pairs import load_task_pairs

FRAME_COLORS = frozenset((4, 7))
TWO_PI = 2.0 * math.pi


def _load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(f"curriculum_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def _normalized(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _independent_oracle(grid: list[list[int]]) -> list[list[int]]:
    """Independent centroid-angle implementation of the canonical recoloring."""
    height = len(grid)
    width = len(grid[0])
    center_r = (height - 1) / 2.0
    center_c = (width - 1) / 2.0
    colors = sorted({value for row in grid for value in row} - FRAME_COLORS)
    if len(colors) < 2:
        raise ValueError("need at least two non-frame colors")

    def angle(color: int) -> float:
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        mean_r = sum(r for r, _ in cells) / len(cells)
        mean_c = sum(c for _, c in cells) / len(cells)
        return math.atan2(mean_c - center_c, -(mean_r - center_r)) % TWO_PI

    ordered = sorted(colors, key=angle)
    mapping = {
        color: ordered[(index - 1) % len(ordered)]
        for index, color in enumerate(ordered)
    }
    return [
        [value if value in FRAME_COLORS else mapping[value] for value in row]
        for row in grid
    ]


def _same(left: Any, right: Any) -> bool:
    return _normalized(left) == _normalized(right)


def _canonical_checks(generator) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pairs = load_task_pairs(
        TASK_ID,
        REPO / "shared" / "data" / "canonical" / "puzzles.jsonl",
    )
    oracle_mismatches: list[dict[str, Any]] = []
    for pair in pairs:
        if not _same(_independent_oracle(pair["input"]), pair["output"]):
            oracle_mismatches.append(
                {"split": pair["split"], "pair_index": pair["pair_index"]}
            )

    shortcut_results: dict[str, Any] = {}
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        mismatches = []
        for pair in pairs:
            try:
                output = rival(pair["input"])
            except Exception as exc:  # retained diagnostic, not silently swallowed
                mismatches.append(
                    {
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            if not _same(output, pair["output"]):
                mismatches.append(
                    {"split": pair["split"], "pair_index": pair["pair_index"]}
                )
        shortcut_results[name] = {
            "fits_all_canonical_pairs": not mismatches,
            "canonical_pair_count": len(pairs),
            "mismatches": mismatches,
        }
    return shortcut_results, oracle_mismatches


def _empty_rival_stats() -> dict[str, int]:
    return {
        "refuted_by_demos": 0,
        "survived_and_agreed_on_query": 0,
        "ambiguous_rotations": 0,
        "errors": 0,
    }


def run_probe(
    *,
    bands: tuple[str, ...],
    seeds: int,
    starts: int,
    max_witnesses: int,
) -> dict[str, Any]:
    generator, generator_path = _load_generator()
    source_hash = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    shortcuts, canonical_oracle_mismatches = _canonical_checks(generator)

    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] = dict(
        generator.LESSON_COMPETITORS
    )
    rival_stats = {name: _empty_rival_stats() for name in rivals}
    ambiguity_witnesses: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    profile_failures: list[dict[str, Any]] = []
    lessons = 0
    rotations = 0

    for band in bands:
        for seed in range(seeds):
            for start in range(starts):
                lessons += 1
                pairs = []
                profiles = []
                try:
                    for offset in range(generator.EXAMPLES_NEEDED + 1):
                        sample_index = start + offset
                        grid = generator.generate(seed, sample_index, difficulty=band)
                        validation = generator.self_check(grid, difficulty=band)
                        if validation:
                            raise ValueError("self_check: " + "; ".join(validation))
                        expected = _independent_oracle(grid)
                        pairs.append({"input": grid, "output": expected})
                        profiles.append(generator.schedule_profile(seed, sample_index, band))
                        unique_inputs.add(_grid_hash(grid))
                except Exception as exc:
                    errors.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue

                expected_profiles = set(generator.SCHEDULE_PROFILES)
                if set(profiles) != expected_profiles:
                    profile_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "profiles": profiles,
                            "expected": sorted(expected_profiles),
                        }
                    )

                for query_index, query in enumerate(pairs):
                    rotations += 1
                    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                    for name, rival in rivals.items():
                        try:
                            fits_demos = all(
                                _same(rival(pair["input"]), pair["output"])
                                for pair in demos
                            )
                            if not fits_demos:
                                rival_stats[name]["refuted_by_demos"] += 1
                                continue
                            rival_query = rival(query["input"])
                            if _same(rival_query, query["output"]):
                                rival_stats[name]["survived_and_agreed_on_query"] += 1
                                continue
                            rival_stats[name]["ambiguous_rotations"] += 1
                            if len(ambiguity_witnesses) < max_witnesses:
                                ambiguity_witnesses.append(
                                    {
                                        "band": band,
                                        "seed": seed,
                                        "start": start,
                                        "query_index": query_index,
                                        "rival": name,
                                        "profiles": profiles,
                                        "demo_input_hashes": [
                                            _grid_hash(pair["input"]) for pair in demos
                                        ],
                                        "query_input_hash": _grid_hash(query["input"]),
                                        "query_input": query["input"],
                                        "expected_output": query["output"],
                                        "rival_output": rival_query,
                                    }
                                )
                        except Exception as exc:
                            rival_stats[name]["errors"] += 1
                            if len(errors) < max_witnesses:
                                errors.append(
                                    {
                                        "band": band,
                                        "seed": seed,
                                        "start": start,
                                        "query_index": query_index,
                                        "rival": name,
                                        "error": f"{type(exc).__name__}: {exc}",
                                    }
                                )

    ambiguous_rotations = sum(
        stats["ambiguous_rotations"] for stats in rival_stats.values()
    )
    shortcut_failures = [
        name
        for name, result in shortcuts.items()
        if not result["fits_all_canonical_pairs"]
    ]
    total_rival_errors = sum(stats["errors"] for stats in rival_stats.values())
    failed = bool(
        canonical_oracle_mismatches
        or shortcut_failures
        or errors
        or profile_failures
        or total_rival_errors
        or ambiguous_rotations
    )
    return {
        "task_id": TASK_ID,
        "status": "failure" if failed else "no_ambiguity_found",
        "source": {
            "generator_path": str(generator_path.relative_to(REPO)),
            "generator_sha256": source_hash,
            "version": getattr(generator, "VERSION", None),
            "rule_hash": getattr(generator, "RULE_HASH", None),
        },
        "configuration": {
            "bands": list(bands),
            "seeds": seeds,
            "starts": starts,
            "pairs_per_lesson": generator.EXAMPLES_NEEDED + 1,
            "query_policy": "hold out every pair once",
            "label_source": "independent centroid-angle Python oracle anchored on canonical pairs",
        },
        "summary": {
            "lessons": lessons,
            "rotations": rotations,
            "ambiguous_rotations": ambiguous_rotations,
            "unique_inputs": len(unique_inputs),
            "generation_or_scoring_errors": len(errors) + total_rival_errors,
            "profile_failures": len(profile_failures),
            "canonical_oracle_mismatches": len(canonical_oracle_mismatches),
            "canonical_shortcut_failures": len(shortcut_failures),
        },
        "canonical_shortcuts": shortcuts,
        "canonical_oracle_mismatches": canonical_oracle_mismatches,
        "rivals": rival_stats,
        "ambiguity_witnesses": ambiguity_witnesses,
        "profile_failures": profile_failures[:max_witnesses],
        "errors": errors[:max_witnesses],
        "limitations": [
            "Finite declared-rival evidence does not prove universal rule identifiability.",
            "The probe uses an independent Python oracle; production labels remain Racket-authoritative.",
        ],
    }


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bands",
        nargs="+",
        choices=("easy", "medium", "hard"),
        default=("easy", "medium", "hard"),
    )
    parser.add_argument("--seeds", type=_positive_int, default=30)
    parser.add_argument("--starts", type=_positive_int, default=8)
    parser.add_argument("--max-witnesses", type=_positive_int, default=8)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    payload = run_probe(
        bands=tuple(args.bands),
        seeds=args.seeds,
        starts=args.starts,
        max_witnesses=args.max_witnesses,
    )
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0 if payload["status"] == "no_ambiguity_found" else 1


if __name__ == "__main__":
    raise SystemExit(main())
