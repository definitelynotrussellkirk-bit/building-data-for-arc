"""Portable bounded compatibility/authority probe for generator 0bd65c18b34c."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "0bd65c18b34c"
BANDS = ("easy", "medium", "hard")


def squares_of(grid):
    return [
        (r, c)
        for r in range(len(grid) - 1)
        for c in range(len(grid[0]) - 1)
        if all(grid[rr][cc] == 2 for rr in (r, r + 1) for cc in (c, c + 1))
    ]


def independent_rule(grid):
    squares = squares_of(grid)
    blues = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    out = [row[:] for row in grid]
    for r, c in blues:
        out[r][c] = 0
    for r, c in blues:
        distances = []
        for sr, sc in squares:
            dr = max(0, sr - r, r - sr - 1)
            dc = max(0, sc - c, c - sc - 1)
            distances.append(max(dr, dc))
        sr, sc = squares[distances.index(min(distances))]
        if sr <= r <= sr + 1:
            target = (r, sc - 1 if c < sc else sc + 2)
        elif sc <= c <= sc + 1:
            target = (sr - 1 if r < sr else sr + 2, c)
        else:
            target = (r, c)
        out[target[0]][target[1]] = 1
    return out


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def frozen_grid(grid):
    return tuple(tuple(row) for row in grid)


def main():
    root = find_root(__file__)
    generator, source_path, source_digest = load_selected_generator(TASK_ID, root=root)

    rows = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    programs = {row["program_solution"] for row in rows}
    pairs = []
    for row in rows:
        pairs.extend(row["train"])
        test = row["test"]
        pairs.extend([test] if isinstance(test, dict) else test)
    unique_pairs = []
    seen_inputs = set()
    for pair in pairs:
        key = frozen_grid(pair["input"])
        if key not in seen_inputs:
            seen_inputs.add(key)
            unique_pairs.append(pair)

    authority = {
        "canonical_rows": len(rows),
        "canonical_pairs": len(pairs),
        "unique_canonical_inputs": len(unique_pairs),
        "unique_programs": len(programs),
        "rule_hash": generator.RULE_HASH,
        "normalized_program_hash_prefix": (
            normalized_rule_hash(next(iter(programs)))[:12] if len(programs) == 1 else None
        ),
        "canonical_labels_match_independent": all(
            independent_rule(pair["input"]) == pair["output"] for pair in unique_pairs
        ),
        "canonical_labels_match_generator": all(
            generator.rule_mirror(pair["input"]) == pair["output"]
            for pair in unique_pairs
        ),
        "canonical_inputs_pass_self_check": all(
            generator.self_check(pair["input"]) == [] for pair in unique_pairs
        ),
    }

    explicit = {}
    for band in BANDS:
        explicit[band] = {}
        for profile_index, profile in enumerate(generator.SCENE_PROFILES):
            seed = 10_000 + 100 * profile_index + len(band)
            sample_index = seed * 19 + 3
            grid = generator.generate(
                seed,
                sample_index,
                difficulty=band,
                scene_profile=profile,
            )
            explicit[band][profile] = {
                "self_check": generator.self_check(grid),
                "observed": generator.observe_overrides(grid),
                "independent_parity": generator.rule_mirror(grid) == independent_rule(grid),
                "shape": [len(grid), len(grid[0])],
            }

    distribution = {}
    for start in (0, 50_000):
        distribution[str(start)] = {}
        for band_index, band in enumerate(BANDS):
            profiles = Counter()
            shapes = set()
            generated_pairs = set()
            errors = []
            odd_witness_misses = []
            for offset in range(120):
                seed = start + band_index * 10_000 + offset
                sample_index = seed * 29 + 7
                grid = generator.generate(seed, sample_index, difficulty=band)
                output = generator.rule_mirror(grid)
                check = generator.self_check(grid)
                observed = generator.observe_overrides(grid)["scene_profile"]
                profiles[observed] += 1
                shapes.add((len(grid), len(grid[0])))
                generated_pairs.add((frozen_grid(grid), frozen_grid(output)))
                if check:
                    errors.append({"offset": offset, "errors": check})
                if output != independent_rule(grid):
                    errors.append({"offset": offset, "errors": ["independent parity"]})
                if sample_index % generator.LESSON_SCHEDULE_PERIOD == 1:
                    if observed != "large_four_balanced":
                        odd_witness_misses.append(offset)
            distribution[str(start)][band] = {
                "profiles": dict(sorted(profiles.items())),
                "shapes": [list(shape) for shape in sorted(shapes)],
                "distinct_pairs": len(generated_pairs),
                "errors": errors,
                "scheduled_tie_profile_misses": odd_witness_misses,
            }

    mutations = []
    compact = [row[:] for row in unique_pairs[2]["input"]]
    cases = {}
    cases["broken_square"] = [row[:] for row in compact]
    cases["broken_square"][3][1] = 0
    cases["extra_red"] = [row[:] for row in compact]
    cases["extra_red"][2][1] = 2
    cases["missing_dot"] = [row[:] for row in compact]
    cases["missing_dot"][8][4] = 0
    cases["invalid_color"] = [row[:] for row in compact]
    cases["invalid_color"][0][0] = 9
    cases["empty"] = []
    cases["wrong_height_9"] = [[0] * 13 for _ in range(9)]
    cases["wrong_width_12"] = [[0] * 12 for _ in range(10)]
    cases["wrong_height_11"] = [[0] * 13 for _ in range(11)]
    for name, grid in cases.items():
        mutations.append({"name": name, "rejected": bool(generator.self_check(grid))})

    rng_state = random.getstate()
    first = generator.generate(37, 43, difficulty="hard")
    rng_unchanged = random.getstate() == rng_state
    snapshot = [row[:] for row in first]
    generator.generate(91, 97, difficulty="easy")
    first_not_mutated = first == snapshot
    again = generator.generate(37, 43, difficulty="hard")
    determinism = first == again and first is not again and all(
        old_row is not new_row for old_row, new_row in zip(first, again)
    )

    checks = {
        "authority": (
            authority["canonical_rows"] == 2
            and authority["canonical_pairs"] == 8
            and authority["unique_canonical_inputs"] == 4
            and authority["unique_programs"] == 1
            and authority["rule_hash"] == authority["normalized_program_hash_prefix"]
            and authority["canonical_labels_match_independent"]
            and authority["canonical_labels_match_generator"]
            and authority["canonical_inputs_pass_self_check"]
        ),
        "explicit_profiles": all(
            record["self_check"] == []
            and record["observed"] == {"scene_profile": profile}
            and record["independent_parity"]
            for band in explicit.values()
            for profile, record in band.items()
        ),
        "distribution": all(
            set(record["profiles"]) == set(generator.SCENE_PROFILES)
            and [30, 30] in record["shapes"]
            and ([10, 13] in record["shapes"] or [13, 10] in record["shapes"])
            and record["distinct_pairs"] >= 119
            and not record["errors"]
            and not record["scheduled_tie_profile_misses"]
            for start in distribution.values()
            for record in start.values()
        ),
        "mutations_rejected": all(row["rejected"] for row in mutations),
        "deterministic_and_global_rng_isolated": (
            rng_unchanged and first_not_mutated and determinism
        ),
    }
    checks["all_passed"] = all(checks.values())
    report = {
        "schema": "0bd65c18b34c-adversarial-probe-v1",
        "task_id": TASK_ID,
        "generator_source": str(source_path),
        "generator_source_sha256": source_digest,
        "checks": checks,
        "authority": authority,
        "explicit_profiles": explicit,
        "distribution": distribution,
        "mutations": mutations,
        "determinism": {
            "global_rng_unchanged": rng_unchanged,
            "first_result_not_mutated_by_other_call": first_not_mutated,
            "fresh_equal_result": determinism,
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if checks["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
