"""Task-local regressions for the transform-sequence stamping generator."""
from __future__ import annotations

import ast
from copy import deepcopy
import itertools
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    RIVALS,
    analyze,
    canonical_pairs,
    load_generator,
    observed,
    rule_output,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "code1",
    "code2",
    "proto_size",
    "n_anchors",
}
BOUNDARIES = {
    "grid_h": (8, 18),
    "grid_w": (9, 18),
    "code1": (1, 7),
    "code2": (1, 7),
    "proto_size": (2, 6),
    "n_anchors": (1, 8),
}
CANONICAL_PROFILES = {
    (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
    for pair in canonical_pairs()
}


def _labeled_pair(seed: int, sample_index: int, band: str | None) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": rule_output(grid)}


def test_axes_metadata_is_a_static_literal() -> None:
    tree = ast.parse(Path(GEN.__file__).read_text(encoding="utf-8"))
    axes_node = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    )
    assert set(ast.literal_eval(axes_node)) == EXPECTED_AXES


def test_public_contract_and_rule_authority_are_pinned() -> None:
    assert GEN.RULE_HASH == "664609196c7e"
    assert set(GEN.AXES) == EXPECTED_AXES
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert set(GEN.SCHEDULE_PROFILES) == {
        "canonical_12x14",
        "canonical_11x13",
        "canonical_12x12",
        "canonical_13x15",
        "generalized_min_8x9",
        "generalized_max_18x18",
    }
    assert GEN.CANONICAL_SHORTCUTS == {}


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}-{pair['pair_index']}",
)
def test_canonical_inputs_are_accepted_and_oracle_matches(pair: dict) -> None:
    before = deepcopy(pair["input"])
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert pair["input"] == before


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_advertised_boundary_combination_is_constructive(band: str | None) -> None:
    for index, combination in enumerate(itertools.product(*BOUNDARIES.values())):
        requested = dict(zip(BOUNDARIES, combination))
        grid = GEN.generate(40_000 + index, 900 + index, difficulty=band, **requested)
        assert GEN.self_check(grid) == [], (band, requested)
        assert observed(grid) == requested
        assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"texture": "no_motifs"},
        {"grid_h": 7},
        {"grid_h": 19},
        {"grid_w": 8},
        {"grid_w": 19},
        {"code1": 0},
        {"code1": 8},
        {"code2": 0},
        {"code2": 8},
        {"proto_size": 1},
        {"proto_size": 7},
        {"n_anchors": 0},
        {"n_anchors": 9},
        {"grid_h": 12.0},
        {"grid_w": True},
        {"code1": "2"},
        {"code2": 4.0},
        {"proto_size": False},
        {"n_anchors": "3"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides: dict) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (True, 0, None),
        (1.0, 0, None),
        ("1", 0, None),
        (1, True, None),
        (1, -1, None),
        (1, 0.0, None),
        (1, "0", None),
        (1, 0, "extreme"),
    ],
)
def test_invalid_generation_coordinates_are_rejected(seed, sample_index, difficulty) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, sample_index, difficulty=difficulty)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_balances_canonical_anchors_with_dimension_extremes(
    band: str | None,
) -> None:
    grids = [GEN.generate(8801, index, difficulty=band) for index in range(24)]
    assert all(GEN.self_check(grid) == [] for grid in grids)
    profiles = [
        (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        for grid in grids
    ]
    assert CANONICAL_PROFILES <= set(profiles)
    assert sum(profile in CANONICAL_PROFILES for profile in profiles) >= 16
    assert (8, 9, 5) in profiles
    assert (18, 18, 5) in profiles
    assert len({str(grid) for grid in grids}) >= 20
    assert grids == [GEN.generate(8801, index, difficulty=band) for index in range(24)]
    assert {GEN.schedule_profile(8801, index, band) for index in range(24)} == set(
        GEN.SCHEDULE_PROFILES
    )


def test_self_check_rejects_destructive_mutations() -> None:
    base = GEN.generate(43, 6, difficulty="hard")
    assert GEN.self_check(base) == []
    info = analyze(base)

    mutations: dict[str, object] = {
        "none": None,
        "empty": [],
        "ragged": deepcopy(base),
        "bad_code": deepcopy(base),
        "row0_payload": deepcopy(base),
        "missing_proto": deepcopy(base),
        "mixed_proto": deepcopy(base),
        "missing_anchors": deepcopy(base),
        "joined_anchor": deepcopy(base),
        "second_proto": deepcopy(base),
    }
    mutations["ragged"][-1].pop()
    mutations["bad_code"][0][0] = 0
    mutations["row0_payload"][0][3] = 5
    for row, col in info["proto"]:
        mutations["missing_proto"][row][col] = 0
    proto_row, proto_col = info["proto"][0]
    mutations["mixed_proto"][proto_row][proto_col] = 8
    for row, col in info["anchors"]:
        mutations["missing_anchors"][row][col] = 0
    anchor_row, anchor_col = info["anchors"][0]
    neighbor = next(
        (row, col)
        for row, col in (
            (anchor_row - 1, anchor_col),
            (anchor_row + 1, anchor_col),
            (anchor_row, anchor_col - 1),
            (anchor_row, anchor_col + 1),
        )
        if 1 <= row < len(base)
        and 0 <= col < len(base[0])
        and mutations["joined_anchor"][row][col] == 0
    )
    mutations["joined_anchor"][neighbor[0]][neighbor[1]] = 4
    mutations["second_proto"][anchor_row][anchor_col] = 9

    for name, grid in mutations.items():
        assert GEN.self_check(grid), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_defaults_refute_sequence_shortcuts_and_lessons_are_identifiable(
    band: str | None,
) -> None:
    assert set(GEN.SEMANTIC_RIVALS) == set(RIVALS)
    for start in range(12):
        demos = [_labeled_pair(7300, start + offset, band) for offset in range(3)]
        query = _labeled_pair(7300, start + 3, band)
        assert GEN.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
        for pair in demos + [query]:
            truth = pair["output"]
            for name, independent_rival in RIVALS.items():
                assert GEN.SEMANTIC_RIVALS[name](deepcopy(pair["input"])) == independent_rival(
                    pair["input"]
                )
                assert independent_rival(pair["input"]) != truth, (band, start, name)
        for witness_name, predicate in GEN.SEMANTIC_WITNESSES.items():
            assert any(predicate(pair["input"]) for pair in demos), witness_name


def test_identity_alias_code7_matches_selected_authority() -> None:
    grid = GEN.generate(
        991,
        4,
        grid_h=12,
        grid_w=14,
        code1=7,
        code2=4,
        proto_size=5,
        n_anchors=3,
    )
    assert GEN.self_check(grid) == []
    assert rule_output(grid) == GEN._rule_output(grid)
