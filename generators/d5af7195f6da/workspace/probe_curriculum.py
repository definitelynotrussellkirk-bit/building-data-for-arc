#!/usr/bin/env python3
"""Fast source-bound curriculum probe for d5af7195f6da.

This is an authoring aid, not a replacement for the Racket-backed
``arcpuzzles lesson-census`` command.  It replays the production sampler's
important local behavior: consecutive generation, exact-input de-duplication,
profile balance, and every possible held-out query rotation.  Rivals are read
from the live generator declarations rather than copied into this tool.
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

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"


def _install_runtime_path() -> None:
    """Locate the source-tree runtime when the caller did not set PYTHONPATH."""
    for parent in (TASK_DIR, *TASK_DIR.parents):
        candidate = parent / "shared" / "runtime"
        if (candidate / "puzzle_generators").is_dir():
            sys.path.insert(0, str(candidate))
            return


_install_runtime_path()


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "curriculum_probe_d5af7195f6da", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _lesson_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"lesson-census:v1:{gen.TASK_ID}:{band}:{index}".encode()
    ).digest()
    return int.from_bytes(digest[:4], "big")


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _live_rivals() -> list[str]:
    names: list[str] = []
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        mapping = getattr(gen, namespace, {})
        names.extend(f"{namespace}:{name}" for name in sorted(mapping))
    return names


def run_probe(*, per_band: int = 12, max_attempts_per_lesson: int = 64) -> dict[str, Any]:
    """Return a JSON-serializable report; no private labels or Racket are used."""
    if type(per_band) is not int or per_band < 1:
        raise ValueError("per_band must be a positive integer")
    if type(max_attempts_per_lesson) is not int or max_attempts_per_lesson < 1:
        raise ValueError("max_attempts_per_lesson must be a positive integer")

    target_pairs = int(gen.EXAMPLES_NEEDED) + 1
    profiles = tuple(gen.SCHEDULE_PROFILES)
    expected_per_profile = target_pairs // len(profiles)
    bands = ("easy", "medium", "hard")
    failures: list[dict[str, Any]] = []
    per_band_report: dict[str, dict[str, int]] = {}
    totals = Counter()

    for band in bands:
        counts = Counter()
        for lesson_index in range(per_band):
            seed = _lesson_seed(band, lesson_index)
            sample_index = lesson_index
            accepted: list[dict[str, Any]] = []
            seen_inputs: set[str] = set()
            attempts = 0

            while len(accepted) < target_pairs and attempts < max_attempts_per_lesson:
                current_index = sample_index
                sample_index += 1
                attempts += 1
                try:
                    grid = gen.generate(seed, current_index, difficulty=band)
                    validation = gen.self_check(grid, difficulty=band)
                    if validation:
                        raise ValueError(f"self_check rejected generated grid: {validation}")
                    input_hash = _grid_hash(grid)
                    if input_hash in seen_inputs:
                        counts["duplicate_inputs"] += 1
                        continue
                    seen_inputs.add(input_hash)
                    observed = gen.observe_overrides(grid)
                    accepted.append(
                        {
                            "sample_index": current_index,
                            "profile": observed["profile"],
                            "pair": _pair(grid),
                        }
                    )
                except Exception as exc:  # report the exact lesson rather than aborting all bands
                    counts["generation_errors"] += 1
                    failures.append(
                        {
                            "kind": "generation_error",
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": current_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )

            counts["lessons"] += 1
            counts["pairs"] += len(accepted)
            if len(accepted) != target_pairs:
                counts["generation_errors"] += 1
                failures.append(
                    {
                        "kind": "incomplete_lesson",
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "accepted": len(accepted),
                        "required": target_pairs,
                        "attempts": attempts,
                    }
                )
                continue

            profile_counts = Counter(item["profile"] for item in accepted)
            expected = {profile: expected_per_profile for profile in profiles}
            if dict(profile_counts) != expected:
                counts["profile_balance_failures"] += 1
                failures.append(
                    {
                        "kind": "profile_balance",
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_indices": [item["sample_index"] for item in accepted],
                        "observed": dict(profile_counts),
                        "expected": expected,
                    }
                )

            for query_index, held_out in enumerate(accepted):
                demos = [
                    item["pair"]
                    for position, item in enumerate(accepted)
                    if position != query_index
                ]
                problems = gen.lesson_identifiable(demos, held_out["pair"])
                if problems:
                    counts["ambiguous_rotations"] += 1
                    failures.append(
                        {
                            "kind": "ambiguous_rotation",
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "query_index": query_index,
                            "query_profile": held_out["profile"],
                            "sample_indices": [item["sample_index"] for item in accepted],
                            "problems": list(problems),
                        }
                    )

        per_band_report[band] = {
            "lessons": counts["lessons"],
            "pairs": counts["pairs"],
            "duplicate_inputs": counts["duplicate_inputs"],
            "profile_balance_failures": counts["profile_balance_failures"],
            "ambiguous_rotations": counts["ambiguous_rotations"],
            "generation_errors": counts["generation_errors"],
        }
        totals.update(counts)

    summary = {
        "lessons": totals["lessons"],
        "pairs": totals["pairs"],
        "duplicate_inputs": totals["duplicate_inputs"],
        "profile_balance_failures": totals["profile_balance_failures"],
        "ambiguous_rotations": totals["ambiguous_rotations"],
        "generation_errors": totals["generation_errors"],
    }
    return {
        "schema": "d5af7195f6da-curriculum-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "configuration": {
            "bands": list(bands),
            "per_band": per_band,
            "demonstrations": gen.EXAMPLES_NEEDED,
            "queries": 1,
            "pairs_per_lesson": target_pairs,
            "start_recipe": "lesson_index",
            "seed_recipe": "sha256('lesson-census:v1:TASK:BAND:INDEX')[:4] as uint32",
            "de_duplication": "reject exact normalized input hashes; continue consecutive indices",
            "rotation_recipe": "hold out every accepted pair once; preserve remaining order",
            "max_attempts_per_lesson": max_attempts_per_lesson,
        },
        "declared_profiles": list(profiles),
        "live_rivals": _live_rivals(),
        "per_band": per_band_report,
        "summary": summary,
        "errors": failures,
        "limitations": [
            "Uses the generator's Python rule mirror; final authority checks require Racket.",
            "Tests declared rivals only; this is not a proof of universal identifiability.",
            "Models exact-input de-duplication and consecutive retries, not every production assembly policy.",
        ],
    }


def write_report(report: dict[str, Any], output_path: Path | str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=12)
    parser.add_argument("--max-attempts-per-lesson", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run_probe(
        per_band=args.per_band,
        max_attempts_per_lesson=args.max_attempts_per_lesson,
    )
    if args.out:
        write_report(report, args.out)
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    bad = any(
        report["summary"][key]
        for key in (
            "profile_balance_failures",
            "ambiguous_rotations",
            "generation_errors",
        )
    )
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
