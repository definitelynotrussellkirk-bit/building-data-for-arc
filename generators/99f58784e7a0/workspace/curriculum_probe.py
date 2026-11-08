"""Reproducible distribution and cyclic-lesson audit for 99f58784e7a0."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from reference_probe import (
    LAYOUT_SPANS,
    canonical_pairs,
    distinct_colors_only_rival,
    intended_output,
    load_generator,
    observed,
)

BANDS = ("easy", "medium", "hard")


def _hash_grid(grid):
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def audit(module, count: int) -> dict:
    rivals = module.LESSON_COMPETITORS
    canonical = canonical_pairs()
    report = {
        "schema": "99f58784e7a0-curriculum-probe-v1",
        "generator_version": module.VERSION,
        "rule_hash": module.RULE_HASH,
        "canonical_pairs": len(canonical),
        "canonical_oracle_matches": sum(
            intended_output(pair["input"]) == pair["output"] for pair in canonical
        ),
        "canonical_rival_fits": {
            name: sum(rival(pair["input"]) == pair["output"] for pair in canonical)
            for name, rival in rivals.items()
        },
        "bands": {},
        "override_combinations": {},
        "cyclic_query_rotations": {},
    }

    for band in BANDS:
        counters = Counter()
        support = {axis: set() for axis in ("layout_profile", "scale", "color_pattern")}
        hashes = set()
        for index in range(count):
            grid = module.generate(23000 + index, index, difficulty=band)
            counters["samples"] += 1
            counters["self_check_failures"] += bool(module.self_check(grid))
            counters["oracle_mismatches"] += module.rule_mirror(grid) != intended_output(grid)
            counters["rival_refutations"] += any(
                rival(grid) != intended_output(grid) for rival in rivals.values()
            )
            stats = observed(grid)
            for axis, value in stats.items():
                support[axis].add(value)
            hashes.add(_hash_grid(grid))
        report["bands"][band] = {
            **counters,
            "unique_inputs": len(hashes),
            "support": {name: sorted(values) for name, values in support.items()},
        }

    for band in (None, *BANDS):
        key = "none" if band is None else band
        failures = []
        tested = 0
        for layout_profile, scale in sorted(LAYOUT_SPANS):
            for color_pattern in ("distinct", "reused"):
                requested = {
                    "layout_profile": layout_profile,
                    "scale": scale,
                    "color_pattern": color_pattern,
                }
                tested += 1
                grid = module.generate(31000 + tested, tested, difficulty=band, **requested)
                if module.self_check(grid) or observed(grid) != requested:
                    failures.append(requested)
        report["override_combinations"][key] = {
            "tested": tested,
            "failures": failures,
        }

    for band in BANDS:
        failures = []
        tested = 0
        for start in range(len(module.SCHEDULE_PROFILES)):
            examples = []
            for offset in range(4):
                grid = module.generate(41000 + start, start + offset, difficulty=band)
                examples.append({"input": grid, "output": intended_output(grid)})
            for query_index in range(4):
                tested += 1
                query = examples[query_index]
                demos = examples[query_index + 1 :] + examples[:query_index]
                reasons = module.lesson_identifiable(demos, query)
                if reasons:
                    failures.append(
                        {"start": start, "query_index": query_index, "reasons": reasons}
                    )
        report["cyclic_query_rotations"][band] = {
            "tested": tested,
            "failures": failures,
        }

    # Independent rival parity check on a legal repeated-color witness.
    witness = module.generate(
        52000,
        1,
        layout_profile="grid_2x2",
        scale="canonical",
        color_pattern="reused",
    )
    report["witness"] = {
        "input_sha256": _hash_grid(witness),
        "production_rival_matches_independent": (
            module.SEMANTIC_RIVALS["distinct_colors_only"](witness)
            == distinct_colors_only_rival(witness)
        ),
        "rival_refuted": distinct_colors_only_rival(witness) != intended_output(witness),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=256)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.count)
    source = args.generator or Path(__file__).resolve().parents[1] / "generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    failures = (
        any(v["self_check_failures"] or v["oracle_mismatches"] for v in report["bands"].values())
        or any(v["failures"] for v in report["override_combinations"].values())
        or any(v["failures"] for v in report["cyclic_query_rotations"].values())
        or not report["witness"]["production_rival_matches_independent"]
        or not report["witness"]["rival_refuted"]
    )
    print(json.dumps({
        "bands": report["bands"],
        "override_combinations": report["override_combinations"],
        "cyclic_query_rotations": report["cyclic_query_rotations"],
        "witness": report["witness"],
    }, indent=2))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
