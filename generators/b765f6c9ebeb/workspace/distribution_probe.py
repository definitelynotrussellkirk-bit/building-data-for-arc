#!/usr/bin/env python3
"""Deterministic stress probe for generator b765f6c9ebeb.

This is intentionally dependency-light so a future reviewer can rerun it from
packet_root with:

    PYTHONPATH=repo/shared/runtime python3 \
      repo/generators/b765f6c9ebeb/workspace/distribution_probe.py \
      --json-out checks/b765f6c9ebeb_distribution_probe.json

It exhausts the declared override cross-product for one pinned seed per
difficulty and separately checks sliding three-example lesson windows.  A
non-zero exit means at least one requested axis was not realized exactly, a
semantic texture did not supply its promised witness, generation was not
stable, or the lesson schedule failed to identify the rule.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "b765f6c9ebeb"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", GENERATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {GENERATOR_PATH}")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _palette_size(grid: list[list[int]]) -> int:
    return len({value for row in grid for value in row})


def _case_repr(case: dict[str, Any]) -> str:
    return ", ".join(f"{key}={value!r}" for key, value in sorted(case.items()))


def run_probe(*, max_examples: int = 20) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    generated = 0
    profiles: Counter[str] = Counter()
    witness_hits: Counter[str] = Counter()
    difficulties = (None, "easy", "medium", "hard")
    heights = (5, 8)
    widths = (5, 10)
    singleton_counts = (2, 3)
    object_counts = (2, 3)
    palettes = tuple(GEN.PALETTE_KINDS)
    textures = tuple(GEN.HELPFUL_TEXTURES)

    # Every declared boundary/category combination, at every difficulty.  The
    # seed is pinned by band and case index; this is a census, not fuzzing.
    cases = itertools.product(
        difficulties,
        heights,
        widths,
        singleton_counts,
        object_counts,
        palettes,
        textures,
    )
    for case_index, (difficulty, h, w, n_single, n_objects, palette, texture) in enumerate(cases):
        requested = {
            "grid_h": h,
            "grid_w": w,
            "singletons": n_single,
            "objects": n_objects,
            "palette_kind": palette,
            "texture": texture,
        }
        seed = 0xB765F6C9 + case_index * 1009
        try:
            before_rng = random.getstate()
            grid = GEN.generate(seed, case_index, difficulty=difficulty, **requested)
            after_rng = random.getstate()
            replay = GEN.generate(seed, case_index, difficulty=difficulty, **requested)
            generated += 1
        except Exception as exc:  # fail loud and retain the replay tuple
            if len(failures) < max_examples:
                failures.append({
                    "kind": "generation_error",
                    "case_index": case_index,
                    "difficulty": difficulty,
                    "seed": seed,
                    "requested": requested,
                    "error": f"{type(exc).__name__}: {exc}",
                })
            continue

        observed = {
            "grid_h": len(grid),
            "grid_w": len(grid[0]),
            **GEN.observe_overrides(grid),
        }
        expected_observed = {
            "grid_h": h,
            "grid_w": w,
            "singletons": n_single,
            "objects": n_objects,
        }
        problems: list[str] = []
        if observed != expected_observed:
            problems.append(
                f"observable mismatch: expected {expected_observed}, got {observed}"
            )
        if grid != replay:
            problems.append("same replay tuple returned different cells")
        if random.getstate() != after_rng or before_rng != after_rng:
            problems.append("generate mutated process-global random state")
        check_errors = GEN.self_check(grid, difficulty=difficulty)
        if check_errors:
            problems.append(f"self_check rejected generated grid: {check_errors}")
        if texture == "color_touch":
            name = "mixed_color_contact"
            if GEN.SEMANTIC_WITNESSES[name](grid):
                witness_hits[name] += 1
            else:
                problems.append(f"texture {texture!r} missed witness {name!r}")
        if texture == "diagonal_same_color":
            name = "same_color_diagonal_singletons"
            if GEN.SEMANTIC_WITNESSES[name](grid):
                witness_hits[name] += 1
            else:
                problems.append(f"texture {texture!r} missed witness {name!r}")
        if not GEN.SEMANTIC_WITNESSES["keep_and_erase"](grid):
            problems.append("ordinary grid missed keep_and_erase witness")
        else:
            witness_hits["keep_and_erase"] += 1

        profiles[
            f"{len(grid)}x{len(grid[0])}/palette={_palette_size(grid)}/"
            f"texture={texture}/difficulty={difficulty}"
        ] += 1
        if problems and len(failures) < max_examples:
            failures.append({
                "kind": "contract_failure",
                "case_index": case_index,
                "difficulty": difficulty,
                "seed": seed,
                "requested": requested,
                "requested_repr": _case_repr(requested),
                "problems": problems,
            })

    lesson_failures: list[dict[str, Any]] = []
    lesson_windows = 0
    for difficulty in difficulties:
        for seed in (20261002, 22554067, 0xCA62FA):
            for start in range(18):
                demos = []
                for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                    source = GEN.generate(seed, sample_index, difficulty=difficulty)
                    demos.append({"input": source, "output": GEN.rule_mirror(source)})
                query_source = GEN.generate(
                    seed, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty
                )
                query = {"input": query_source, "output": GEN.rule_mirror(query_source)}
                reasons = GEN.lesson_identifiable(demos, query)
                lesson_windows += 1
                if reasons and len(lesson_failures) < max_examples:
                    lesson_failures.append({
                        "difficulty": difficulty,
                        "seed": seed,
                        "sample_index": start,
                        "reasons": reasons,
                    })

    # Canonical-profile coverage is measured independently of the stress matrix.
    canonical_profile_draws = []
    for sample_index in range(3):
        grid = GEN.generate(20261002, sample_index, difficulty="easy")
        canonical_profile_draws.append(
            [len(grid), len(grid[0]), _palette_size(grid)]
        )

    status = "PASS" if not failures and not lesson_failures else "FAIL"
    return {
        "tool": "b765f6c9ebeb_distribution_probe",
        "status": status,
        "generator_version": GEN.VERSION,
        "rule_hash": GEN.RULE_HASH,
        "override_cases_requested": 4 * 2 * 2 * 2 * 2 * 4 * 3,
        "override_cases_generated": generated,
        "failures": failures,
        "lesson_windows_checked": lesson_windows,
        "lesson_failures": lesson_failures,
        "canonical_profile_draws": canonical_profile_draws,
        "expected_canonical_profiles": [[5, 6, 6], [5, 5, 5], [5, 7, 5]],
        "witness_hits": dict(sorted(witness_hits.items())),
        "profile_histogram": dict(sorted(profiles.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--max-examples", type=int, default=20)
    args = parser.parse_args()
    result = run_probe(max_examples=max(1, args.max_examples))
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n")
    print(rendered)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
