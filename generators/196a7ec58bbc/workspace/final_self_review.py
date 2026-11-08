from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import argparse
import json

from reviewer_support import canonical_pairs, load_selected_generator

TASK = "196a7ec58bbc"
EXPECTED_SHA = "716d964e83da3769819ffa8e4c51ed38ffd7e375643fd97a4bb574db67b69af1"


def profile(grid):
    return (len(grid), len(grid[0]), len({v for row in grid for v in row}))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = Path.cwd()
    gen, source, source_sha = load_selected_generator(TASK, root=root)
    failures: list[str] = []
    if source_sha != EXPECTED_SHA:
        failures.append(f"source hash mismatch: {source_sha}")

    canonical = list(canonical_pairs(TASK, root=root, labeled_only=True))
    canonical_exact = all(
        gen.self_check(pair["input"]) == []
        and gen.rule_mirror(pair["input"]) == pair["output"]
        for pair in canonical
    )
    if not canonical_exact:
        failures.append("canonical pair acceptance/output mismatch")

    band_rows = {}
    all_hashable = set()
    for band in ("easy", "medium", "hard"):
        profiles = Counter()
        palettes = Counter()
        anchor_hits = []
        for sample_index in range(80):
            grid = gen.generate(8675309, sample_index, difficulty=band)
            errors = gen.self_check(grid, difficulty=band)
            if errors:
                failures.append(f"{band}/{sample_index}: self_check {errors}")
            if gen._rotation_orbit_size(grid) != 4:
                failures.append(f"{band}/{sample_index}: orbit != 4")
            if not gen.SEMANTIC_WITNESSES["rotation_not_reflection"](grid):
                failures.append(f"{band}/{sample_index}: reflection rival not refuted")
            p = profile(grid)
            profiles[str(p)] += 1
            palettes[p[2]] += 1
            all_hashable.add(tuple(tuple(row) for row in grid))
            if sample_index < 20 and p in gen._CANONICAL_PROFILES:
                anchor_hits.append({"sample_index": sample_index, "profile": p})
        if not anchor_hits:
            failures.append(f"{band}: no canonical profile in first 20")
        band_rows[band] = {
            "profiles_80": dict(sorted(profiles.items())),
            "palette_sizes_80": dict(sorted(palettes.items())),
            "canonical_profile_hits_first_20": anchor_hits,
        }

    override_cases = []
    for side in (2, 3):
        for palette_size in (2, 3, 4):
            for band in (None, "easy", "medium", "hard"):
                grid = gen.generate(
                    314159,
                    side * 100 + palette_size * 10 + (0 if band is None else len(band)),
                    difficulty=band,
                    grid_n=side,
                    palette_size=palette_size,
                )
                observed = gen.observe_overrides(grid)
                expected = {"grid_n": side, "palette_size": palette_size}
                okay = observed == expected and gen.self_check(grid) == []
                if not okay:
                    failures.append(
                        f"override {side}/{palette_size}/{band}: observed {observed}"
                    )
                override_cases.append(
                    {
                        "grid_n": side,
                        "palette_size": palette_size,
                        "difficulty": band,
                        "observed": observed,
                        "passed": okay,
                    }
                )

    invalid_cases = []
    for seed, sample_index in (
        (True, 0), (1.0, 0), ("1", 0), (0, True), (0, 1.0), (0, "1"), (0, -1)
    ):
        rejected = False
        try:
            gen.generate(seed, sample_index)
        except ValueError:
            rejected = True
        if not rejected:
            failures.append(f"invalid recipe accepted: {seed!r}/{sample_index!r}")
        invalid_cases.append(
            {"seed": repr(seed), "sample_index": repr(sample_index), "rejected": rejected}
        )

    report = {
        "task_id": TASK,
        "source_path": str(source),
        "source_sha256": source_sha,
        "canonical_rule_hash": gen.RULE_HASH,
        "canonical_pair_count": len(canonical),
        "canonical_pairs_exact": canonical_exact,
        "sample_count": 240,
        "unique_sample_count": len(all_hashable),
        "bands": band_rows,
        "override_case_count": len(override_cases),
        "override_cases": override_cases,
        "invalid_recipe_cases": invalid_cases,
        "finite_rival_scope": sorted(gen.SEMANTIC_RIVALS),
        "failures": failures,
        "passed": not failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
