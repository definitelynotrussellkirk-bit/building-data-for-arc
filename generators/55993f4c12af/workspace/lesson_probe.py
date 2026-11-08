#!/usr/bin/env python3
"""Source-bound cyclic lesson probe for task 55993f4c12af.

Unlike the shared smoke gate, this probe enumerates every start position in the
four-slot curriculum cycle and evaluates the generator's live
LESSON_COMPETITORS/CANONICAL_SHORTCUTS declarations.  It is intentionally
self-contained so a later reviewer can rerun it after changing the task source.
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

TASK_ID = "55993f4c12af"
TASK_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_HOME.parents[1]
GENERATOR = TASK_HOME / "generator.py"
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs  # noqa: E402


def load_generator():
    spec = importlib.util.spec_from_file_location(f"lesson_probe_{TASK_ID}", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest_grid(grid: Any) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def run_probe(*, cycles: int, seed_base: int) -> dict[str, Any]:
    if cycles < 1:
        raise ValueError("cycles must be positive")
    gen = load_generator()
    pairs = canonical_pairs(TASK_ID, root=REPO_ROOT)

    shortcut_checks: dict[str, dict[str, Any]] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        matches = [rival(pair["input"]) == pair["output"] for pair in pairs]
        shortcut_checks[name] = {
            "canonical_pairs": len(matches),
            "matches": sum(matches),
            "fits_every_pair": all(matches),
        }

    bands: dict[str, Any] = {}
    total_ambiguous = 0
    total_windows = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        rival_survives_demos = Counter()
        rival_survives_and_fails_query = Counter()
        failures: list[dict[str, Any]] = []
        unique_inputs: set[str] = set()
        windows = 0
        for cycle in range(cycles):
            seed = seed_base + band_index * 100_000 + cycle
            for start in range(len(gen.SCHEDULE_PROFILES)):
                demos = []
                for offset in range(gen.EXAMPLES_NEEDED):
                    grid = gen.generate(seed, start + offset, difficulty=band)
                    unique_inputs.add(digest_grid(grid))
                    demos.append({"input": grid, "output": gen.rule_mirror(grid)})
                query_grid = gen.generate(
                    seed, start + gen.EXAMPLES_NEEDED, difficulty=band
                )
                unique_inputs.add(digest_grid(query_grid))
                query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
                windows += 1
                errors = gen.lesson_identifiable(demos, query)
                surviving: list[str] = []
                query_failures: list[str] = []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
                    if fits:
                        surviving.append(name)
                        rival_survives_demos[name] += 1
                        if rival(query["input"]) != query["output"]:
                            query_failures.append(name)
                            rival_survives_and_fails_query[name] += 1
                if errors or query_failures:
                    failures.append(
                        {
                            "cycle": cycle,
                            "seed": seed,
                            "start": start,
                            "errors": errors,
                            "surviving_rivals": surviving,
                            "query_failures": query_failures,
                        }
                    )
        bands[band] = {
            "cycles": cycles,
            "cyclic_starts_per_cycle": len(gen.SCHEDULE_PROFILES),
            "lesson_windows": windows,
            "unique_materialized_inputs": len(unique_inputs),
            "ambiguous_windows": len(failures),
            "rival_survives_demos": dict(sorted(rival_survives_demos.items())),
            "rival_survives_demos_and_fails_query": dict(
                sorted(rival_survives_and_fails_query.items())
            ),
            "failures": failures[:25],
        }
        total_windows += windows
        total_ambiguous += len(failures)

    source = GENERATOR.read_bytes()
    return {
        "schema": "55993f4c12af-cyclic-lesson-probe/1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source).hexdigest(),
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "assembly_policy": (
            "For each band and seed-cycle, enumerate all four cyclic starts; "
            "use EXAMPLES_NEEDED=3 consecutive generated pairs as demos and "
            "the next consecutive pair as query. Evaluate the live declared "
            "LESSON_COMPETITORS rather than a copied rival list."
        ),
        "canonical_shortcuts": shortcut_checks,
        "bands": bands,
        "totals": {
            "lesson_windows": total_windows,
            "ambiguous_windows": total_ambiguous,
            "all_canonical_shortcuts_fit": all(
                item["fits_every_pair"] for item in shortcut_checks.values()
            ),
            "pass": total_ambiguous == 0
            and all(item["fits_every_pair"] for item in shortcut_checks.values()),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=25)
    parser.add_argument("--seed-base", type=int, default=559_930)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run_probe(cycles=args.cycles, seed_base=args.seed_base)
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if result["totals"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
