"""Focused semantic and contract tests for generator d546d87fec58."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.d546d87fec58 import generator as gen


ROOT = Path(__file__).resolve().parents[1]
BASE_PATHS = (
    ROOT / "data/base/solutions/training/b8825c91__d546d87fec58.json",
    ROOT / "data/base/solutions/augmented/b8825c91__f4096078ebd4.json",
)


def _canonical_rows():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == gen.TASK_ID:
                rows.append(row)
    return rows


def _canonical_pairs():
    pairs = []
    for row in _canonical_rows():
        pairs.extend(row["train"])
        test = row.get("test") or []
        pairs.extend(test if isinstance(test, list) else [test])
    return pairs


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _single_mirror(grid, kind):
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 4:
                continue
            if kind == "rot180":
                rr, cc = height - 1 - row, width - 1 - col
            elif kind == "horizontal":
                rr, cc = row, width - 1 - col
            elif kind == "vertical":
                rr, cc = height - 1 - row, col
            else:
                raise AssertionError(kind)
            if grid[rr][cc] != 4:
                output[row][col] = grid[rr][cc]
    return output


def _key(grid):
    return tuple(tuple(row) for row in grid)


def _first_mask_cell(grid):
    return next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 4
    )


def test_rule_hash_and_all_task_local_authorities_are_canonical_exact():
    rows = _canonical_rows()
    assert len(rows) == 2
    rules = {row["program_solution"] for row in rows}
    assert len(rules) == 1
    canonical = next(iter(rules))
    # Re-pinned 2026-07-24 (was 75b3a2f9a7f9): the canonical rule now
    # precomputes (rotate-180 g)/(flip-lr g)/(flip-ud g) rather than
    # recomputing mirrored indices inline. Same semantics, verified
    # 4/4 train + 1/1 test through the Racket bridge.
    assert _normalized_hash(canonical) == gen.RULE_HASH == "5c0ceb196b2a"
    for path in BASE_PATHS:
        base = json.loads(path.read_text(encoding="utf-8"))
        target = base["racket_target"]
        assert target["raw_code"] == target["target_code"] == canonical
        assert target["needs_conversion"] is False
        assert base["primitive_metadata"]["primitive_chain"] == [
            "rows",
            "cols",
            "cellmap",
            "at",
        ]


def test_all_ten_source_row_pairs_are_accepted_exact_and_input_pure():
    pairs = _canonical_pairs()
    assert len(pairs) == 10
    first = pairs[0]["input"]
    second = pairs[-1]["input"]
    first_snapshot = copy.deepcopy(first)
    out_a1 = gen.rule_mirror(first)
    out_b = gen.rule_mirror(second)
    out_a2 = gen.rule_mirror(first)
    assert out_a1 == out_a2 == pairs[0]["output"]
    assert out_b == pairs[-1]["output"]
    assert first == first_snapshot

    for pair in pairs:
        source = pair["input"]
        snapshot = copy.deepcopy(source)
        assert gen.self_check(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == snapshot
        assert gen._is_full_symmetric(pair["output"])
        assert gen._branch_facts(source)["mask_profile"] == "rot180"


def test_canonical_candidate_operations_record_answer_equivalence_boundary():
    pairs = _canonical_pairs()
    exact = {
        kind: sum(_single_mirror(pair["input"], kind) == pair["output"] for pair in pairs)
        for kind in ("rot180", "horizontal", "vertical")
    }
    # Rotation is the only single operation that handles every official pair.
    # Horizontal/vertical shortcuts match some pairs only because full symmetry
    # makes their answers equivalent on those particular masks.
    assert exact == {"rot180": 10, "horizontal": 8, "vertical": 6}


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("profile", gen.MASK_PROFILES)
@pytest.mark.parametrize("grid_size", [10, 20])
@pytest.mark.parametrize("palette_size", [2, 8])
@pytest.mark.parametrize("block_h", [2, 4])
@pytest.mark.parametrize("block_w", [2, 4])
def test_every_declared_boundary_combination_is_exact_and_observable(
    difficulty,
    profile,
    grid_size,
    palette_size,
    block_h,
    block_w,
):
    grid = gen.generate(
        101 + grid_size + palette_size,
        700 + block_h * 10 + block_w,
        difficulty=difficulty,
        grid_size=grid_size,
        palette_size=palette_size,
        block_h=block_h,
        block_w=block_w,
        mask_profile=profile,
    )
    expected = {
        "grid_size": grid_size,
        "palette_size": palette_size,
        "block_h": block_h,
        "block_w": block_w,
        "mask_profile": profile,
    }
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == expected
    facts = gen._branch_facts(grid)
    area = block_h * block_w
    if profile == "rot180":
        assert facts["counts"] == {"rot180": area}
    elif profile == "horizontal_fallback":
        assert facts["counts"] == {"horizontal": 2 * area}
    else:
        assert facts["counts"] == {
            "rot180": area,
            "horizontal": area,
            "vertical": area,
        }


def test_default_linked_census_has_every_profile_and_full_canonical_completion():
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        profiles = Counter()
        inputs = set()
        outputs = set()
        for offset in range(200):
            seed = 20_000 + 10_000 * band_index + offset
            grid = gen.generate(seed, seed * 17 + 3, difficulty=difficulty)
            output = gen.rule_mirror(grid)
            observed = gen.observe_overrides(grid)
            assert gen.self_check(grid) == []
            assert gen._is_full_symmetric(output)
            assert all(value != 4 for row in output for value in row)
            profiles[observed["mask_profile"]] += 1
            inputs.add(_key(grid))
            outputs.add(_key(output))
        assert set(profiles) == set(gen.MASK_PROFILES)
        assert min(profiles.values()) >= 45
        assert len(inputs) >= 195
        assert len(outputs) >= 195


def test_profiles_distinguish_single_mirror_shortcuts_without_value_conflicts():
    for profile in gen.MASK_PROFILES:
        grid = gen.generate(
            913,
            27,
            difficulty="medium",
            grid_size=16,
            palette_size=8,
            block_h=3,
            block_w=4,
            mask_profile=profile,
        )
        official = gen.rule_mirror(grid)
        candidates = {
            kind: _single_mirror(grid, kind) == official
            for kind in ("rot180", "horizontal", "vertical")
        }
        assert gen._branch_facts(grid)["conflicts"] == 0
        if profile == "rot180":
            assert candidates == {
                "rot180": True,
                "horizontal": True,
                "vertical": True,
            }
        elif profile == "horizontal_fallback":
            assert candidates == {
                "rot180": False,
                "horizontal": True,
                "vertical": True,
            }
        else:
            assert candidates == {
                "rot180": False,
                "horizontal": False,
                "vertical": False,
            }


def test_structural_self_check_rejects_six_targeted_impostors():
    grid = gen.generate(
        41,
        5,
        grid_size=16,
        palette_size=5,
        block_h=3,
        block_w=3,
        mask_profile="rot180",
    )
    output = gen.rule_mirror(grid)

    no_mask = copy.deepcopy(output)

    single_color = copy.deepcopy(grid)
    for row, values in enumerate(single_color):
        for col, value in enumerate(values):
            if value != 4:
                single_color[row][col] = 1

    conflict = copy.deepcopy(grid)
    palette = sorted({value for row in output for value in row})
    for row, values in enumerate(conflict):
        for col, value in enumerate(values):
            orbit = gen._symmetry_orbit(len(conflict), row, col)
            if value != 4 and all(conflict[rr][cc] != 4 for rr, cc in orbit):
                conflict[row][col] = next(color for color in palette if color != value)
                break
        else:
            continue
        break

    notched = copy.deepcopy(grid)
    component = gen._mask_components(notched)[0]
    row1, col1, row2, col2 = gen._component_box(component)
    notch = ((row1 + row2) // 2, (col1 + col2) // 2)
    notched[notch[0]][notch[1]] = output[notch[0]][notch[1]]

    fully_erased = copy.deepcopy(grid)
    row, col = _first_mask_cell(fully_erased)
    for rr, cc in gen._symmetry_orbit(len(fully_erased), row, col):
        fully_erased[rr][cc] = 4

    foreign_color = copy.deepcopy(grid)
    for row, values in enumerate(foreign_color):
        for col, value in enumerate(values):
            if value != 4:
                foreign_color[row][col] = 0
                break
        else:
            continue
        break

    impostors = {
        "no_mask": no_mask,
        "single_color": single_color,
        "mirror_conflict": conflict,
        "notched_rectangle": notched,
        "fully_erased_orbit": fully_erased,
        "foreign_color": foreign_color,
    }
    for name, impostor in impostors.items():
        assert gen.self_check(impostor), name
        assert gen.observe_overrides(impostor) == {}, name
        # The broad executable oracle remains distinct from curriculum validity.
        assert len(gen.rule_mirror(impostor)) == len(impostor)


def test_negative_recombination_unique_replacement_feature_is_rejected_but_executes():
    grid = gen.generate(
        77,
        9,
        grid_size=16,
        palette_size=6,
        block_h=2,
        block_w=3,
        mask_profile="rot180",
    )
    row, col = _first_mask_cell(grid)
    rr, cc = len(grid) - 1 - row, len(grid) - 1 - col
    assert grid[rr][cc] != 4
    negative = copy.deepcopy(grid)
    negative[rr][cc] = 0
    assert sum(value == 0 for values in negative for value in values) == 1
    oracle_output = gen.rule_mirror(negative)
    assert oracle_output[row][col] == 0
    assert gen.self_check(negative)
    assert gen.observe_overrides(negative) == {}


def test_generation_is_deterministic_fresh_and_global_rng_isolated():
    random.seed(20260723)
    state = random.getstate()
    first = gen.generate(777, 21, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(777, 21, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(777, 21, difficulty="hard") == second


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_size": 9},
        {"grid_size": 21},
        {"palette_size": 1},
        {"palette_size": 9},
        {"block_h": 1},
        {"block_w": 1},
        {"block_w": 5},
        {"mask_profile": "unknown"},
        {"grid_size": True},
        {"palette_size": "8"},
        {"unknown_axis": 1},
    ],
)
def test_invalid_controls_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty="extreme")
