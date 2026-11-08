"""Source-bound regression tests for d62a0e470ae8."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    authority_output,
    canonical_pairs,
    components,
    load_generator,
    observed,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_metadata_is_bound_to_selected_authority():
    assert gen.GENERATOR_ID == gen.TASK_ID == "d62a0e470ae8"
    assert gen.RULE_HASH == "43fde3a5fa41"
    assert set(gen.AXES) == {"grid_profile", "key", "main_size", "n_distractors"}


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert authority_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_honored_in_every_band(band):
    requested = {
        "grid_profile": "7x9",
        "key": 4,
        "main_size": 9,
        "n_distractors": 3,
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("typo", 1),
        ("grid_profile", "6x6"),
        ("grid_profile", 79),
        ("key", 0),
        ("key", 5),
        ("key", 2.0),
        ("key", True),
        ("main_size", 4),
        ("main_size", 10),
        ("n_distractors", -1),
        ("n_distractors", 4),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(name, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{name: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_covers_rule_defining_controls_in_each_band(band):
    rows = [observed(gen.generate(2200, i, difficulty=band)) for i in range(24)]
    assert {row["key"] for row in rows} == {1, 2, 3, 4}
    assert {row["n_distractors"] for row in rows} == {0, 1, 2, 3}
    assert {row["main_size"] for row in rows} == {5, 6, 7, 8, 9}
    assert {"7x9", "8x10", "9x9"} <= {row["grid_profile"] for row in rows}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_inputs_are_deterministic_strict_and_have_a_unique_largest_object(band):
    for index in range(80):
        grid = gen.generate(7000 + index, index * 7 + 1, difficulty=band)
        assert grid == gen.generate(7000 + index, index * 7 + 1, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        objs = components(grid)
        sizes = sorted((obj["size"] for obj in objs), reverse=True)
        assert len(sizes) == observed(grid)["n_distractors"] + 1
        assert sizes[0] == observed(grid)["main_size"]
        assert len(sizes) == 1 or sizes[0] > sizes[1]
        colors = {obj["color"] for obj in objs}
        assert len(colors) == 1
        assert grid[0][0] not in colors


@pytest.mark.parametrize("index", range(48))
def test_rule_mirror_matches_independent_oracle_and_does_not_mutate(index):
    grid = gen.generate(8100 + index, index)
    original = deepcopy(grid)
    assert gen.rule_mirror(grid) == authority_output(grid)
    assert grid == original


def test_witness_claims_are_actual_counterexamples_to_named_rivals():
    fired = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for index in range(96):
        grid = gen.generate(9100 + index, index)
        intended = authority_output(grid)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                fired[name] += 1
                named = gen.WITNESS_RIVALS.get(name, [])
                assert named, name
                assert any(gen.SEMANTIC_RIVALS[rival](grid) != intended for rival in named)
    assert all(count > 0 for count in fired.values())


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_four_demo_lesson_refutes_query_changing_competitors(band):
    for start in range(20):
        seed = 12000 + start
        pairs = []
        for offset in range(5):
            grid = gen.generate(seed, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": authority_output(grid)})
        demos, query = pairs[:4], pairs[4]
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
            assert not (fits and changes_query), name


@pytest.mark.parametrize("mutation", ["remove_key", "tie_largest", "solid_main", "extra_color"])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(33, 7, grid_profile="8x10", key=2, main_size=7, n_distractors=2)
    objs = sorted(components(grid), key=lambda obj: obj["size"], reverse=True)
    if mutation == "remove_key":
        grid[0][0] = 0
    elif mutation == "tie_largest":
        # Grow the first distractor to tie the main while staying disconnected.
        target = set(objs[1]["cells"])
        color = objs[1]["color"]
        forbidden = {cell for obj in objs if obj is not objs[1] for cell in obj["cells"]}
        h, w = len(grid), len(grid[0])
        while len(target) < objs[0]["size"]:
            grown = False
            for r, c in sorted(target):
                for dr, dc in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                    p = (r + dr, c + dc)
                    if not (1 <= p[0] < h and 0 <= p[1] < w) or p in target or p in forbidden:
                        continue
                    if any(abs(p[0] - rr) + abs(p[1] - cc) == 1 for rr, cc in forbidden):
                        continue
                    grid[p[0]][p[1]] = color
                    target.add(p)
                    grown = True
                    break
                if grown:
                    break
            if not grown:
                pytest.skip("fixture has no safe tie-growth path")
    elif mutation == "solid_main":
        main = objs[0]
        r1 = min(r for r, _ in main["cells"])
        r2 = max(r for r, _ in main["cells"])
        c1 = min(c for _, c in main["cells"])
        c2 = max(c for _, c in main["cells"])
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                grid[r][c] = main["color"]
    elif mutation == "extra_color":
        r, c = objs[-1]["cells"][0]
        grid[r][c] = next(v for v in range(1, 10) if v not in (grid[0][0], objs[0]["color"]))
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True, 0], [0, 0]]])
def test_malformed_inputs_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_real_racket_reference_matches_python_and_generator_mirrors():
    try:
        grids = [pair["input"] for pair in canonical_pairs()]
        grids += [gen.generate(14000 + i, i) for i in range(24)]
        actual = racket_outputs(grids)
    except Exception as exc:
        if "RACKET_MISSING" in str(exc) or "not on PATH" in str(exc):
            pytest.skip(str(exc))
        raise
    expected = [authority_output(grid) for grid in grids]
    assert actual == expected
    assert actual == [gen.rule_mirror(grid) for grid in grids]


def test_default_key_and_distractor_controls_are_not_one_to_one_locked():
    pairs = {
        (observed(gen.generate(17000 + seed, index))["key"],
         observed(gen.generate(17000 + seed, index))["n_distractors"])
        for seed in range(16)
        for index in range(16)
    }
    assert all(len({d for k, d in pairs if k == key}) > 1 for key in range(1, 5))
    assert all(len({k for k, d in pairs if d == count}) > 1 for count in range(4))


def test_difficulty_bands_change_incidental_pixels_not_observed_axes():
    differing = 0
    requested = {"grid_profile": "8x10", "key": 3, "main_size": 7, "n_distractors": 2}
    for index in range(24):
        grids = [gen.generate(18000 + index, index, difficulty=band, **requested)
                 for band in ("easy", "medium", "hard")]
        assert all(observed(grid) == requested for grid in grids)
        differing += len({repr(grid) for grid in grids}) > 1
    assert differing >= 20
