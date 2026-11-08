"""Source-bound 100-lessons-per-band shortcut audit for ad9405621c3d.

The probe uses the shipped generator, four consecutive demonstrations, one
consecutive query, and the independent oracle in ``reference_probe.py``.  It
records the exact sampler and hashes both source files.  Python labels are
supplementary; ``--racket-sample`` checks a deterministic subset against the
selected Racket authority with no fallback.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from reference_probe import (
    TASK,
    independent_output,
    load_generator,
    outer_two_ring_output,
    racket_outputs,
)

HERE = Path(__file__).resolve().parent


def _stable_seed(band, lesson_index):
    digest = hashlib.sha256(
        f"{TASK}:lesson-probe-v1:{band}:{lesson_index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def audit(module, lessons_per_band):
    report = {
        "schema": "ad9405621c3d-lesson-shortcut-audit-v1",
        "task_id": TASK,
        "generator_version": module.VERSION,
        "lessons_per_band": lessons_per_band,
        "n_demos": 4,
        "n_queries": 1,
        "sampler": (
            "For each band and lesson k: seed=sha256(task:lesson-probe-v1:band:k)[:12]; "
            "start sample_index=11*k; materialize indices start..start+4 with the same seed "
            "and difficulty. The first four are demos and the fifth is the query."
        ),
        "domain_limits": {
            "grid_h": [6, 9],
            "grid_w": [7, 9],
            "endpoint_colors": [2, 3, 4, 6, 7, 8, 9],
            "schedule_profiles": list(module.SCHEDULE_PROFILES),
            "claim_scope": "finite audit of this declared generator domain; not universal induction",
        },
        "bands": {},
    }
    racket_candidates = []
    for band in ("easy", "medium", "hard"):
        counts = Counter()
        schedule = Counter()
        dimensions = Counter()
        colors = Counter()
        unique_inputs = set()
        unique_pairs = set()
        examples = []
        for lesson_index in range(lessons_per_band):
            seed = _stable_seed(band, lesson_index)
            start = lesson_index * 11
            grids = [
                module.generate(seed, start + offset, difficulty=band)
                for offset in range(5)
            ]
            outputs = [independent_output(grid) for grid in grids]
            demo_disagreements = [
                outer_two_ring_output(grid) != output
                for grid, output in zip(grids[:4], outputs[:4])
            ]
            query_disagrees = outer_two_ring_output(grids[4]) != outputs[4]
            counts["lessons"] += 1
            counts["identifiable"] += any(demo_disagreements)
            counts["unidentifiable"] += not any(demo_disagreements)
            counts["query_rival_disagreement"] += query_disagrees
            counts["all_five_self_check_clean"] += all(
                not module.self_check(grid) for grid in grids
            )
            counts["all_five_deterministic"] += all(
                grid == module.generate(seed, start + offset, difficulty=band)
                for offset, grid in enumerate(grids)
            )
            for offset, (grid, output) in enumerate(zip(grids, outputs)):
                profile = module.schedule_profile(seed, start + offset, difficulty=band)
                schedule[profile] += 1
                observed = module.observe_overrides(grid)
                dimensions[f"{observed['grid_h']}x{observed['grid_w']}"] += 1
                colors[str(observed["endpoint_color"])] += 1
                grid_key = json.dumps(grid, separators=(",", ":"))
                pair_key = json.dumps([grid, output], separators=(",", ":"))
                unique_inputs.add(hashlib.sha256(grid_key.encode()).hexdigest())
                unique_pairs.add(hashlib.sha256(pair_key.encode()).hexdigest())
                if len(racket_candidates) < 192 and (lesson_index + offset) % 7 == 0:
                    racket_candidates.append(grid)
            if len(examples) < 3 and any(demo_disagreements):
                examples.append(
                    {
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": start,
                        "demo_disagreement_offsets": [
                            i for i, value in enumerate(demo_disagreements) if value
                        ],
                        "query_disagrees": query_disagrees,
                    }
                )
        report["bands"][band] = {
            **dict(counts),
            "unique_inputs": len(unique_inputs),
            "unique_input_output_pairs": len(unique_pairs),
            "schedule_profile_counts": dict(sorted(schedule.items())),
            "dimension_counts": dict(sorted(dimensions.items())),
            "endpoint_color_counts": dict(sorted(colors.items())),
            "counterexample_examples": examples,
        }
    return report, racket_candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--racket-sample", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.lessons_per_band < 100:
        parser.error("--lessons-per-band must be at least 100")
    if args.racket_sample < 0:
        parser.error("--racket-sample must be nonnegative")

    module = load_generator(args.generator)
    report, candidates = audit(module, args.lessons_per_band)
    generator_path = Path(
        args.generator or HERE.parent / "generator.py"
    ).resolve()
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["reference_probe_sha256"] = hashlib.sha256(
        (HERE / "reference_probe.py").read_bytes()
    ).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}

    exit_code = 0
    for band, row in report["bands"].items():
        if row["identifiable"] != args.lessons_per_band:
            exit_code = 1
        if row["all_five_self_check_clean"] != args.lessons_per_band:
            exit_code = 1
        if row["all_five_deterministic"] != args.lessons_per_band:
            exit_code = 1

    if args.racket_sample:
        selected = candidates[: args.racket_sample]
        outputs = racket_outputs(selected)
        mismatches = [
            index
            for index, (grid, output) in enumerate(zip(selected, outputs))
            if independent_output(grid) != output
        ]
        report["racket"] = {
            "status": "passed" if not mismatches else "failed",
            "checked": len(outputs),
            "mismatches": mismatches,
            "sampler": "first N grids from deterministic (lesson_index+offset)%7==0 candidate stream",
        }
        if mismatches:
            exit_code = 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "bands": {
                    band: {
                        key: row[key]
                        for key in (
                            "lessons",
                            "identifiable",
                            "unidentifiable",
                            "unique_inputs",
                            "unique_input_output_pairs",
                            "query_rival_disagreement",
                        )
                    }
                    for band, row in report["bands"].items()
                },
                "racket": report["racket"],
            },
            indent=2,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
