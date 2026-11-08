"""Task-local regression tests with an oracle independent of generator internals."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    geometry_output,
    load_generator,
    observed,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_accepts_every_canonical_input_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert geometry_output(pair["input"]) == pair["output"]


def test_selected_rule_hash_is_pinned():
    assert gen.RULE_HASH == "1724b71ea895"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_observable_overrides_in_every_band(band):
    options = {
        "grid_h": 12,
        "grid_w": 6,
        "seed_count": 6,
        "color_profile": "mixed",
    }
    grid = gen.generate(41, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "options",
    [
        {"typo_axis": 1},
        {"grid_h": 5},
        {"grid_h": 13},
        {"grid_w": 5},
        {"grid_w": 13},
        {"seed_count": 0},
        {"seed_count": 7},
        {"color_profile": "unknown"},
        {"grid_h": True},
        {"grid_w": 8.0},
        {"seed_count": "2"},
        {"color_profile": 5},
        {"seed_count": 1, "color_profile": "mixed"},
    ],
)
def test_invalid_or_incompatible_overrides_fail_loudly(options):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **options)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_clean_deterministic_and_has_canonical_support(band):
    shapes = set()
    profiles = set()
    exact_profile_hits = 0
    for index in range(160):
        seed = 5000 + index
        sample_index = 17 * index + 3
        grid = gen.generate(seed, sample_index, difficulty=band)
        assert grid == gen.generate(seed, sample_index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == observed(grid)
        assert geometry_output(grid) != grid
        stats = observed(grid)
        shapes.add((stats["grid_h"], stats["grid_w"]))
        profiles.add(stats["color_profile"])
        exact_profile_hits += (
            (stats["grid_h"], stats["grid_w"]) in {(8, 8), (9, 9)}
            and stats["color_profile"] != "mixed"
        )
    assert exact_profile_hits >= 12
    assert {"canonical", "monochrome", "mixed"} <= profiles
    assert {(8, 8), (9, 9)} <= shapes


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 8 for _ in range(8)],
        [[0] * 5 for _ in range(6)],
        [[0] * 13 for _ in range(8)],
    ],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_validator_rejects_destructive_mutations():
    original = gen.generate(
        90,
        3,
        grid_h=8,
        grid_w=8,
        seed_count=3,
        color_profile="mixed",
    )

    border = [row[:] for row in original]
    source = next((r, c) for r, row in enumerate(border) for c, value in enumerate(row) if value)
    border[source[0]][source[1]] = 0
    border[0][0] = 5
    assert gen.self_check(border)

    cyan_source = [row[:] for row in original]
    r, c = next((r, c) for r, row in enumerate(cyan_source) for c, value in enumerate(row) if value)
    cyan_source[r][c] = 8
    assert gen.self_check(cyan_source)

    touching = [[0] * 8 for _ in range(8)]
    touching[3][3] = 5
    touching[3][4] = 5
    assert gen.self_check(touching)

    too_many = [[0] * 8 for _ in range(8)]
    points = [(1, 1), (1, 3), (1, 5), (3, 1), (3, 3), (3, 5), (5, 1)]
    for r, c in points:
        too_many[r][c] = 5
    assert gen.self_check(too_many)


def test_canonical_shortcut_fits_canonical_but_generated_witness_refutes_it():
    shortcut = gen.CANONICAL_SHORTCUTS["only_color_five_centers"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs())
    witness = gen.generate(
        7,
        11,
        grid_h=8,
        grid_w=8,
        seed_count=2,
        color_profile="monochrome",
    )
    assert gen.SEMANTIC_WITNESSES["non_five_center_matters"](witness)
    assert shortcut(witness) != geometry_output(witness)


def test_every_witness_claim_names_a_real_disagreeing_rival():
    grids = [
        gen.generate(200 + i, i, seed_count=2, color_profile="monochrome")
        for i in range(12)
    ]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        fired = 0
        for grid in grids:
            if not gen.SEMANTIC_WITNESSES[witness_name](grid):
                continue
            fired += 1
            expected = geometry_output(grid)
            assert any(gen.SEMANTIC_RIVALS[name](grid) != expected for name in rival_names)
        assert fired


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(311, index, difficulty="hard") for index in range(32)]
    assert racket_outputs(grids) == [geometry_output(grid) for grid in grids]

@pytest.mark.parametrize(
    "seed,start",
    [
        (1841668169, 14),
        (672830305, 25),
    ],
    ids=["official-easy-lesson-14", "official-easy-lesson-25"],
)
def test_official_four_pair_lessons_survive_every_query_rotation(seed, start):
    """Every cyclic query choice must leave demos that identify the rule.

    These two deterministic schedules are regression cases discovered by
    rotating the query through the official lesson-census materialization.
    """
    grids = [
        gen.generate(seed, start + offset, difficulty="easy")
        for offset in range(4)
    ]
    pairs = [(grid, geometry_output(grid)) for grid in grids]
    assert sum(
        observed(grid)["color_profile"] != "canonical" for grid in grids
    ) >= 2

    rivals = dict(gen.SEMANTIC_RIVALS)
    rivals.update(gen.LESSON_COMPETITORS)
    rivals.update(gen.CANONICAL_SHORTCUTS)
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        for name, rival in rivals.items():
            assert any(rival(grid) != output for grid, output in demos), (
                seed,
                start,
                query_index,
                name,
            )
