"""Regression suite for 23220e3be06f; workspace helpers are independent."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    canonical_profile,
    colored_component_count,
    crop_motif,
    dihedral_images,
    load_generator,
    normalized_rule_hash,
    observed,
    racket_outputs,
    reference_output,
    rotations_only_rival,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_and_all_canonical_pairs() -> None:
    assert gen.RULE_HASH == normalized_rule_hash() == "710976311dfe"
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert reference_output(pair["input"]) == pair["output"]
        assert gen.reference_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("palette_mode", ["overlap", "distinct"])
def test_exact_overrides_are_observable_and_band_safe(
    band: str | None, palette_mode: str
) -> None:
    requested = {
        "grid_h": 10,
        "grid_w": 11,
        "code": 6,
        "n_cells": 8,
        "palette_mode": palette_mode,
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert gen.reference_output(grid) == reference_output(grid)


@pytest.mark.parametrize(
    "axis,value",
    [
        ("unknown_axis", 1),
        ("grid_h", 6),
        ("grid_h", 11),
        ("grid_w", 7),
        ("grid_w", 12),
        ("code", 0),
        ("code", 7),
        ("n_cells", 3),
        ("n_cells", 9),
        ("palette_mode", "monochrome"),
        ("grid_h", True),
        ("grid_w", "9"),
        ("code", 2.0),
        ("n_cells", None),
    ],
)
def test_invalid_overrides_reject(axis: str, value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, difficulty="hard", **{axis: value})


@pytest.mark.parametrize("difficulty", ["invalid", 0, True])
def test_invalid_difficulty_rejects(difficulty: object) -> None:
    with pytest.raises(ValueError):
        gen.generate(1, 2, difficulty=difficulty)


@pytest.mark.parametrize("code", range(1, 7))
def test_every_command_uses_canonical_order(code: int) -> None:
    grid = gen.generate(
        70 + code,
        code,
        difficulty="hard",
        grid_h=9,
        grid_w=10,
        code=code,
        n_cells=6,
        palette_mode="distinct",
    )
    motif = crop_motif(grid)
    assert len(set(dihedral_images(motif))) == 8
    assert gen.reference_output(grid) == reference_output(grid)


@pytest.mark.parametrize("band_index,band", enumerate(("easy", "medium", "hard")))
def test_default_distribution_covers_branches_and_canonical_profiles(
    band_index: int, band: str
) -> None:
    canonical_profiles = {canonical_profile(pair["input"]) for pair in canonical_pairs()}
    codes: set[int] = set()
    cells: set[int] = set()
    modes: set[str] = set()
    profiles: set[tuple[int, int, int]] = set()
    distinct_inputs: set[str] = set()
    for index in range(90):
        seed = 20_000 + band_index * 10_000 + index
        grid = gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(seed, index, difficulty=band)
        facts = observed(grid)
        assert gen.observe_overrides(grid) == facts
        assert gen.reference_output(grid) == reference_output(grid)
        motif = crop_motif(grid)
        assert len({value for row in motif for value in row if value}) == 2
        assert 2 <= colored_component_count(motif) <= 3
        assert len(set(dihedral_images(motif))) == 8
        codes.add(facts["code"])
        cells.add(facts["n_cells"])
        modes.add(facts["palette_mode"])
        profiles.add(canonical_profile(grid))
        distinct_inputs.add(json.dumps(grid, separators=(",", ":")))
    assert codes == set(range(1, 7))
    assert cells == set(range(4, 9))
    assert modes == {"overlap", "distinct"}
    assert canonical_profiles <= profiles
    assert len(distinct_inputs) >= 87


def test_four_item_teaching_schedule_supports_every_query_rotation() -> None:
    for seed in range(24):
        for start in range(12):
            codes = [
                observed(gen.generate(seed, start + offset, difficulty="medium"))["code"]
                for offset in range(4)
            ]
            assert codes[0] == codes[2]
            assert codes[1] == codes[3]
            assert codes[0] != codes[1]


def test_difficulty_changes_defaults_without_restricting_domains() -> None:
    rows = [gen.generate(998, 13, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in rows}) > 1
    requested = {
        "grid_h": 7,
        "grid_w": 8,
        "code": 5,
        "n_cells": 4,
        "palette_mode": "overlap",
    }
    for band in ("easy", "medium", "hard"):
        assert observed(gen.generate(998, 13, difficulty=band, **requested)) == requested


def test_validator_rejects_structural_impostors() -> None:
    base = gen.generate(
        99,
        14,
        grid_h=8,
        grid_w=9,
        code=2,
        n_cells=5,
        palette_mode="distinct",
    )
    assert gen.self_check(base) == []

    cases: dict[str, object] = {
        "empty": [],
        "ragged": [[0], [0, 0]],
        "bool_cells": [[True] * 9 for _ in range(8)],
        "all_background": [[0] * 9 for _ in range(8)],
    }
    missing_code = deepcopy(base)
    missing_code[0][0] = 0
    cases["missing_code"] = missing_code

    extra_top_row = deepcopy(base)
    extra_top_row[0][2] = 7
    cases["extra_top_row"] = extra_top_row

    one_color = deepcopy(base)
    motif_colors = sorted({value for row in crop_motif(one_color) for value in row if value})
    for row in range(len(one_color)):
        for col in range(len(one_color[0])):
            if one_color[row][col] == motif_colors[1]:
                one_color[row][col] = motif_colors[0]
    cases["one_color"] = one_color

    symmetric = [[0] * 9 for _ in range(8)]
    symmetric[0][0] = 2
    for row, col, color in ((3, 3, 4), (3, 4, 5), (4, 3, 5), (4, 4, 4)):
        symmetric[row][col] = color
    cases["symmetric"] = symmetric

    touches_edge = deepcopy(base)
    motif = crop_motif(base)
    for row in range(len(touches_edge)):
        for col in range(len(touches_edge[0])):
            if (row, col) != (0, 0):
                touches_edge[row][col] = 0
    for row, values in enumerate(motif):
        for col, value in enumerate(values):
            touches_edge[1 + row][col] = value
    cases["touches_edge"] = touches_edge

    for name, grid in cases.items():
        assert gen.self_check(grid), name


def test_mutation_fixtures_are_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_canonical_fitting_rotation_shortcut_has_flip_counterexamples() -> None:
    pairs = canonical_pairs()
    assert all(rotations_only_rival(pair["input"]) == pair["output"] for pair in pairs)
    assert "rotations_only" in gen.CANONICAL_SHORTCUTS
    for code in (5, 6):
        grid = gen.generate(
            401 + code,
            code,
            code=code,
            grid_h=9,
            grid_w=10,
            n_cells=7,
            palette_mode="distinct",
        )
        truth = reference_output(grid)
        assert gen.SEMANTIC_WITNESSES["flip_command"](grid)
        assert gen.SEMANTIC_RIVALS["rotations_only"](grid) == rotations_only_rival(grid)
        assert rotations_only_rival(grid) != truth


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_default_lesson_and_query_rotation_is_identifiable(band: str) -> None:
    for start in range(36):
        grids = [gen.generate(90_000 + start, start + offset, difficulty=band) for offset in range(4)]
        labelled = [{"input": grid, "output": reference_output(grid)} for grid in grids]
        for query_index in range(4):
            demos = [episode for index, episode in enumerate(labelled) if index != query_index]
            query = labelled[query_index]
            assert gen.lesson_identifiable(demos, query) == [], (band, start, query_index)


def test_generation_is_fresh_and_global_rng_pure() -> None:
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(42, 9, difficulty="hard")
    assert random.getstate() == before
    second = gen.generate(42, 9, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 0
    assert second[0][0] != 0


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
        gen.generate(
            55_000 + code,
            code,
            code=code,
            grid_h=8 + code % 2,
            grid_w=9 + code % 2,
            n_cells=4 + code % 5,
            palette_mode="distinct",
        )
        for code in range(1, 7)
    ]
    assert racket_outputs(grids) == [reference_output(grid) for grid in grids]
