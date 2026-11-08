#!/usr/bin/env python3
"""Source-bound semantic/lesson probe for ``a2d296c74658``.

The probe deliberately discovers rivals and shortcuts from the selected
``generator.py`` rather than maintaining a second name list.  It samples
sequential overlapping lesson windows because the production curriculum is a
sample-index schedule.  The report binds every count to the exact generator
bytes before and after execution.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


TASK_ID = "a2d296c74658"
ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
RUNTIME_PATH = ROOT / "shared" / "runtime"
BANDS = ("easy", "medium", "hard")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_generator():
    if str(RUNTIME_PATH) not in sys.path:
        sys.path.insert(0, str(RUNTIME_PATH))
    spec = importlib.util.spec_from_file_location(
        f"semantic_probe_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _coerce(grid: Any) -> list[list[int]]:
    return [
        [int(ch) for ch in row] if isinstance(row, str) else [int(v) for v in row]
        for row in grid
    ]


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    selected = None
    for line in CANONICAL_PATH.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            if selected is not None:
                raise RuntimeError(f"duplicate canonical row for {TASK_ID}")
            selected = row
    if selected is None:
        raise RuntimeError(f"missing canonical row for {TASK_ID}")
    tests = selected["test"] if isinstance(selected["test"], list) else [selected["test"]]
    return [
        {"input": _coerce(pair["input"]), "output": _coerce(pair["output"])}
        for pair in [*selected["train"], *tests]
    ]


def _grid_key(grid: Any) -> str:
    payload = json.dumps(_coerce(grid), separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_probe(*, lessons_per_band: int = 128) -> dict[str, Any]:
    """Run the declared semantic contract on overlapping scheduled lessons."""
    if type(lessons_per_band) is not int or lessons_per_band < 1:
        raise ValueError("lessons_per_band must be a positive integer")

    source_hash = _sha256(GENERATOR_PATH)
    generator = _load_generator()
    canonical = _canonical_pairs()

    shortcuts = dict(getattr(generator, "CANONICAL_SHORTCUTS", {}))
    rivals = dict(getattr(generator, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(generator, "SEMANTIC_WITNESSES", {}))
    if not shortcuts or not rivals or not witnesses:
        raise RuntimeError("generator semantic declarations are incomplete")

    canonical_shortcuts_fit = {
        name: all(shortcut(pair["input"]) == pair["output"] for pair in canonical)
        for name, shortcut in shortcuts.items()
    }

    report: dict[str, Any] = {
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(ROOT)),
        "generator_sha256": source_hash,
        "canonical_path": str(CANONICAL_PATH.relative_to(ROOT)),
        "canonical_pair_count": len(canonical),
        "canonical_shortcuts_fit": canonical_shortcuts_fit,
        "domain_limits": {
            "grid_h": [7, 10],
            "grid_w": [6, 9],
            "num_triplets": [2, 4],
            "difficulties": list(BANDS),
        },
        "lesson_policy": {
            "sampler": (
                "one fixed seed per difficulty; generate consecutive sample_index "
                "values 0..lessons+2; evaluate every overlapping 3-demo window "
                "with the immediately following sample as query"
            ),
            "demos_per_lesson": int(generator.EXAMPLES_NEEDED),
            "query_offset": int(generator.EXAMPLES_NEEDED),
            "cyclic_schedule_period": len(generator.SCHEDULE_PROFILES),
            "all_cyclic_starts_covered": lessons_per_band >= len(generator.SCHEDULE_PROFILES),
        },
        "bands": {},
    }

    demos_per_lesson = int(generator.EXAMPLES_NEEDED)
    if demos_per_lesson != 3:
        raise RuntimeError(
            f"probe is specified for 3-demo lessons, generator declares {demos_per_lesson}"
        )

    for band_index, difficulty in enumerate(BANDS):
        seed = 8_200_000 + band_index * 100_000
        generated = [
            generator.generate(seed, sample_index, difficulty=difficulty)
            for sample_index in range(lessons_per_band + demos_per_lesson)
        ]
        outputs = [generator.rule_mirror(grid) for grid in generated]
        keys = [_grid_key(grid) for grid in generated]

        lesson_failures: list[dict[str, Any]] = []
        killed = Counter({name: 0 for name in rivals})
        query_disagreements = Counter({name: 0 for name in rivals})
        for start in range(lessons_per_band):
            demos = [
                {"input": generated[index], "output": outputs[index]}
                for index in range(start, start + demos_per_lesson)
            ]
            query_index = start + demos_per_lesson
            query = {
                "input": generated[query_index],
                "output": outputs[query_index],
            }
            reasons = generator.lesson_identifiable(demos, query)
            if reasons:
                lesson_failures.append({"start": start, "reasons": list(reasons)})

            for name, rival in rivals.items():
                survives = all(
                    rival(pair["input"]) == pair["output"] for pair in demos
                )
                if not survives:
                    killed[name] += 1
                if rival(query["input"]) != query["output"]:
                    query_disagreements[name] += 1

        witness_hits = {
            name: sum(bool(predicate(grid)) for grid in generated)
            for name, predicate in witnesses.items()
        }
        rival_input_disagreements = {
            name: sum(rival(grid) != output for grid, output in zip(generated, outputs))
            for name, rival in rivals.items()
        }
        profile_counts = Counter(
            generator.schedule_profile(seed, index, difficulty)
            for index in range(len(generated))
        )
        strict_count = sum(generator.strict_canonical_like(grid) == [] for grid in generated)

        report["bands"][difficulty] = {
            "seed": seed,
            "sample_index_range": [0, len(generated) - 1],
            "generated_inputs": len(generated),
            "unique_inputs": len(set(keys)),
            "duplicate_input_count": len(keys) - len(set(keys)),
            "lessons": lessons_per_band,
            "overlapping_windows": True,
            "lesson_failures": lesson_failures,
            "rivals_killed_in_demos": dict(killed),
            "rival_query_disagreements": dict(query_disagreements),
            "rival_input_disagreements": rival_input_disagreements,
            "witness_hits": witness_hits,
            "strict_canonical_count": strict_count,
            "strict_canonical_fraction": strict_count / len(generated),
            "profile_counts": dict(sorted(profile_counts.items())),
        }

    report["generator_sha256_after"] = _sha256(GENERATOR_PATH)
    if report["generator_sha256_after"] != source_hash:
        raise RuntimeError("generator bytes changed while semantic probe was running")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_probe(lessons_per_band=args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    failures = sum(len(band["lesson_failures"]) for band in report["bands"].values())
    shortcuts_ok = all(report["canonical_shortcuts_fit"].values())
    source_stable = report["generator_sha256"] == report["generator_sha256_after"]
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "lessons_per_band": args.lessons_per_band,
                "lesson_failures": failures,
                "canonical_shortcuts_fit": shortcuts_ok,
                "source_stable": source_stable,
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if failures == 0 and shortcuts_ok and source_stable else 1


if __name__ == "__main__":
    raise SystemExit(main())
