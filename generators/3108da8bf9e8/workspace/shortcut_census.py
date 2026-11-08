#!/usr/bin/env python3
"""Measure positional, local-sort, texture, and lesson leakage for this generator.

Run from the repository root:

    PYTHONPATH=shared/runtime python3 \
      generators/3108da8bf9e8/workspace/shortcut_census.py \
      --per-band 400 --lessons-per-band 96

Version 2 extends the original fixed-map census with the complete hypothesis
class obtained by partitioning the nine macro-positions into three unlabeled
triples and sorting only inside each triple.  There are 280 such partitions.
This catches lessons that look varied at the pixel and exact-map levels while a
fixed local decomposition still explains every demonstration.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import math
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

TASK_ID = "3108da8bf9e8"
BANDS = ("easy", "medium", "hard")
TARGET_RANK_ORDER = (6, 7, 8, 3, 4, 5, 0, 1, 2)
PRIMARY_SHORTCUTS = (
    "sort_within_macro_rows",
    "sort_within_macro_columns",
    "reverse_macro_rows",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_generator():
    repo = _repo_root()
    runtime = repo / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    path = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"shortcut_census_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rank_signature(generator, grid) -> tuple[int, ...]:
    counts = generator._block_one_counts(grid)
    rank = {count: index for index, count in enumerate(sorted(counts))}
    return tuple(rank[count] for count in counts)


def _position_map(generator, grid) -> tuple[int, ...]:
    """Destination macro-position for each input macro-position."""
    signature = _rank_signature(generator, grid)
    destination_for_rank = {
        rank: destination for destination, rank in enumerate(TARGET_RANK_ORDER)
    }
    return tuple(destination_for_rank[rank] for rank in signature)


def _texture_mask(block) -> str:
    return "".join("1" if value == 1 else "2" for row in block for value in row)


def _omitted_count(generator, grid) -> int:
    present = set(generator._block_one_counts(grid))
    missing = sorted(set(range(10)) - present)
    if len(missing) != 1:
        raise ValueError(f"expected one omitted count, got {missing}")
    return missing[0]


@lru_cache(maxsize=1)
def three_groups_of_three() -> tuple[tuple[tuple[int, ...], ...], ...]:
    """Return all 280 unlabeled partitions of nine positions into three triples."""
    positions = set(range(9))
    partitions: set[tuple[tuple[int, ...], ...]] = set()
    # Canonicalize labels by forcing position 0 into the first group and the
    # smallest remaining position into the second group.
    for first_tail in itertools.combinations(range(1, 9), 2):
        first = (0, *first_tail)
        remaining = positions - set(first)
        second_anchor = min(remaining)
        for second_tail in itertools.combinations(
            sorted(remaining - {second_anchor}), 2
        ):
            second = (second_anchor, *second_tail)
            third = tuple(sorted(remaining - set(second)))
            partitions.add(
                tuple(sorted((tuple(sorted(first)), tuple(sorted(second)), third)))
            )
    result = tuple(sorted(partitions))
    if len(result) != 280:
        raise AssertionError(f"expected 280 three-triple partitions, got {len(result)}")
    return result


def _partition_solves(
    signature: tuple[int, ...], partition: tuple[tuple[int, ...], ...]
) -> bool:
    """Whether local sorting within ``partition`` produces the official output."""
    return all(
        {signature[index] for index in group}
        == {TARGET_RANK_ORDER[index] for index in group}
        for group in partition
    )


def solving_three_group_partitions(
    signature: tuple[int, ...],
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    """Every fixed three-triple decomposition that solves this rank layout."""
    if len(signature) != 9 or set(signature) != set(range(9)):
        raise ValueError("signature must be a permutation of ranks 0..8")
    return tuple(
        partition
        for partition in three_groups_of_three()
        if _partition_solves(signature, partition)
    )


def _band_report(generator, band: str, per_band: int, seed: int) -> dict[str, Any]:
    position_maps: Counter[tuple[int, ...]] = Counter()
    displacement: Counter[int] = Counter()
    moved_rows: Counter[int] = Counter()
    moved_columns: Counter[int] = Counter()
    omissions: Counter[int] = Counter()
    shortcut_matches: Counter[str] = Counter()
    texture_masks: dict[int, set[str]] = defaultdict(set)
    local_solver_counts: Counter[int] = Counter()
    errors: list[str] = []
    valid_draws = 0

    rivals = dict(getattr(generator, "SEMANTIC_RIVALS", {}))
    for sample_index in range(per_band):
        try:
            grid = generator.generate(seed, sample_index, difficulty=band)
            self_errors = generator.self_check(grid, difficulty=band)
            if self_errors:
                errors.append(f"sample {sample_index}: self_check={self_errors}")
                continue
            valid_draws += 1
            official = generator.rule_mirror(grid)
            signature = _rank_signature(generator, grid)
            position_maps[_position_map(generator, grid)] += 1
            moved = [
                index
                for index, (actual, expected) in enumerate(
                    zip(signature, TARGET_RANK_ORDER)
                )
                if actual != expected
            ]
            displacement[len(moved)] += 1
            moved_rows[len({index // 3 for index in moved})] += 1
            moved_columns[len({index % 3 for index in moved})] += 1
            omissions[_omitted_count(generator, grid)] += 1
            local_solver_counts[len(solving_three_group_partitions(signature))] += 1
            for name, rival in rivals.items():
                try:
                    shortcut_matches[name] += rival(grid) == official
                except Exception as exc:  # retained as evidence, not hidden
                    errors.append(f"sample {sample_index}: rival {name!r} raised {exc!r}")
            for block in generator._extract_blocks(grid):
                texture_masks[generator._block_count(block)].add(_texture_mask(block))
        except Exception as exc:
            errors.append(f"sample {sample_index}: generate/analyze raised {exc!r}")

    max_reuse = max(position_maps.values(), default=0)
    draws_with_local_solver = sum(
        frequency for count, frequency in local_solver_counts.items() if count > 0
    )
    return {
        "draws": per_band,
        "valid_draws": valid_draws,
        "unique_position_maps": len(position_maps),
        "most_reused_position_map_count": max_reuse,
        "most_reused_position_map_fraction": max_reuse / per_band if per_band else 0.0,
        "displacement_histogram": {
            str(key): displacement[key] for key in sorted(displacement)
        },
        "moved_macro_rows_histogram": {
            str(key): moved_rows[key] for key in sorted(moved_rows)
        },
        "moved_macro_columns_histogram": {
            str(key): moved_columns[key] for key in sorted(moved_columns)
        },
        "omitted_count_histogram": {
            str(key): omissions[key] for key in sorted(omissions)
        },
        "shortcut_exact_matches": {
            name: shortcut_matches[name] for name in sorted(rivals)
        },
        "three_group_local_solver_count_histogram": {
            str(key): local_solver_counts[key] for key in sorted(local_solver_counts)
        },
        "draws_with_three_group_local_solver": draws_with_local_solver,
        "max_three_group_local_solvers_for_one_draw": max(
            local_solver_counts, default=0
        ),
        "texture_unique_masks": {
            str(count): len(texture_masks[count]) for count in range(10)
        },
        "texture_support_fraction": {
            str(count): (
                len(texture_masks[count]) / math.comb(9, count)
                if math.comb(9, count)
                else 0.0
            )
            for count in range(10)
        },
        "errors": errors,
    }


def _lesson_report(
    generator,
    band: str,
    lessons_per_band: int,
    seed: int,
) -> dict[str, Any]:
    fixed_all = 0
    fixed_demos = 0
    query_discriminates = 0
    local_demos = 0
    local_all = 0
    local_query_refutes = 0
    local_survivor_counts: Counter[int] = Counter()
    map_counts: Counter[tuple[int, ...]] = Counter()
    errors: list[str] = []

    band_offset = BANDS.index(band) * 10_000_019
    for lesson_index in range(lessons_per_band):
        lesson_seed = seed + band_offset + lesson_index * 104_729
        maps: list[tuple[int, ...]] = []
        local_solvers: list[set[tuple[tuple[int, ...], ...]]] = []
        for example_index in range(4):
            try:
                grid = generator.generate(
                    lesson_seed,
                    lesson_index * 4 + example_index,
                    difficulty=band,
                )
                maps.append(_position_map(generator, grid))
                local_solvers.append(
                    set(solving_three_group_partitions(_rank_signature(generator, grid)))
                )
            except Exception as exc:
                errors.append(
                    f"lesson {lesson_index} example {example_index}: {exc!r}"
                )
                break
        if len(maps) != 4:
            continue
        map_counts.update(maps)
        demos_fixed = len(set(maps[:3])) == 1
        all_fixed = len(set(maps)) == 1
        fixed_demos += demos_fixed
        fixed_all += all_fixed
        query_discriminates += demos_fixed and maps[3] != maps[0]

        demo_survivors = set.intersection(*local_solvers[:3])
        all_survivors = demo_survivors & local_solvers[3]
        local_survivor_counts[len(demo_survivors)] += 1
        local_demos += bool(demo_survivors)
        local_all += bool(all_survivors)
        local_query_refutes += bool(demo_survivors - all_survivors)

    return {
        "lessons": lessons_per_band,
        "examples_per_lesson": 4,
        "fixed_position_fits_all_demos": fixed_demos,
        "fixed_position_survives_all_examples": fixed_all,
        "fixed_position_query_discriminates": query_discriminates,
        "three_group_survives_all_demos": local_demos,
        "three_group_survives_all_examples": local_all,
        "three_group_query_refutes_at_least_one": local_query_refutes,
        "three_group_demo_survivor_count_histogram": {
            str(key): local_survivor_counts[key]
            for key in sorted(local_survivor_counts)
        },
        "unique_position_maps_seen": len(map_counts),
        "errors": errors,
    }


def build_report(
    generator,
    *,
    per_band: int = 400,
    lessons_per_band: int = 96,
    seed: int = 20261002,
) -> dict[str, Any]:
    if per_band <= 0 or lessons_per_band <= 0:
        raise ValueError("per_band and lessons_per_band must be positive")

    bands = {
        band: _band_report(
            generator,
            band,
            per_band,
            seed + BANDS.index(band) * 1_000_003,
        )
        for band in BANDS
    }
    lessons = {
        band: _lesson_report(generator, band, lessons_per_band, seed)
        for band in BANDS
    }

    failures: list[str] = []
    expected_displacements = {
        "easy": {4},
        "medium": {5, 6, 7, 8},
        "hard": {9},
    }
    minimum_maps = {
        "easy": min(180, max(2, per_band // 2)),
        "medium": min(180, max(2, per_band // 2)),
        "hard": min(180, max(2, per_band // 2)),
    }
    minimum_texture_masks = {
        count: min(math.comb(9, count), max(1, per_band // 5))
        for count in range(10)
    }
    for band, stats in bands.items():
        if stats["errors"]:
            failures.append(f"{band}: {len(stats['errors'])} analysis error(s)")
        seen_displacements = {int(key) for key in stats["displacement_histogram"]}
        if not seen_displacements or not seen_displacements <= expected_displacements[band]:
            failures.append(
                f"{band}: unexpected displacement support {sorted(seen_displacements)}"
            )
        if stats["unique_position_maps"] < minimum_maps[band]:
            failures.append(
                f"{band}: only {stats['unique_position_maps']} position maps; "
                f"need at least {minimum_maps[band]}"
            )
        for name in PRIMARY_SHORTCUTS:
            matches = stats["shortcut_exact_matches"].get(name)
            if matches is None:
                failures.append(f"{band}: missing declared rival {name!r}")
            elif matches:
                failures.append(f"{band}: rival {name!r} matched {matches} draw(s)")
        if stats["draws_with_three_group_local_solver"]:
            failures.append(
                f"{band}: {stats['draws_with_three_group_local_solver']} draw(s) "
                "admit a three-groups-of-three local sorting shortcut"
            )

        for count, minimum in minimum_texture_masks.items():
            observed = stats["texture_unique_masks"][str(count)]
            if observed < minimum:
                failures.append(
                    f"{band}: texture count {count} has only {observed} masks; "
                    f"need at least {minimum}"
                )

        lesson = lessons[band]
        if lesson["errors"]:
            failures.append(f"{band}: {len(lesson['errors'])} lesson error(s)")
        if lesson["fixed_position_survives_all_examples"]:
            failures.append(
                f"{band}: a fixed position map survived all examples in "
                f"{lesson['fixed_position_survives_all_examples']} lesson(s)"
            )
        if lesson["three_group_survives_all_demos"]:
            failures.append(
                f"{band}: a three-group local sorter survived every demo in "
                f"{lesson['three_group_survives_all_demos']} lesson(s)"
            )

    return {
        "schema": "arc-generator-shortcut-census-v2",
        "task_id": getattr(generator, "TASK_ID", TASK_ID),
        "generator_version": getattr(generator, "VERSION", None),
        "seed": seed,
        "per_band": per_band,
        "lessons_per_band": lessons_per_band,
        "three_group_partition_count": len(three_groups_of_three()),
        "primary_shortcuts": list(PRIMARY_SHORTCUTS),
        "bands": bands,
        "lessons": lessons,
        "thresholds": {
            "minimum_unique_position_maps": minimum_maps,
            "minimum_texture_masks": {
                str(count): minimum for count, minimum in minimum_texture_masks.items()
            },
            "allowed_displacements": {
                band: sorted(values) for band, values in expected_displacements.items()
            },
            "primary_shortcut_matches": 0,
            "draws_with_three_group_local_solver": 0,
            "fixed_position_survives_all_examples": 0,
            "three_group_survives_all_demos": 0,
        },
        "thresholds_passed": not failures,
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=400)
    parser.add_argument("--lessons-per-band", type=int, default=96)
    parser.add_argument("--seed", type=int, default=20261002)
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path(__file__).with_name("shortcut_census_report.json"),
    )
    args = parser.parse_args(argv)
    report = build_report(
        _load_generator(),
        per_band=args.per_band,
        lessons_per_band=args.lessons_per_band,
        seed=args.seed,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["thresholds_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
