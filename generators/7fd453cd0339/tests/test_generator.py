"""Focused regression suite for the 7fd453cd0339 generator repair."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import TASK_ID, components, corner_output, load_generator, observed, witness_differences

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def test_pins_rule_and_declares_only_real_axes():
    assert gen.RULE_HASH == "de0c1931e97a"
    assert gen.VERSION == "3.0.0"
    assert set(gen.AXES) == {"grid_h", "grid_w", "rectangles", "palette_kind", "texture"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", PAIRS, ids=lambda pair: f"{pair['split']}{pair['pair_index']}")
def test_canonical_examples_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert corner_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(grid_h=6, grid_w=8, rectangles=2, palette_kind="canonical_24", texture="canonical"),
        dict(grid_h=6, grid_w=8, rectangles=2, palette_kind="canonical_35", texture="counterexample"),
        dict(grid_h=14, grid_w=18, rectangles=4, palette_kind="broad", texture="canonical"),
        dict(grid_h=14, grid_w=18, rectangles=4, palette_kind="broad", texture="counterexample"),
    ],
)
def test_every_exact_override_is_observable_in_every_band(band, options):
    grid = gen.generate(701, 19, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 5),
        ("grid_h", 15),
        ("grid_w", 7),
        ("grid_w", 19),
        ("rectangles", 1),
        ("rectangles", 5),
        ("palette_kind", "warm"),
        ("texture", "line_rects"),
        ("grid_h", True),
        ("rectangles", 2.0),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_schedule_is_six_periodic_and_alternates_anchor_and_counterexample():
    expected = (
        "canonical_a",
        "counterexample",
        "canonical_b",
        "counterexample",
        "canonical_c",
        "counterexample",
    )
    assert gen.SCHEDULE_PROFILES == expected
    assert gen.LESSON_SCHEDULE_PERIOD == 6
    for start in range(12):
        assert gen.schedule_profile(999, start) == expected[start % 6]
    for start in range(6):
        window = [gen.schedule_profile(0, start + offset) for offset in range(4)]
        assert window.count("counterexample") == 2


def test_default_schedule_realizes_all_public_linked_profiles():
    strict_signatures = set()
    for index in (0, 2, 4):
        grid = gen.generate(123, index)
        assert gen.strict_canonical_like(grid) == []
        strict_signatures.add(gen.canonical_profile_signature(grid))
    assert strict_signatures == gen.CANONICAL_PROFILE_SIGNATURES


def test_counterexample_contains_line_and_repeated_color_components():
    grid = gen.generate(
        13,
        1,
        grid_h=6,
        grid_w=8,
        rectangles=2,
        palette_kind="canonical_24",
        texture="counterexample",
    )
    comps = components(grid)
    assert len(comps) == 2
    assert comps[0][0] == comps[1][0]
    shapes = []
    for _, cells in comps:
        rows = {r for r, _ in cells}
        cols = {c for _, c in cells}
        shapes.append((len(rows), len(cols)))
    assert any(h == 1 or w == 1 for h, w in shapes)
    assert any(h >= 2 and w >= 3 for h, w in shapes)
    assert corner_output(grid) != grid


def test_declared_shortcuts_fit_all_canonical_pairs_and_fail_counterexample():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS), name
    grid = gen.generate(13, 1, grid_h=6, grid_w=8, rectangles=2,
                        palette_kind="canonical_24", texture="counterexample")
    expected = corner_output(grid)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        prediction = rival(grid)
        assert prediction != expected, name
        assert witness_differences(expected, prediction), name


def _pair(grid):
    return {"input": grid, "output": corner_output(grid)}


@pytest.mark.parametrize("start", range(6))
def test_every_four_pair_schedule_window_is_rotation_identifiable(start):
    pairs = [_pair(gen.generate(9001, start + offset)) for offset in range(4)]
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        query = pairs[query_index]
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(demo["input"]) != demo["output"] for demo in demos), (
                start,
                query_index,
                name,
            )


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_defaults_are_deterministic_valid_and_cover_domains(band):
    shapes = set()
    object_counts = set()
    palettes = set()
    textures = set()
    for index in range(120):
        grid = gen.generate(4000 + index, index, difficulty=band)
        assert grid == gen.generate(4000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        obs = gen.observe_overrides(grid)
        shapes.add((obs["grid_h"], obs["grid_w"]))
        object_counts.add(obs["rectangles"])
        palettes.add(obs["palette_kind"])
        textures.add(obs["texture"])
    assert len(shapes) >= 15
    assert object_counts == {2, 3, 4}
    assert palettes == {"canonical_24", "canonical_35", "broad"}
    assert textures == {"canonical", "counterexample"}


def test_self_check_rejects_solid_impostor_and_malformed_inputs():
    assert gen.self_check([[2] * 8 for _ in range(6)])
    assert gen.self_check([])
    assert gen.self_check([[]])
    assert gen.self_check([[0, 0], [0]])
    assert gen.self_check([[True] * 8 for _ in range(6)])


def test_rule_mirror_is_pure():
    grid = gen.generate(77, 5)
    before = deepcopy(grid)
    assert gen.rule_mirror(grid) == corner_output(grid)
    assert grid == before


def test_difficulty_bands_change_anchor_phase_without_breaking_alternation():
    profiles = {
        band: tuple(gen.schedule_profile(0, index, difficulty=band) for index in range(6))
        for band in ("easy", "medium", "hard")
    }
    assert len(set(profiles.values())) == 3
    for sequence in profiles.values():
        assert sum(name == "counterexample" for name in sequence) == 3
        for start in range(6):
            window = [sequence[(start + offset) % 6] for offset in range(4)]
            assert window.count("counterexample") == 2


def test_real_racket_reference_matches_independent_oracle():
    """The unchanged canonical program labels both public and adversarial cases."""
    from arc_repl.racket_bridge import racket_runtime_status
    from reference_probe import racket_outputs

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    witness = gen.generate(
        13,
        1,
        grid_h=6,
        grid_w=8,
        rectangles=2,
        palette_kind="canonical_24",
        texture="counterexample",
    )
    grids = [pair["input"] for pair in PAIRS] + [witness]
    assert racket_outputs(grids) == [corner_output(grid) for grid in grids]


def test_retained_counterexample_replays_generator_rule_and_all_shortcuts():
    import json

    fixture_path = HOME / "counterexamples" / "line-plus-same-color-rectangle.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    case = fixture["generator_case"]
    grid = gen.generate(case["seed"], case["index"], **case["overrides"])
    assert grid == fixture["input"]
    assert gen.self_check(grid) == []
    assert corner_output(grid) == fixture["intended_output"]
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        retained = fixture["rivals"][name]
        assert rival(grid) == retained["output"]
        assert witness_differences(fixture["intended_output"], retained["output"]) == [
            tuple(item) for item in retained["differing_cells"]
        ]
