"""Review regressions for the blue-header column-selection generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "2636c90a673a"
ROOT = find_root(__file__)
CANONICAL_LEDGER = canonical_path(ROOT)
HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("reviewed_mask_columns_generator", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

import sys
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    drop_header_only_rival,
    intended_output,
    max_same_color_component_size,
    nonzero_component_count,
    modal_nonzero_header_rival,
    nonzero_header_rival,
    observed_numeric_axes,
    odd_header_rival,
    repeated_nonzero_header_rival,
)

CANONICAL_PROFILES = {(5, 7, 9), (6, 8, 10), (6, 9, 10)}


def _profile(grid):
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def _pinned_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_metadata_pins_the_authority_and_declares_only_real_controls():
    assert GEN.RULE_HASH == "2d7db8fb7aa9"
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.EXAMPLES_NEEDED == 3
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "n_keep",
        "palette_size",
        "body_style",
        "density",
    }


def test_canonical_pairs_are_owned_and_independent_oracle_matches_labels():
    assert CANONICAL_LEDGER.is_file()
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("style", ["row_bands", "column_bands", "mixed"])
@pytest.mark.parametrize("density", ["medium", "dense"])
def test_every_joint_exact_override_is_constructive_and_observable(
    band, style, density
):
    requested = {
        "grid_h": 5,
        "grid_w": 7,
        "n_keep": 5,
        "palette_size": 10,
        "body_style": style,
        "density": density,
    }
    grid = GEN.generate(91, 7, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": 5,
        "grid_w": 7,
        "n_keep": 5,
        "palette_size": 10,
    }
    assert intended_output(grid) != grid[1:]
    assert nonzero_component_count(grid) == 1


@pytest.mark.parametrize(
    "key,value",
    [
        ("grid_h", 4),
        ("grid_h", 10),
        ("grid_h", True),
        ("grid_h", 5.0),
        ("grid_w", 6),
        ("grid_w", 13),
        ("n_keep", 1),
        ("n_keep", 6),
        ("palette_size", 3),
        ("palette_size", 11),
        ("body_style", "unknown"),
        ("density", "sparse"),
        ("typo_axis", 1),
    ],
)
def test_invalid_unknown_and_retired_controls_fail_loudly(key, value):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **{key: value})


def test_default_distribution_is_canonical_scale_connected_and_semantic():
    for band in ("easy", "medium", "hard"):
        for index in range(48):
            grid = GEN.generate(1700 + index, index * 11, difficulty=band)
            saved = deepcopy(grid)
            assert grid == GEN.generate(1700 + index, index * 11, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            assert _profile(grid) in CANONICAL_PROFILES
            assert observed_numeric_axes(grid) == GEN.observe_overrides(grid)
            assert nonzero_component_count(grid) == 1
            assert any(value not in (0, 1) for value in grid[0])
            assert nonzero_header_rival(grid) != intended_output(grid)
            assert odd_header_rival(grid) != intended_output(grid)
            assert drop_header_only_rival(grid) != intended_output(grid)
            assert grid == saved


def test_default_distribution_reaches_canonical_monochrome_component_scale():
    pairs = canonical_pairs(TASK, root=ROOT)
    canonical_sizes = sorted(
        max_same_color_component_size(pair["input"]) for pair in pairs
    )
    canonical_median = canonical_sizes[len(canonical_sizes) // 2]
    generated_sizes = [
        max_same_color_component_size(
            GEN.generate(2600 + index, index * 13, difficulty=band)
        )
        for band in ("easy", "medium", "hard")
        for index in range(24)
    ]
    assert min(generated_sizes) <= canonical_median <= max(generated_sizes)


def test_pinned_profile_floor_has_exact_support_in_every_band():
    for band in ("easy", "medium", "hard"):
        profiles = []
        for index in range(20):
            seed = _pinned_seed(band, index)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profiles.append(_profile(grid))
        assert all(profile in CANONICAL_PROFILES for profile in profiles)


def test_declared_shortcuts_fit_canonical_pairs_and_generated_witnesses_refute_them():
    pairs = canonical_pairs(TASK, root=ROOT)
    shortcuts = {
        "nonzero_header": nonzero_header_rival,
        "odd_header": odd_header_rival,
        "repeated_nonzero_header": repeated_nonzero_header_rival,
        "modal_nonzero_header": modal_nonzero_header_rival,
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == set(shortcuts)
    for name, shortcut in shortcuts.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name

    for band in ("easy", "medium", "hard"):
        for index in range(12):
            grid = GEN.generate(800 + index, index, difficulty=band)
            truth = intended_output(grid)
            assert GEN.SEMANTIC_WITNESSES["colored_header_distractors"](grid)
            assert GEN.SEMANTIC_RIVALS["nonzero_header"](grid) != truth
            assert GEN.SEMANTIC_RIVALS["odd_header"](grid) != truth
            assert GEN.SEMANTIC_RIVALS["repeated_nonzero_header"](grid) != truth
            if index % 2 == 0:
                assert GEN.SEMANTIC_RIVALS["modal_nonzero_header"](grid) != truth


def test_frequency_decoy_schedule_refutes_repetition_and_modal_marker_shortcuts():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert all(
        repeated_nonzero_header_rival(pair["input"]) == pair["output"]
        for pair in pairs
    )
    assert all(
        modal_nonzero_header_rival(pair["input"]) == pair["output"]
        for pair in pairs
    )

    for band in ("easy", "medium", "hard"):
        for start in range(8):
            grids = [
                GEN.generate(4100 + start, index, difficulty=band)
                for index in range(start, start + 4)
            ]
            # Every four-pair window has at least two examples on which the
            # frequency shortcut is wrong, so any query rotation leaves one
            # such witness among the three demonstrations.
            modal_witnesses = sum(
                modal_nonzero_header_rival(grid) != intended_output(grid)
                for grid in grids
            )
            assert modal_witnesses >= 2
            assert all(
                repeated_nonzero_header_rival(grid) != intended_output(grid)
                for grid in grids
            )


def test_every_lesson_and_query_rotation_refutes_all_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            lesson = []
            for index in range(start, start + 4):
                grid = GEN.generate(500 + start, index, difficulty=band)
                lesson.append({"input": grid, "output": intended_output(grid)})
            for held_out, query in enumerate(lesson):
                demos = [pair for i, pair in enumerate(lesson) if i != held_out]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        rival(pair["input"]) != pair["output"] for pair in demos
                    ), (band, start, held_out, name)


def test_self_check_rejects_minimal_impostors_and_malformed_near_misses():
    bad = [
        None,
        [],
        [[]],
        [[1, 1], [1, 1]],
        [[0] * 7 for _ in range(5)],
        [[1] * 7] + [[2] * 7 for _ in range(4)],
        [[1, 1, 0, 0, 0, 0, 0]] + [[0] * 7 for _ in range(4)],
    ]
    for grid in bad:
        reasons = GEN.self_check(grid)
        assert isinstance(reasons, list) and reasons
        assert all(isinstance(reason, str) for reason in reasons)

    grid = GEN.generate(17, 3)
    ragged = deepcopy(grid)
    ragged[-1].pop()
    assert GEN.self_check(ragged)
    bad_color = deepcopy(grid)
    bad_color[-1][-1] = 10
    assert GEN.self_check(bad_color)
