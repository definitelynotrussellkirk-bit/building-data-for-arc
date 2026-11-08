"""Task-local regression tests for the reviewed 3065bdeaa7b0 sampler."""
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
    RIVALS,
    canonical_pairs,
    first_two_occurrences_of_every_color,
    first_two_pairs_only,
    intended_output,
    load_generator,
    observed,
    racket_outputs,
    witness_flags,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def _lesson(seed, start, band):
    pairs = []
    for offset in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": intended_output(grid)})
    return pairs


def test_pins_canonical_authority_and_declares_exact_axes():
    assert gen.RULE_HASH == "1bc66fae4078"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_pairs", "n_decoys"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_anchor",
        "pair_count",
        "one_pair_decoy",
        "combined",
    )
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "first_two_pairs_only",
        "first_two_occurrences_of_every_color",
    }


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: f"{len(p['input'])}x{len(p['input'][0])}")
def test_accepts_canonical_and_independent_oracle_matches(pair):
    assert gen.self_check(deepcopy(pair["input"])) == []
    assert gen.strict_canonical_like(deepcopy(pair["input"])) == []
    assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 9, "grid_w": 9, "n_pairs": 1, "n_decoys": 0},
        {"grid_h": 18, "grid_w": 18, "n_pairs": 4, "n_decoys": 2},
        {"grid_h": 12, "grid_w": 13, "n_pairs": 3, "n_decoys": 1},
    ],
)
def test_exact_overrides_are_constructive_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(17, 9, difficulty=band, **options)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 8),
        ("grid_h", 19),
        ("grid_w", 8),
        ("grid_w", 19),
        ("n_pairs", 0),
        ("n_pairs", 5),
        ("n_decoys", -1),
        ("n_decoys", 3),
        ("n_pairs", 2.5),
        ("grid_h", True),
        ("n_decoys", "2"),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_cyclic_three_demo_lesson_refutes_all_declared_rivals(band):
    period = len(gen.SCHEDULE_PROFILES)
    for start in range(period):
        lesson = _lesson(314159, start, band)
        demos, query = lesson[: gen.EXAMPLES_NEEDED], lesson[-1]
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_schedule_has_canonical_anchors_and_semantic_witnesses_in_each_band(band):
    profiles = []
    for sample_index in range(8):
        grid = gen.generate(2718, sample_index, difficulty=band)
        profiles.append(gen.schedule_profile(2718, sample_index, band))
        assert gen.self_check(grid) == []
        stats = observed(grid)
        if sample_index % 4 == 0:
            assert gen.strict_canonical_like(grid) == []
            assert stats["n_pairs"] == 2
            assert stats["n_decoys"] == 0
        elif sample_index % 4 == 2:
            assert stats["n_pairs"] == 1
            assert stats["n_decoys"] == 1
            assert witness_flags(grid)["ignored_nonpair_color"]
        else:
            flags = witness_flags(grid)
            assert all(flags.values()), flags
            intended = intended_output(grid)
            for name, rival in RIVALS.items():
                assert rival(grid) != intended, name
    assert set(profiles) == set(gen.SCHEDULE_PROFILES)


@pytest.mark.parametrize("sample_index", [1, 3])
def test_difficulty_band_changes_unoverridden_rich_dimensions(sample_index):
    easy = observed(gen.generate(12345, sample_index, difficulty="easy"))
    medium = observed(gen.generate(12345, sample_index, difficulty="medium"))
    hard = observed(gen.generate(12345, sample_index, difficulty="hard"))
    assert easy["grid_h"] < hard["grid_h"]
    assert easy["grid_w"] < hard["grid_w"]
    assert len({(x["grid_h"], x["grid_w"]) for x in (easy, medium, hard)}) >= 2


def test_declared_shortcuts_fit_every_canonical_pair_and_generated_cases_refute_them():
    for pair in canonical_pairs():
        assert first_two_pairs_only(pair["input"]) == pair["output"]
        assert first_two_occurrences_of_every_color(pair["input"]) == pair["output"]
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            assert rival(pair["input"]) == pair["output"], name
    grid = gen.generate(99, 1, difficulty="medium")
    intended = intended_output(grid)
    assert first_two_pairs_only(grid) != intended
    assert first_two_occurrences_of_every_color(grid) != intended


def test_semantic_witness_claims_are_actual_disagreements():
    grid = gen.generate(404, 3, difficulty="hard")
    intended = intended_output(grid)
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        assert witness(grid), witness_name
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != intended


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(9)]],
)
def test_malformed_grid_returns_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize(
    "mutation",
    ["remove_endpoint", "add_fourth_decoy", "same_row_pair", "foreign_endpoint_on_path"],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(44, 2, grid_h=12, grid_w=13, n_pairs=4, n_decoys=2)
    positions = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                positions.setdefault(color, []).append((r, c))
    pair_color = next(color for color, pts in positions.items() if len(pts) == 2)
    decoy_color = next(color for color, pts in positions.items() if len(pts) == 3)
    if mutation == "remove_endpoint":
        r, c = positions[pair_color][0]
        grid[r][c] = 0
    elif mutation == "add_fourth_decoy":
        grid[0][1] = decoy_color
    elif mutation == "same_row_pair":
        a, b = positions[pair_color]
        grid[b[0]][b[1]] = 0
        target = next(c for c, value in enumerate(grid[a[0]]) if value == 0)
        grid[a[0]][target] = pair_color
    elif mutation == "foreign_endpoint_on_path":
        colors = [color for color, pts in positions.items() if len(pts) == 2]
        a, b = sorted(positions[colors[0]])
        # Pick an interior point on the first horizontal leg and move another endpoint there.
        interior_c = a[1] + (1 if b[1] > a[1] else -1)
        old = positions[colors[1]][0]
        grid[old[0]][old[1]] = 0
        grid[a[0]][interior_c] = colors[1]
    assert gen.self_check(grid)


def test_keyed_rng_is_independent_of_python_hash_seed():
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


def test_lesson_probe_uses_stable_source_bound_sampler_contract():
    import lesson_probe

    assert lesson_probe.TASK_ID == gen.TASK_ID
    assert lesson_probe.BANDS == ("easy", "medium", "hard")
    assert lesson_probe.N_DEMOS == gen.EXAMPLES_NEEDED
    assert lesson_probe.N_QUERIES == 1
    assert lesson_probe.STRIDE % len(gen.SCHEDULE_PROFILES) in {1, 3}
    assert lesson_probe.pinned_seed("easy", 7) == lesson_probe.pinned_seed("easy", 7)
    assert lesson_probe.pinned_seed("easy", 7) != lesson_probe.pinned_seed("hard", 7)


def test_real_racket_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(808, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(12))
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]
