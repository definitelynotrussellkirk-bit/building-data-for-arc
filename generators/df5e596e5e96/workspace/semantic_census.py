#!/usr/bin/env python3
"""Source-bound curriculum census for generator df5e596e5e96.

The generic semantic gate is intentionally small.  This reusable probe measures
complete 3-demo + 1-query lessons over every cyclic start of the generator's
four-slot schedule, checks the generator's *declared* rivals rather than a copied
name list, and reports unique-input/output counts plus witness coverage.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import types
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "df5e596e5e96"
_TOOL_PARENT = Path(__file__).resolve().parents[1]
if (_TOOL_PARENT / "generator.py").is_file():
    # Source-tree placement: generators/TASK/workspace/semantic_census.py
    TASK_DIR = _TOOL_PARENT
    REPO_ROOT = TASK_DIR.parents[1]
    runtime_import_root = REPO_ROOT / "shared" / "runtime"
else:
    # Portable explicit copy: runtime/workspace/semantic_census.py
    runtime_root = _TOOL_PARENT
    TASK_DIR = runtime_root / "puzzle_generators" / "per_puzzle" / TASK_ID
    REPO_ROOT = runtime_root
    runtime_import_root = runtime_root
if str(runtime_import_root) not in sys.path:
    sys.path.insert(0, str(runtime_import_root))
GENERATOR_PATH = TASK_DIR / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"semantic_census_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs():
    """Use the shared canonical reader in both source and portable layouts."""
    try:
        from scripts.canonical_profile_gate import canonical_pairs
    except ModuleNotFoundError as exc:
        if exc.name != "scripts":
            raise
        scripts_dir = REPO_ROOT / "shared" / "tools"
        if not scripts_dir.is_dir():
            return []
        package = types.ModuleType("scripts")
        package.__path__ = [str(scripts_dir)]
        sys.modules["scripts"] = package
        from scripts.canonical_profile_gate import canonical_pairs
    return canonical_pairs(TASK_ID)


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def run_census(*, lessons_per_band: int = 100, seed_base: int = 17000) -> dict[str, Any]:
    if type(lessons_per_band) is not int or lessons_per_band <= 0:
        raise ValueError("lessons_per_band must be a positive integer")
    if type(seed_base) is not int:
        raise TypeError("seed_base must be an integer")

    gen = _load_generator()
    bands = ("easy", "medium", "hard")
    report: dict[str, Any] = {
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "lesson_policy": (
            f"{gen.EXAMPLES_NEEDED} consecutive demonstrations plus one query; "
            "lesson start cycles through sample_index modulo 4"
        ),
        "lessons_per_band": lessons_per_band,
        "lessons_total": lessons_per_band * len(bands),
        "cyclic_starts": sorted({index % 4 for index in range(lessons_per_band)}),
        "bands": {},
    }

    total_ambiguous = 0
    for band_index, band in enumerate(bands):
        input_hashes: set[str] = set()
        output_hashes: set[str] = set()
        profile_counts: Counter[str] = Counter()
        witness_hits: Counter[str] = Counter()
        rival_disagreements: Counter[str] = Counter()
        ambiguous: list[dict[str, Any]] = []
        starts: Counter[int] = Counter()

        for lesson_index in range(lessons_per_band):
            start = lesson_index % len(gen.SCHEDULE_PROFILES)
            starts[start] += 1
            seed = seed_base + band_index * 100_000 + lesson_index
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                output = gen.rule_mirror(grid)
                pairs.append({"input": grid, "output": output})
                input_hashes.add(_digest(grid))
                output_hashes.add(_digest(output))
                profile_counts[gen.schedule_profile(seed, sample_index, band)] += 1
                for name, witness in gen.SEMANTIC_WITNESSES.items():
                    if witness(grid):
                        witness_hits[name] += 1
                for name, rival in gen.LESSON_COMPETITORS.items():
                    if rival(grid) != output:
                        rival_disagreements[name] += 1

            reasons = gen.lesson_identifiable(
                pairs[: gen.EXAMPLES_NEEDED], pairs[gen.EXAMPLES_NEEDED]
            )
            if reasons:
                ambiguous.append(
                    {
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "start": start,
                        "reasons": reasons,
                    }
                )

        total_ambiguous += len(ambiguous)
        report["bands"][band] = {
            "lessons": lessons_per_band,
            "examples": lessons_per_band * (gen.EXAMPLES_NEEDED + 1),
            "cyclic_start_counts": dict(sorted(starts.items())),
            "unique_inputs": len(input_hashes),
            "unique_outputs": len(output_hashes),
            "profile_counts": dict(sorted(profile_counts.items())),
            "witness_hits": dict(sorted(witness_hits.items())),
            "rival_disagreements": dict(sorted(rival_disagreements.items())),
            "ambiguous_lessons": len(ambiguous),
            "ambiguity_examples": ambiguous[:5],
        }

    report["ambiguous_lessons"] = total_ambiguous
    canonical = _canonical_pairs()
    report["canonical_pairs"] = len(canonical)
    report["canonical_shortcuts"] = {
        name: {
            "fits": sum(rival(pair["input"]) == pair["output"] for pair in canonical),
            "total": len(canonical),
            "fits_all": bool(canonical)
            and all(rival(pair["input"]) == pair["output"] for pair in canonical),
        }
        for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--seed-base", type=int, default=17000)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    report = run_census(
        lessons_per_band=args.lessons_per_band,
        seed_base=args.seed_base,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 1 if report["ambiguous_lessons"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
