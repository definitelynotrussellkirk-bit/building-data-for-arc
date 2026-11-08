from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "9a94379ed070"
ROOT = find_root(__file__)
GEN, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def test_rule_hash_and_all_canonical_pairs_are_owned() -> None:
    assert GEN.RULE_HASH == "ae44c1c82119"
    pairs = _canonical_pairs()
    assert len(pairs) == 8
    for pair in pairs:
        assert GEN.self_check(copy.deepcopy(pair["input"])) == []
        assert GEN.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_generated_instances_are_deterministic_fresh_and_rng_pure() -> None:
    random.seed(918273)
    before = random.getstate()
    first = GEN.generate(41, 17, difficulty="hard")
    after = random.getstate()
    replay = GEN.generate(41, 17, difficulty="hard")
    assert before == after
    assert first == replay
    assert first is not replay
    assert all(left is not right for left, right in zip(first, replay))
    assert GEN.self_check(first) == []
    assert GEN.rule_mirror(first) == GEN.rule_mirror(replay)


@pytest.mark.parametrize(
    "override,expected",
    [
        ({"tile_size": 3}, ("tile_size", 3)),
        ({"tile_size": 5}, ("tile_size", 5)),
        ({"tile_color": 1}, ("tile_color", 1)),
        ({"tile_color": 9}, ("tile_color", 9)),
        ({"stripe_orientation": "row"}, ("stripe_orientation", "row")),
        ({"stripe_orientation": "column"}, ("stripe_orientation", "column")),
        ({"stripe_index": 0}, ("stripe_index", 0)),
        ({"stripe_index": 4}, ("stripe_index", 4)),
        ({"texture": "sparse"}, ("texture", "sparse")),
        ({"texture": "irregular"}, ("texture", "irregular")),
        ({"texture": "dense"}, ("texture", "dense")),
    ],
)
def test_boundary_overrides_are_exact(override, expected) -> None:
    axis, value = expected
    for band in ("easy", "medium", "hard"):
        grid = GEN.generate(71, 23, difficulty=band, **override)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid)[axis] == value


def test_incompatible_and_unknown_overrides_fail_loudly() -> None:
    with pytest.raises(ValueError, match="stripe_index"):
        GEN.generate(1, 1, tile_size=3, stripe_index=4)
    with pytest.raises(ValueError, match="tile_color"):
        GEN.generate(1, 1, tile_color=3)
    with pytest.raises(TypeError, match="unknown"):
        GEN.generate(1, 1, not_an_axis=7)


def _base_grid():
    return GEN.generate(
        193,
        29,
        difficulty="medium",
        tile_size=4,
        tile_color=6,
        stripe_orientation="column",
        stripe_index=1,
        texture="irregular",
    )


def test_self_check_rejects_marker_copy_and_separator_impostors() -> None:
    base = _base_grid()
    facts = GEN.semantic_observables(base)
    q = facts["tile_size"]
    color = facts["tile_color"]

    no_marker = [[0 if value == 3 else value for value in row] for row in base]

    broken_marker = copy.deepcopy(base)
    marker_cell = next(
        (row, col)
        for row in range(len(base))
        for col in range(len(base))
        if base[row][col] == 3
    )
    broken_marker[marker_cell[0]][marker_cell[1]] = 0

    broken_copy = copy.deepcopy(base)
    clean = [[0 if value == 3 else value for value in row] for row in base]
    changed = False
    for block_row in range(q):
        for block_col in range(q):
            row0 = block_row * (q + 1)
            col0 = block_col * (q + 1)
            for tile_row in range(q):
                for tile_col in range(q):
                    row, col = row0 + tile_row, col0 + tile_col
                    if clean[row][col] == color:
                        broken_copy[row][col] = 0
                        changed = True
                        break
                if changed:
                    break
            if changed:
                break
        if changed:
            break
    assert changed

    separator_corruption = copy.deepcopy(base)
    separator_corruption[q][q] = color

    for malformed in (no_marker, broken_marker, broken_copy, separator_corruption):
        assert GEN.self_check(malformed), "malformed recombination was accepted"


def test_negative_recombination_with_two_different_visible_tiles_is_rejected() -> None:
    grid = _base_grid()
    facts = GEN.semantic_observables(grid)
    q = facts["tile_size"]
    color = facts["tile_color"]
    clean = [[0 if value == 3 else value for value in row] for row in grid]
    visible = []
    for br in range(q):
        for bc in range(q):
            r0, c0 = br * (q + 1), bc * (q + 1)
            if any(clean[r0 + r][c0 + c] for r in range(q) for c in range(q)):
                visible.append((br, bc))
    assert len(visible) >= 2

    malformed = copy.deepcopy(grid)
    br, bc = visible[-1]
    r0, c0 = br * (q + 1), bc * (q + 1)
    target = next(
        (r, c)
        for r in range(q)
        for c in range(q)
        if clean[r0 + r][c0 + c] == 0
    )
    malformed[r0 + target[0]][c0 + target[1]] = color
    assert GEN.self_check(malformed)
