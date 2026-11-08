from __future__ import annotations

import copy
import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "8b320727aa72"
ROOT = find_root(__file__)
gen, _GENERATOR_SOURCE, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _lawful_single_erasure_grid() -> tuple[list[list[int]], list[list[int]]]:
    """Return a hand-built valid input and its literal consensus tile."""
    consensus = [
        [2, 7, 8, 8, 8],
        [4, 8, 8, 8, 8],
        [5, 8, 6, 8, 8],
        [8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8],
    ]
    grid = [[3 for _ in range(29)] for _ in range(29)]
    for tile_index in range(25):
        tile_r, tile_c = divmod(tile_index, 5)
        row0, col0 = tile_r * 6, tile_c * 6
        for r in range(5):
            for c in range(5):
                grid[row0 + r][col0 + c] = consensus[r][c]
    # The last tile erases one foreground cell (value 2) to background 8.
    grid[24][24] = 8
    return grid, consensus


@pytest.mark.parametrize(
    ("args", "kwargs", "message"),
    [
        ((True, 0), {}, "seed must be an integer"),
        ((1.5, 0), {}, "seed must be an integer"),
        ((1, True), {}, "sample_index must be a nonnegative integer"),
        ((1, -1), {}, "sample_index must be a nonnegative integer"),
        ((1, 0), {"difficulty": "expert"}, "difficulty must be"),
        ((1, 0), {"difficulty": 1}, "difficulty must be"),
        ((1, 0), {"corrupt_tile_index": 24.0}, "corrupt_tile_index must be an integer"),
        ((1, 0), {"anchor_position": 1}, "anchor_position must be a bool"),
        ((1, 0), {"__typo_axis__": 3}, "unknown override axes"),
        ((1, 0), {"tile_layout": "spiral"}, "tile_layout must be one of"),
        (
            (1, 0),
            {"disagreement_distribution": 7},
            "disagreement_distribution must be one of",
        ),
    ],
)
def test_generate_rejects_invalid_call_contract(args, kwargs, message):
    with pytest.raises(ValueError, match=message):
        gen.generate(*args, **kwargs)


def test_legacy_private_layout_controls_remain_accepted_for_frozen_fixture():
    grid = gen.generate(
        7,
        2,
        difficulty="hard",
        tile_layout="frame",
        disagreement_distribution="edge",
        n_filled_in_tile=12,
        n_disagreements=5,
        palette_size=5,
        background_color=9,
        separator_color=4,
        corrupt_tile_index=24,
        anchor_position=True,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "n_filled_in_tile": 12,
        "n_disagreements": 5,
        "palette_size": 5,
        "background_color": 9,
        "separator_color": 4,
        "corrupt_tile_index": 24,
        "anchor_position": True,
    }


def test_mark_and_restore_rules_have_hand_derived_outputs_without_mutation():
    grid, consensus = _lawful_single_erasure_grid()
    before = copy.deepcopy(grid)
    expected_mark = [row[:] for row in consensus]
    expected_mark[0][0] = 1

    assert gen.self_check(grid) == []
    assert gen._canonical_mark_output(grid) == expected_mark
    assert gen._restore_consensus_output(grid) == consensus
    assert grid == before


def test_semantic_witness_proves_restore_consensus_is_a_rival():
    grid, _ = _lawful_single_erasure_grid()
    expected_mark = gen._canonical_mark_output(grid)
    rival_output = gen._restore_consensus_output(grid)

    assert gen.SEMANTIC_WITNESSES["disagreement_marker_required"](grid) is True
    assert gen.WITNESS_RIVALS == {
        "disagreement_marker_required": ["restore_consensus"]
    }
    assert gen.SEMANTIC_RIVALS["restore_consensus"](grid) == rival_output
    assert rival_output != expected_mark


def test_lesson_identifiable_flags_only_a_surviving_query_changing_rival():
    grid, _ = _lawful_single_erasure_grid()
    canonical = gen._canonical_mark_output(grid)
    restored = gen._restore_consensus_output(grid)

    canonical_demos = [{"input": grid, "output": canonical}]
    query = {"input": grid, "output": canonical}
    assert gen.lesson_identifiable(canonical_demos, query) == []

    ambiguous_demos = [{"input": grid, "output": restored}]
    findings = gen.lesson_identifiable(ambiguous_demos, query)
    assert len(findings) == 1
    assert "restore_consensus fits all 1 demonstrations" in findings[0]
