from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", Path(__file__).resolve().parents[1] / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_1856980929fe", GENERATOR_PATH)
assert SPEC and SPEC.loader
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)


def canonical_pairs(task_id):
    here = Path(__file__).resolve()
    for parent in here.parents:
        for rel in ("shared/data/canonical/puzzles.jsonl", "data/canonical/puzzles.jsonl"):
            path = parent / rel
            if not path.is_file():
                continue
            for line in path.read_text().splitlines():
                row = json.loads(line)
                if row.get("task_id") == task_id:
                    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
                    return [*row["train"], *tests]
    raise AssertionError("canonical task row not found")


CANONICAL_SIZES = {(2, 3), (2, 4), (2, 5), (3, 2), (3, 3), (4, 2)}


def _rectangles(grid):
    return [(r, c, rh, rw) for r, c, rh, rw in gen._rectangles(grid)]


def test_metadata_rule_pin_and_canonical_pairs_are_exact():
    assert gen.TASK_ID == "1856980929fe"
    assert gen.GENERATOR_ID == gen.TASK_ID
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "77504f6c55fa"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("size", sorted(CANONICAL_SIZES))
def test_exact_overrides_are_honored_in_every_band(band, size):
    size_name = f"{size[0]}x{size[1]}"
    grid = gen.generate(
        1701,
        29,
        difficulty=band,
        grid_h=29,
        grid_w=29,
        n_seeds=3,
        rect_size=size_name,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"grid_h": 29, "grid_w": 29, "n_seeds": 3}
    rects = _rectangles(grid)
    assert len(rects) == 3
    assert {(rh, rw) for _, _, rh, rw in rects} == {size}


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=1)
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_h=24)
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_w=30)
    with pytest.raises(ValueError):
        gen.generate(1, 0, n_seeds=0)
    with pytest.raises(ValueError):
        gen.generate(1, 0, rect_size="2x2")


def test_self_check_rejects_minimal_and_nonrectangular_impostors():
    full = [[3] * 22 for _ in range(25)]
    two_by_two = [[0] * 22 for _ in range(25)]
    for r in (5, 6):
        for c in (7, 8):
            two_by_two[r][c] = 3
    irregular = [[0] * 22 for _ in range(25)]
    for r, c in ((5, 5), (5, 6), (5, 7), (6, 5), (6, 6)):
        irregular[r][c] = 3
    for name, grid in (("full", full), ("two_by_two", two_by_two), ("irregular", irregular)):
        assert gen.self_check(grid), name


def test_default_curriculum_covers_canonical_sizes_mixed_sizes_and_clipping():
    seen_sizes = set()
    seed_counts = set()
    has_mixed = False
    has_lower_half = False
    has_left_clip = False
    has_right_clip = False
    profiles = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(96):
            grid = gen.generate(9000 + band_index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(9000 + band_index, index, difficulty=band)
            rects = _rectangles(grid)
            dims = {(rh, rw) for _, _, rh, rw in rects}
            seen_sizes.update(dims)
            seed_counts.add(len(rects))
            has_mixed |= len(dims) > 1
            has_lower_half |= any(r >= len(grid) // 2 for r, _, _, _ in rects)
            has_left_clip |= any(c < rw for _, c, _, rw in rects)
            has_right_clip |= any(c + 2 * rw > len(grid[0]) for _, c, _, rw in rects)
            profiles.add(gen.schedule_profile(9000 + band_index, index, band))
    assert seen_sizes == CANONICAL_SIZES
    assert seed_counts == {1, 2, 3}
    assert has_mixed
    assert has_lower_half
    assert has_left_clip and has_right_clip
    assert profiles == set(gen.SCHEDULE_PROFILES)


def test_declared_semantic_witnesses_really_refute_their_rivals():
    witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for index in range(128):
        grid = gen.generate(712, index, difficulty="medium")
        authority = gen.rule_mirror(grid)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            if not predicate(grid):
                continue
            witness_hits[name] += 1
            for rival_name in gen.WITNESS_RIVALS[name]:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != authority
    assert all(count > 0 for count in witness_hits.values())


def test_lesson_gate_catches_the_retained_first_two_seed_shortcut():
    demos = []
    for sample_index in range(11, 16):
        grid = gen.generate(2, sample_index, difficulty="easy")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(2, 16, difficulty="easy")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}

    assert [len(_rectangles(row["input"])) for row in demos] == [1, 1, 2, 2, 2]
    assert len(_rectangles(query_grid)) == 3
    assert "first_two_seeds_only" in gen.LESSON_COMPETITORS

    rival = gen.LESSON_COMPETITORS["first_two_seeds_only"]
    assert all(rival(row["input"]) == row["output"] for row in demos)
    assert rival(query_grid) != query["output"]
    assert gen.lesson_identifiable(demos, query) == [
        "first_two_seeds_only fits every demo but changes the query answer"
    ]


def test_three_seed_witness_refutes_the_first_two_seed_rival():
    grid = gen.generate(2, 16, difficulty="easy")
    assert len(_rectangles(grid)) == 3
    assert "third_seed_expansion" in gen.SEMANTIC_WITNESSES
    assert gen.WITNESS_RIVALS["third_seed_expansion"] == ["first_two_seeds_only"]
    assert gen.SEMANTIC_WITNESSES["third_seed_expansion"](grid)
