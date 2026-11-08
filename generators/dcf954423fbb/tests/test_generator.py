"""Focused regression tests for the repaired dcf954423fbb generator."""
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
from semantic_probe import (  # noqa: E402
    LESSON_RIVALS,
    RIVALS,
    all_blue_recolors,
    audit,
    border_cells_only,
    border_sides,
    canonical_pairs,
    components,
    explicit_right_edge_witness,
    horizontal_edges_only,
    load_generator,
    min_border_distance,
    near_border_recolors,
    observed,
    three_nearest_components,
    two_nearest_components,
    racket_outputs,
    rule_output,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {(8, 10, 3), (9, 12, 3), (8, 11, 3), (10, 13, 3)}


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda pair: f"{pair['split']}-{pair['pair_index']}")
def test_accepts_canonical_inputs_and_independent_oracle_matches(pair):
    assert GEN.self_check(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 8, "grid_w": 10, "n_blobs": 3},
        {"grid_h": 10, "grid_w": 13, "n_blobs": 6},
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, options):
    grid = GEN.generate(71, 19, difficulty=band, **options)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == options
    assert {key: observed(grid)[key] for key in options} == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 3),
        ("grid_h", 7),
        ("grid_h", 11),
        ("grid_w", 9),
        ("grid_w", 14),
        ("n_blobs", 2),
        ("n_blobs", 7),
        ("n_blobs", 4.5),
        ("grid_h", True),
        ("grid_w", "12"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_deterministic_lawful_and_refutes_rivals(band):
    unique = set()
    sides = set()
    exact_profiles = set()
    for index in range(96):
        seed = 2100 + index
        sample_index = index * 11 + 3
        grid = GEN.generate(seed, sample_index, difficulty=band)
        assert grid == GEN.generate(seed, sample_index, difficulty=band)
        assert GEN.self_check(grid) == []
        truth = rule_output(grid)
        assert GEN._apply_rule(grid) == truth
        for name, rival in RIVALS.items():
            assert rival(grid) != truth, f"{name} survived band={band} index={index}"
        stats = observed(grid)
        assert stats["side_only_blobs"] >= 1
        assert stats["near_border_interior"] >= 1
        sides.update(stats["touched_sides"])
        exact_profiles.add((len(grid), len(grid[0]), len(set(sum(grid, [])))))
        unique.add(json.dumps(grid, separators=(",", ":")))
    assert sides == {"top", "bottom", "left", "right"}
    assert exact_profiles <= CANONICAL_PROFILES
    assert len(unique) >= 80



def test_reusable_probe_reports_zero_surviving_lesson_rivals():
    report = audit(GEN, per_band=8)
    for band, row in report["per_band"].items():
        assert row["lesson_windows"] == 16, band
        for name in LESSON_RIVALS:
            assert row[f"lesson_survives_{name}"] == 0, (band, name)
            assert row[f"lesson_changes_query_{name}"] == 0, (band, name)
    assert report["canonical_rival_fit"]["three_nearest_components"] == {
        "fits": 5,
        "pairs": 5,
    }

def test_explicit_right_edge_component_rejects_horizontal_only_shortcut():
    grid = explicit_right_edge_witness()
    assert GEN.self_check(grid) == []
    truth = rule_output(grid)
    assert horizontal_edges_only(grid) != truth
    assert truth[2][9] == truth[3][9] == truth[3][8] == 2


def test_canonical_shortcuts_require_generated_counterexamples():
    pairs = canonical_pairs()
    assert all(
        near_border_recolors(pair["input"]) == pair["output"]
        for pair in pairs
    )
    assert all(
        three_nearest_components(pair["input"]) == pair["output"]
        for pair in pairs
    )
    assert any(
        two_nearest_components(pair["input"]) != pair["output"]
        for pair in pairs
    )
    for index in range(24):
        grid = GEN.generate(811 + index, index, difficulty="medium")
        assert near_border_recolors(grid) != rule_output(grid)


def test_all_mandatory_semantic_witnesses_are_structural_not_metadata_only():
    grid = GEN.generate(901, 7, grid_h=8, grid_w=10, n_blobs=3)
    height, width = len(grid), len(grid[0])
    parts = components(grid, 1)
    sides = [border_sides(part, height, width) for part in parts]
    assert any(side in ({"left"}, {"right"}) for side in sides)
    assert any(not side and min_border_distance(part, height, width) == 1 for part, side in zip(parts, sides))
    assert any(side and any(0 < r < height - 1 and 0 < c < width - 1 for r, c in part) for part, side in zip(parts, sides))
    assert any(not side for side in sides)
    truth = rule_output(grid)
    assert border_cells_only(grid) != truth
    assert all_blue_recolors(grid) != truth


def test_semantic_contract_names_and_rivals_agree_with_independent_probe():
    expected = set(LESSON_RIVALS)
    assert set(GEN.SEMANTIC_RIVALS) == expected
    assert set(GEN.LESSON_COMPETITORS) == expected
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "near_border_recolors",
        "three_nearest_components",
    }
    expected_witnesses = {
        "side_only_border_component",
        "near_border_interior_component",
        "border_component_extends_inward",
        "interior_component_preserved",
        "border_component_count_not_two",
        "border_component_count_not_three",
    }
    assert set(GEN.SEMANTIC_WITNESSES) == expected_witnesses
    assert set(GEN.WITNESS_RIVALS) == expected_witnesses

    witness_hits = {name: 0 for name in expected_witnesses}
    rival_refutations = {name: 0 for name in expected}
    for index in range(24):
        grid = GEN.generate(1200 + index, index)
        truth = rule_output(grid)
        for name, predicate in GEN.SEMANTIC_WITNESSES.items():
            if not predicate(grid):
                continue
            witness_hits[name] += 1
            for rival_name in GEN.WITNESS_RIVALS[name]:
                assert GEN.SEMANTIC_RIVALS[rival_name](grid) != truth
        for name, rival in GEN.SEMANTIC_RIVALS.items():
            assert rival(grid) == LESSON_RIVALS[name](grid)
            rival_refutations[name] += rival(grid) != truth
    assert all(witness_hits.values())
    assert all(rival_refutations.values())


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_cyclic_three_demo_lesson_refutes_fixed_count_and_declared_competitors(band):
    pairs = []
    for index in range(16):
        grid = GEN.generate(3300 + index, index, difficulty=band)
        pairs.append({"input": grid, "output": rule_output(grid)})
    for start in range(len(pairs)):
        demos = [deepcopy(pairs[(start + offset) % len(pairs)]) for offset in range(3)]
        query = deepcopy(pairs[(start + 3) % len(pairs)])
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in LESSON_RIVALS.items():
            assert not all(
                rival(demo["input"]) == demo["output"] for demo in demos
            ), f"{name} survived band={band} start={start}"


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 10 for _ in range(8)],
        [[0] * 10 for _ in range(8)],
        [[0] * 10 for _ in range(8)] + [[11] * 10],
    ],
)
def test_malformed_or_semantically_empty_grid_is_diagnostic_not_exception(grid):
    assert GEN.self_check(grid)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from semantic_probe import load_generator;"
        "print(json.dumps(load_generator(sys.argv[2]).generate(31,8,difficulty='hard')))"
    )
    generator_path = Path(GEN.__file__).resolve()
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    script,
                    str(HOME / "workspace"),
                    str(generator_path),
                ],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_rule_hash_and_public_metadata_are_pinned():
    assert GEN.RULE_HASH == "77b049629337"
    assert GEN.VERSION == "2.1.0"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_blobs"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.EXAMPLES_NEEDED == 3


def test_real_racket_authority_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [GEN.generate(5000 + index, index, difficulty="medium") for index in range(32)]
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]
