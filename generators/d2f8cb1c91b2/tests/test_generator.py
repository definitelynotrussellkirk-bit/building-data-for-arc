"""Focused regressions for the d2f8cb1c91b2 generator repair."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    TRANSFORMS,
    canonical_pairs,
    component_count,
    infer_matches,
    keep_y_conflict_rival,
    load_generator,
    matching_is_conflict_rival,
    merge_stats,
    no_transform_rival,
    observed,
    racket_outputs,
    reference_output,
    split_panels,
    transform_grid,
    transpose_alias_rival,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")
CODES = tuple(code for code in TRANSFORMS if code != "id")


def test_public_contract_is_pinned_and_honest() -> None:
    assert gen.RULE_HASH == "a401bcfe7b0a"
    assert gen.VERSION == "3.0.0"
    assert set(gen.AXES) == {"transform", "palette_size"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    assert gen.EXAMPLES_NEEDED == 3


def test_all_d4_transforms_match_independent_coordinates() -> None:
    matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    for code in TRANSFORMS:
        assert gen._transform_grid(matrix, code) == transform_grid(matrix, code), code
    images = {json.dumps(gen._transform_grid(matrix, code)) for code in TRANSFORMS}
    assert len(images) == 8


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_inputs_are_accepted_and_python_oracle_matches(pair) -> None:
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert reference_output(pair["input"]) == pair["output"]
    assert gen.reference_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("code", CODES)
@pytest.mark.parametrize("palette_size", (3, 4))
def test_exact_overrides_are_real_and_observable(band, code, palette_size) -> None:
    options = {"transform": code, "palette_size": palette_size}
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert infer_matches(grid) == [code]
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert gen.reference_output(grid) == reference_output(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("unknown_axis", 1),
        ("transform", "id"),
        ("transform", "bad"),
        ("transform", 3),
        ("palette_size", 2),
        ("palette_size", 5),
        ("palette_size", True),
        ("palette_size", "3"),
        ("palette_size", 3.0),
    ],
)
def test_invalid_overrides_reject_loudly(key, value) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", ("invalid", 0, True))
def test_invalid_difficulty_rejects(difficulty) -> None:
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=difficulty)


def test_retained_transform_alias_bug_is_fixed() -> None:
    grids = {
        code: gen.generate(17, 0, difficulty="easy", transform=code, palette_size=3)
        for code in ("r3", "tr", "atr")
    }
    assert len({json.dumps(grid, separators=(",", ":")) for grid in grids.values()}) == 3
    assert {code: infer_matches(grid) for code, grid in grids.items()} == {
        "r3": ["r3"],
        "tr": ["tr"],
        "atr": ["atr"],
    }


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_default_distribution_teaches_every_merge_branch_at_canonical_scale(band) -> None:
    transforms: set[str] = set()
    palettes: set[int] = set()
    unique: set[str] = set()
    components: list[int] = []
    for index in range(120):
        grid = gen.generate(30_000 + index, index, difficulty=band)
        assert len(grid) == 3 and all(len(row) == 15 for row in grid)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(30_000 + index, index, difficulty=band)
        stats = merge_stats(grid)
        assert stats["x_only"] >= 1
        assert stats["y_only"] >= 1
        assert stats["match"] >= 1
        assert stats["conflict"] >= 1
        assert any(value == 9 for row in reference_output(grid) for value in row)
        facts = observed(grid)
        transforms.add(facts["transform"])
        palettes.add(facts["palette_size"])
        unique.add(json.dumps(grid, separators=(",", ":")))
        components.append(component_count(grid))
    assert transforms == set(CODES)
    assert palettes == {3, 4}
    assert len(unique) >= 116
    assert max(components) <= 10


def test_semantic_rivals_have_generated_counterexamples() -> None:
    r3 = gen.generate(401, 0, transform="r3", palette_size=3)
    atr = gen.generate(402, 2, transform="atr", palette_size=4)
    ordinary = gen.generate(403, 1, transform="r1", palette_size=3)
    for grid in (r3, atr):
        assert transpose_alias_rival(grid) != reference_output(grid)
        assert gen.SEMANTIC_RIVALS["transpose_aliases"](grid) == transpose_alias_rival(grid)
        assert gen.SEMANTIC_WITNESSES["transpose_alias_counterexample"](grid)
    assert no_transform_rival(ordinary) != reference_output(ordinary)
    assert keep_y_conflict_rival(ordinary) != reference_output(ordinary)
    assert matching_is_conflict_rival(ordinary) != reference_output(ordinary)


def test_every_four_item_schedule_window_survives_query_rotation() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(48):
            grids = [gen.generate(80_000 + start, start + offset, difficulty=band) for offset in range(4)]
            pairs = [{"input": grid, "output": reference_output(grid)} for grid in grids]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                assert gen.lesson_identifiable(demos, query) == [], (band, start, query_index)
                assert any(
                    transpose_alias_rival(demo["input"]) != demo["output"]
                    for demo in demos
                )


def test_validator_rejects_structural_and_semantic_impostors() -> None:
    base = gen.generate(99, 14, transform="r3", palette_size=4)
    cases = {
        "empty": [],
        "ragged": [[0], [0, 0]],
        "bool": [[True] * 15 for _ in range(3)],
    }
    missing_separator = deepcopy(base)
    missing_separator[0][3] = 0
    cases["missing_separator"] = missing_separator
    extra_separator = deepcopy(base)
    extra_separator[0][0] = 5
    cases["extra_separator"] = extra_separator
    identity_demo = deepcopy(base)
    a, _, _, _ = split_panels(identity_demo)
    for row in range(3):
        identity_demo[row][4:7] = a[row]
    cases["identity_demo"] = identity_demo
    no_conflict = deepcopy(base)
    _, _, x, _ = split_panels(no_conflict)
    for row in range(3):
        no_conflict[row][12:15] = [0, 0, 0]
    # An all-zero Y can only remove conflicts, regardless of transformed X.
    cases["no_conflict"] = no_conflict
    for name, grid in cases.items():
        assert gen.self_check(grid), name


def test_python_hash_seed_does_not_change_generation() -> None:
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_real_racket_reference_when_available() -> None:
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [
        gen.generate(55_000 + index, index, transform=code, palette_size=3 + index % 2)
        for index, code in enumerate(CODES)
    ]
    assert racket_outputs(grids) == [reference_output(grid) for grid in grids]
