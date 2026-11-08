#!/usr/bin/env python3
"""Fast source-bound qualification probe for task 7017b91a367d.

It checks canonical mirror parity, every advertised exact override in every
band, the declared border counterexample, and all query rotations for a range
of cyclic lesson starts. It is intentionally complementary to, not a substitute
for, the Racket-backed repository battery and lesson census.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path
from typing import Iterable

from reference_probe import (
    canonical_records,
    intended_output,
    json_sha256,
    labeled_pair,
    load_generator,
    occupancy_histogram,
)


def _source_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_report(*, generator_path: str | Path | None = None, starts: Iterable[int] = range(12)):
    path = Path(generator_path) if generator_path is not None else Path(__file__).resolve().parents[1] / "generator.py"
    gen = load_generator(path)
    canonical = canonical_records()
    errors: list[str] = []

    count_matches = sum(intended_output(pair["input"]) == pair["output"] for pair in canonical)
    shortcut = gen.CANONICAL_SHORTCUTS.get("central_3x3_only")
    shortcut_matches = (
        sum(shortcut(pair["input"]) == pair["output"] for pair in canonical)
        if callable(shortcut)
        else 0
    )
    if count_matches != len(canonical):
        errors.append("independent count mirror does not match every canonical label")
    if shortcut_matches != len(canonical):
        errors.append("declared central shortcut does not fit every canonical label")

    override_failures = []
    override_cases = 0
    unique_inputs = set()
    for band in (None, "easy", "medium", "hard"):
        for index, (profile, palette) in enumerate(
            itertools.product(gen.PROFILE_HISTOGRAMS, gen.PALETTE_KINDS)
        ):
            override_cases += 1
            grid = gen.generate(
                17017 + index,
                index,
                difficulty=band,
                profile=profile,
                palette_kind=palette,
            )
            observed = gen.observe_overrides(grid)
            expected = {"profile": profile, "palette_kind": palette}
            if gen.self_check(grid) or observed != expected:
                override_failures.append(
                    {"band": band, "profile": profile, "palette_kind": palette, "observed": observed}
                )
            if occupancy_histogram(grid) != gen.PROFILE_HISTOGRAMS[profile]:
                override_failures.append(
                    {"band": band, "profile": profile, "palette_kind": palette, "error": "histogram mismatch"}
                )
            unique_inputs.add(json_sha256(grid))
    if override_failures:
        errors.append(f"{len(override_failures)} exact override checks failed")

    starts = tuple(int(value) for value in starts)
    rotation_failures = []
    rotations = 0
    for band in (None, "easy", "medium", "hard"):
        for start in starts:
            pairs = [
                labeled_pair(gen.generate(52017 + start, start + offset, difficulty=band))
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query in enumerate(pairs):
                rotations += 1
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                reasons = gen.lesson_identifiable(deepcopy(demos), deepcopy(query))
                refuting = [
                    i
                    for i, demo in enumerate(demos)
                    if shortcut(demo["input"]) != demo["output"]
                ]
                if reasons or not refuting:
                    rotation_failures.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                            "refuting_demo_indices": refuting,
                        }
                    )
    if rotation_failures:
        errors.append(f"{len(rotation_failures)} cyclic query rotations remain ambiguous")

    witness_seed = 7017
    witness_index = 1  # top_left schedule branch
    witness_grid = gen.generate(
        witness_seed,
        witness_index,
        profile="s4_d3_t2",
        palette_kind="default",
    )
    witness_intended = intended_output(witness_grid)
    witness_rival = shortcut(witness_grid)
    witness_fires = gen.SEMANTIC_WITNESSES["border_occupancy"](witness_grid)
    if not witness_fires or witness_intended == witness_rival:
        errors.append("concrete border witness does not refute central_3x3_only")

    report = {
        "schema": "7017b91a367d-qualification-v1",
        "status": "PASS" if not errors else "FAIL",
        "generator_path": str(path),
        "generator_sha256": _source_sha(path),
        "canonical": {
            "pairs": len(canonical),
            "count_rule_matches": count_matches,
            "central_shortcut_matches": shortcut_matches,
        },
        "overrides": {
            "cases": override_cases,
            "failures": override_failures,
            "unique_inputs": len(unique_inputs),
        },
        "lessons": {
            "demonstrations": gen.EXAMPLES_NEEDED,
            "starts": list(starts),
            "query_rotations": rotations,
            "ambiguous_rotations": len(rotation_failures),
            "failures": rotation_failures,
        },
        "witness": {
            "seed": witness_seed,
            "sample_index": witness_index,
            "schedule_profile": gen.schedule_profile(witness_seed, witness_index),
            "profile": "s4_d3_t2",
            "palette_kind": "default",
            "input": witness_grid,
            "intended_output": witness_intended,
            "rival_output": witness_rival,
            "input_sha256": json_sha256(witness_grid),
            "intended_output_sha256": json_sha256(witness_intended),
            "rival_output_sha256": json_sha256(witness_rival),
        },
        "errors": errors,
        "limits": [
            "The intended-output mirror is independent Python, not the selected Racket authority.",
            "The rival set is finite; passing does not prove universal rule identifiability.",
            "The cyclic-start probe covers only the requested integer starts.",
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--starts", type=int, default=12, help="test starts 0..N-1")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(generator_path=args.generator, starts=range(args.starts))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
