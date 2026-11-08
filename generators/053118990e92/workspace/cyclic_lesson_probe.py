#!/usr/bin/env python3
"""Source-bound cyclic lesson audit for generator 053118990e92.

The shared lesson census checks the production demo->query assembly policy, but
it intentionally does not rotate every materialized pair into the query slot.
This task-local probe fills that gap.  It uses the generator's live
``LESSON_COMPETITORS``, ``CANONICAL_SHORTCUTS`` and ``SEMANTIC_WITNESSES``
declarations, checks every cyclic schedule start requested, and records source
identity plus compact failure reproducers.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Sequence


TASK_ID = "053118990e92"
SCHEMA = "arcpuzzles-cyclic-lesson-probe-v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_hash(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load_generator(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        f"task_{TASK_ID}_cyclic_probe_generator", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs(path: Path, task_id: str) -> list[dict[str, Any]]:
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return [*row.get("train", []), *row.get("test", [])]
    raise KeyError(f"task {task_id} not found in {path}")


def _canonical_shortcut_check(
    generator: ModuleType,
    canonical_path: Path,
) -> dict[str, Any]:
    pairs = _canonical_pairs(canonical_path, generator.TASK_ID)
    usable: list[tuple[int, dict[str, Any]]] = []
    unusable: list[dict[str, Any]] = []
    for index, pair in enumerate(pairs):
        reasons = list(generator.self_check(pair["input"]))
        if not reasons and generator.rule_mirror(pair["input"]) != pair["output"]:
            reasons.append("rule_mirror does not match canonical output")
        if reasons:
            unusable.append({"pair_index": index, "reasons": reasons})
        else:
            usable.append((index, pair))

    shortcut_results: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    for name, shortcut in sorted(generator.CANONICAL_SHORTCUTS.items()):
        matched: list[int] = []
        mismatched: list[int] = []
        for index, pair in usable:
            if shortcut(pair["input"]) == pair["output"]:
                matched.append(index)
            else:
                mismatched.append(index)
                failures.append(
                    {
                        "shortcut": name,
                        "pair_index": index,
                        "reason": "declared shortcut does not fit canonical pair",
                    }
                )
        shortcut_results[name] = {
            "matched_pairs": matched,
            "mismatched_pairs": mismatched,
        }

    return {
        "total_pairs": len(pairs),
        "usable_pairs": len(usable),
        "unusable_pairs": unusable,
        "shortcuts": shortcut_results,
        "failures": failures,
    }


def _pair(generator: ModuleType, seed: int, sample_index: int, band: str) -> dict[str, Any]:
    grid = generator.generate(seed, sample_index, difficulty=band)
    return {
        "input": grid,
        "output": generator.rule_mirror(grid),
        "sample_index": sample_index,
        "profile": generator.schedule_profile(seed, sample_index, band),
        "input_sha256": _grid_hash(grid),
        "self_check": list(generator.self_check(grid)),
    }


def run_probe(
    generator: ModuleType,
    *,
    bands: Sequence[str] = ("easy", "medium", "hard"),
    seed_start: int = 0,
    seeds: int = 16,
    starts: Iterable[int] | None = None,
    canonical_path: Path,
) -> dict[str, Any]:
    """Audit every query rotation in each selected five-pair schedule window."""
    if seeds <= 0:
        raise ValueError("seeds must be positive")
    bands = tuple(bands)
    if not bands:
        raise ValueError("at least one difficulty band is required")
    bad_bands = [band for band in bands if band not in ("easy", "medium", "hard")]
    if bad_bands:
        raise ValueError(f"unsupported bands: {bad_bands}")

    period = len(generator.SCHEDULE_PROFILES)
    starts_tuple = tuple(range(period) if starts is None else starts)
    if not starts_tuple:
        raise ValueError("at least one schedule start is required")
    window_size = int(generator.EXAMPLES_NEEDED) + 1
    if window_size < 2:
        raise ValueError("EXAMPLES_NEEDED must leave at least one demo and one query")

    competitors = dict(generator.LESSON_COMPETITORS)
    shortcuts = dict(generator.CANONICAL_SHORTCUTS)
    witnesses = dict(generator.SEMANTIC_WITNESSES)
    source_path = Path(generator.__file__).resolve()

    witness_demo_coverage = {name: 0 for name in sorted(witnesses)}
    rival_refutations = {name: 0 for name in sorted(competitors)}
    shortcut_refutations = {name: 0 for name in sorted(shortcuts)}
    failures: list[dict[str, Any]] = []
    invalid_pairs: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    windows = 0
    rotations = 0

    for band in bands:
        for seed in range(seed_start, seed_start + seeds):
            for start in starts_tuple:
                windows += 1
                pairs = [
                    _pair(generator, seed, start + offset, band)
                    for offset in range(window_size)
                ]
                for offset, pair in enumerate(pairs):
                    unique_inputs.add(pair["input_sha256"])
                    if pair["self_check"]:
                        invalid_pairs.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "window_offset": offset,
                                "sample_index": pair["sample_index"],
                                "profile": pair["profile"],
                                "input_sha256": pair["input_sha256"],
                                "reasons": pair["self_check"],
                            }
                        )

                for query_offset, query in enumerate(pairs):
                    rotations += 1
                    demos = [
                        {"input": pair["input"], "output": pair["output"]}
                        for offset, pair in enumerate(pairs)
                        if offset != query_offset
                    ]
                    query_public = {
                        "input": query["input"],
                        "output": query["output"],
                    }
                    reasons = list(generator.lesson_identifiable(demos, query_public))
                    missing_witnesses = [
                        name
                        for name, witness in sorted(witnesses.items())
                        if not any(witness(pair["input"]) for pair in demos)
                    ]
                    surviving_rivals = [
                        name
                        for name, rival in sorted(competitors.items())
                        if all(rival(pair["input"]) == pair["output"] for pair in demos)
                    ]
                    surviving_shortcuts = [
                        name
                        for name, shortcut in sorted(shortcuts.items())
                        if all(
                            shortcut(pair["input"]) == pair["output"]
                            for pair in demos
                        )
                    ]

                    for name in witnesses:
                        if name not in missing_witnesses:
                            witness_demo_coverage[name] += 1
                    for name in competitors:
                        if name not in surviving_rivals:
                            rival_refutations[name] += 1
                    for name in shortcuts:
                        if name not in surviving_shortcuts:
                            shortcut_refutations[name] += 1

                    if reasons or missing_witnesses or surviving_rivals:
                        failures.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_offset": query_offset,
                                "query_sample_index": query["sample_index"],
                                "query_profile": query["profile"],
                                "input_sha256s": [
                                    pair["input_sha256"] for pair in pairs
                                ],
                                "reasons": reasons,
                                "missing_witnesses": missing_witnesses,
                                "surviving_rivals": surviving_rivals,
                                "surviving_canonical_shortcuts": surviving_shortcuts,
                            }
                        )

    canonical = _canonical_shortcut_check(generator, canonical_path)
    passed = not failures and not invalid_pairs and not canonical["failures"]
    return {
        "schema": SCHEMA,
        "task_id": generator.TASK_ID,
        "generator_version": getattr(generator, "VERSION", None),
        "generator_sha256": _sha256(source_path),
        "rule_hash": getattr(generator, "RULE_HASH", None),
        "sampling_policy": {
            "bands": list(bands),
            "seed_start": seed_start,
            "seed_count": seeds,
            "schedule_starts": list(starts_tuple),
            "window_size": window_size,
            "demos_per_rotation": window_size - 1,
            "query_policy": "each pair in the window is rotated into query once",
        },
        "declarations": {
            "lesson_competitors": sorted(competitors),
            "canonical_shortcuts": sorted(shortcuts),
            "semantic_witnesses": sorted(witnesses),
        },
        "totals": {
            "windows": windows,
            "rotations": rotations,
            "identifiable_rotations": rotations - len(failures),
            "ambiguous_rotations": len(failures),
            "materialized_pair_occurrences": windows * window_size,
            "unique_inputs": len(unique_inputs),
            "invalid_pair_occurrences": len(invalid_pairs),
        },
        "witness_demo_coverage": witness_demo_coverage,
        "rival_refutations": rival_refutations,
        "canonical_shortcut_refutations": shortcut_refutations,
        "canonical_shortcut_check": canonical,
        "invalid_pairs": invalid_pairs,
        "failures": failures,
        "passed": passed,
        "limitations": [
            "Finite checks cover only declared rivals and witnesses, not every plausible induction rule.",
            "Repeated windows overlap; materialized pair occurrences are not unique-input counts.",
            "The Python rule_mirror is an audit mirror; selected Racket authority is checked separately by the battery.",
        ],
    }


def _parse_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _parse_starts(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(item) for item in _parse_csv(value))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("starts must be comma-separated integers") from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--bands", default="easy,medium,hard")
    parser.add_argument(
        "--starts",
        type=_parse_starts,
        help="comma-separated schedule starts; default covers every schedule residue",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[3]
    generator_path = Path(__file__).resolve().parents[1] / "generator.py"
    canonical_path = repo_root / "shared/data/canonical/puzzles.jsonl"
    generator = _load_generator(generator_path)
    report = run_probe(
        generator,
        bands=_parse_csv(args.bands),
        seed_start=args.seed_start,
        seeds=args.seeds,
        starts=args.starts,
        canonical_path=canonical_path,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(rendered, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
        print(
            f"{TASK_ID}: {report['totals']['identifiable_rotations']}/"
            f"{report['totals']['rotations']} cyclic rotations identifiable; "
            f"unique_inputs={report['totals']['unique_inputs']}; out={args.out}"
        )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
