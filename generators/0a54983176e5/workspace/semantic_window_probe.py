#!/usr/bin/env python3
"""Check every requested lesson window against the generator's declared rivals.

This probe is intentionally declaration-driven: it reads EXAMPLES_NEEDED,
CANONICAL_SHORTCUTS, LESSON_COMPETITORS, rule_mirror, and lesson_identifiable
from the selected generator instead of copying a rival list into the tool.
It is a cheap companion to the Racket-backed lesson census, useful while
editing a schedule or adding a new semantic rival.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence

TASK_ID = "0a54983176e5"
TOOL_PATH = Path(__file__).resolve()
REPO_ROOT = TOOL_PATH.parents[3]
GENERATOR_PATH = REPO_ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"

# Permit direct execution from a packet checkout as well as execution through
# run_with_racket.py, which already provides this import path.
RUNTIME_PATH = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"semantic_window_probe_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _normalise_grid(value: Any) -> list[list[int]]:
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return copy.deepcopy(value)


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") != TASK_ID:
                continue
            pairs = list(record.get("train", [])) + list(record.get("test", []))
            return [
                {
                    "input": _normalise_grid(pair["input"]),
                    "output": _normalise_grid(pair["output"]),
                }
                for pair in pairs
            ]
    raise RuntimeError(f"canonical task {TASK_ID} missing from {CANONICAL_PATH}")


def _pair(seed: int, sample_index: int, difficulty: str | None) -> dict[str, Any]:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def run_probe(
    *,
    seed_start: int = 910_000,
    seed_count: int = 16,
    starts: Iterable[int] = range(9),
    difficulties: Sequence[str | None] = ("easy", "medium", "hard"),
) -> dict[str, Any]:
    """Return a JSON-serialisable report for all requested lesson windows."""
    if seed_count < 1:
        raise ValueError("seed_count must be >= 1")
    starts = tuple(int(value) for value in starts)
    if not starts:
        raise ValueError("at least one lesson-window start is required")
    difficulties = tuple(difficulties)
    if not difficulties:
        raise ValueError("at least one difficulty is required")

    examples_needed = int(GEN.EXAMPLES_NEEDED)
    competitors = dict(GEN.LESSON_COMPETITORS)
    shortcuts = dict(GEN.CANONICAL_SHORTCUTS)
    failures: list[dict[str, Any]] = []

    canonical = _canonical_pairs()
    shortcut_fit: dict[str, dict[str, Any]] = {}
    for name, rival in sorted(shortcuts.items()):
        fitted = [
            index
            for index, pair in enumerate(canonical)
            if rival(pair["input"]) == pair["output"]
        ]
        shortcut_fit[name] = {
            "fit_count": len(fitted),
            "pair_count": len(canonical),
            "fitted_pair_indices": fitted,
        }
        if len(fitted) != len(canonical):
            failures.append(
                {
                    "kind": "declared_shortcut_not_canonical_fitting",
                    "rival": name,
                    "fit_count": len(fitted),
                    "pair_count": len(canonical),
                }
            )

    windows_checked = 0
    rival_evaluations = 0
    witness_counts = {name: 0 for name in competitors}
    for difficulty in difficulties:
        for seed in range(seed_start, seed_start + seed_count):
            for start in starts:
                windows_checked += 1
                demos = [
                    _pair(seed, start + offset, difficulty)
                    for offset in range(examples_needed)
                ]
                query = _pair(seed, start + examples_needed, difficulty)

                lesson_errors = list(GEN.lesson_identifiable(demos, query))
                if lesson_errors:
                    failures.append(
                        {
                            "kind": "lesson_identifiable_failed",
                            "difficulty": difficulty,
                            "seed": seed,
                            "start": start,
                            "errors": lesson_errors,
                        }
                    )

                for name, rival in sorted(competitors.items()):
                    rival_evaluations += 1
                    refuted_indices = [
                        index
                        for index, pair in enumerate(demos)
                        if rival(pair["input"]) != pair["output"]
                    ]
                    if refuted_indices:
                        witness_counts[name] += 1
                    else:
                        failures.append(
                            {
                                "kind": "surviving_lesson_competitor",
                                "difficulty": difficulty,
                                "seed": seed,
                                "start": start,
                                "rival": name,
                            }
                        )

    source_hash = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    return {
        "schema": "arc-task-semantic-window-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(REPO_ROOT)),
        "generator_sha256": source_hash,
        "rule_hash": getattr(GEN, "RULE_HASH", None),
        "examples_needed": examples_needed,
        "lesson_policy": (
            "same seed; demonstrations are consecutive sample indices "
            "[start, start + EXAMPLES_NEEDED); query is the next sample"
        ),
        "seed_start": seed_start,
        "seed_count": seed_count,
        "starts": list(starts),
        "difficulties": list(difficulties),
        "canonical_pairs_checked": len(canonical),
        "canonical_shortcut_fit": shortcut_fit,
        "rivals_checked": sorted(competitors),
        "windows_checked": windows_checked,
        "rival_evaluations": rival_evaluations,
        "windows_refuting_each_rival": witness_counts,
        "failures": failures,
        "passed": not failures,
    }


def _parse_difficulties(text: str) -> tuple[str | None, ...]:
    values: list[str | None] = []
    for raw in text.split(","):
        value = raw.strip().lower()
        if value in {"none", "default", "null"}:
            values.append(None)
        elif value in {"easy", "medium", "hard"}:
            values.append(value)
        else:
            raise argparse.ArgumentTypeError(f"unknown difficulty {raw!r}")
    return tuple(values)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=910_000)
    parser.add_argument("--seed-count", type=int, default=16)
    parser.add_argument("--start-offset", type=int, default=0)
    parser.add_argument(
        "--start-count",
        type=int,
        default=9,
        help="number of consecutive cyclic starts to test",
    )
    parser.add_argument(
        "--difficulties",
        type=_parse_difficulties,
        default=("easy", "medium", "hard"),
        help="comma-separated easy,medium,hard,default",
    )
    parser.add_argument("--out", type=Path, help="optional JSON report path")
    args = parser.parse_args(argv)
    if args.start_count < 1:
        parser.error("--start-count must be >= 1")

    report = run_probe(
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        starts=range(args.start_offset, args.start_offset + args.start_count),
        difficulties=args.difficulties,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
