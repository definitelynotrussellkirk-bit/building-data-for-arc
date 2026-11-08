from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "0f25172eefa4"
ROOT = find_root(__file__)
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.0f25172eefa4.generator"
)


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def _canonical_record():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                record = json.loads(line)
                if record.get("task_id") == TASK_ID:
                    return record
    raise AssertionError(f"missing canonical record for {TASK_ID}")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _crop_body(grid: list[list[int]]) -> list[list[int]]:
    pts = [
        (r, c)
        for r, row in enumerate(grid[:-1])
        for c, value in enumerate(row)
        if value != 0
    ]
    top = min(r for r, _ in pts)
    left = min(c for _, c in pts)
    bottom = max(r for r, _ in pts)
    right = max(c for _, c in pts)
    return [row[left : right + 1] for row in grid[top : bottom + 1]]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _hstack_center(pieces: list[list[list[int]]], gap: int = 1) -> list[list[int]]:
    height = max(len(piece) for piece in pieces)
    widths = [len(piece[0]) for piece in pieces]
    output = [[0] * (sum(widths) + gap * (len(pieces) - 1)) for _ in range(height)]
    col = 0
    for piece in pieces:
        top = (height - len(piece)) // 2
        for r, row in enumerate(piece):
            output[top + r][col : col + len(row)] = row
        col += len(piece[0]) + gap
    return output


def _expected(grid: list[list[int]]) -> list[list[int]]:
    body = _crop_body(grid)
    pieces = []
    for code in (value for value in grid[-1] if value != 0):
        if code in (2, 5):
            piece = copy.deepcopy(body)
        elif code == 3:
            piece = _rotate_cw(body)
        elif code == 4:
            piece = _rotate_180(body)
        else:
            raise AssertionError(code)
        pieces.append(piece)
    return _hstack_center(pieces)


def _five_copies_previous(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting rival: 5 repeats the previous transform, or identity first."""
    body = _crop_body(grid)
    pieces = []
    previous = copy.deepcopy(body)
    for code in (value for value in grid[-1] if value != 0):
        if code == 2:
            piece = copy.deepcopy(body)
        elif code == 3:
            piece = _rotate_cw(body)
        elif code == 4:
            piece = _rotate_180(body)
        elif code == 5:
            piece = copy.deepcopy(previous) if pieces else copy.deepcopy(body)
        else:
            raise AssertionError(code)
        pieces.append(piece)
        previous = piece
    return _hstack_center(pieces)


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _blank_grid(h: int = 5, w: int = 7) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def test_metadata_authority_hash_and_description_are_pinned():
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "2.2.0"
    assert GEN.RULE_HASH == "44e21d5003cc"
    record = _canonical_record()
    assert _normalized_hash(record["program_solution"]) == GEN.RULE_HASH
    description = record["written_solution"].lower()
    assert "2" in description and "5" in description
    assert "identity" in description
    assert "horizontal flip" not in description


def test_all_canonical_pairs_are_accepted_and_exact():
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert _expected(pair["input"]) == pair["output"]


def test_generated_distribution_has_all_semantic_branches():
    shapes = set()
    sequences = set()
    dimensions = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            grid = GEN.generate(seed, seed % 7, difficulty=band)
            assert GEN.self_check(grid, difficulty=band) == []
            obs = GEN.semantic_observables(grid)
            assert obs["key_count"] == 4
            assert obs["has_identity"]
            assert obs["has_clockwise"]
            assert obs["has_180"]
            assert obs["transform_class_count"] == 3
            assert obs["output_wider_than_input"]
            assert _expected(grid)
            shapes.add(obs["body_shape"])
            sequences.add(obs["key_sequence"])
            dimensions.add((obs["grid_h"], obs["grid_w"]))
    assert shapes == set(GEN._SHAPES)
    assert sequences == set(GEN._SEQUENCE_SCHEDULE)
    assert len(dimensions) >= 8


def test_canonical_fitting_code5_position_shortcut_is_refuted_by_every_demo_window():
    pairs = _pairs()
    assert all(_five_copies_previous(pair["input"]) == pair["output"] for pair in pairs)

    period = len(GEN._SEQUENCE_SCHEDULE)
    for band in ("easy", "medium", "hard"):
        for start in range(period):
            demos = [
                GEN.generate(1701, start + offset, difficulty=band)
                for offset in range(3)
            ]
            assert any(_five_copies_previous(grid) != _expected(grid) for grid in demos)


def test_code5_position_shortcut_is_refuted_after_any_query_rotation():
    period = len(GEN._SEQUENCE_SCHEDULE)
    for band in ("easy", "medium", "hard"):
        for start in range(period):
            block = [
                GEN.generate(1801, start + offset, difficulty=band)
                for offset in range(4)
            ]
            for held_out in range(4):
                demos = [grid for index, grid in enumerate(block) if index != held_out]
                assert any(
                    _five_copies_previous(grid) != _expected(grid) for grid in demos
                )


def test_every_four_default_indices_include_a_canonical_profile_anchor():
    profiles = {_profile(pair["input"]) for pair in _pairs()}
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            block = [
                GEN.generate(1901, start + offset, difficulty=band)
                for offset in range(4)
            ]
            assert any(_profile(grid) in profiles for grid in block)


@pytest.mark.parametrize("grid_h", [5, 8])
@pytest.mark.parametrize("grid_w", [7, 10])
@pytest.mark.parametrize("body_color", [1, 9])
@pytest.mark.parametrize("body_shape", list(GEN._SHAPES))
@pytest.mark.parametrize("key_sequence", list(GEN._KEY_SEQUENCES))
def test_full_boundary_override_product_is_exact(
    grid_h, grid_w, body_color, body_shape, key_sequence
):
    overrides = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "body_color": body_color,
        "body_shape": body_shape,
        "key_sequence": key_sequence,
    }
    grid = GEN.generate(1201, 73, difficulty="hard", **overrides)
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.self_check(grid) == []


def test_unknown_override_fails_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, texture="warm")


def test_determinism_fresh_returns_and_process_global_rng_isolation():
    state = random.getstate()
    first = GEN.generate(444, 19, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(444, 19, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(444, 19, difficulty="medium") == second


def test_every_declared_shape_distinguishes_all_executable_classes():
    for cells in GEN._SHAPES.values():
        assert GEN._transform_class_count(GEN._tight_mask(cells)) == 3


def test_self_check_rejects_targeted_semantic_impostors():
    no_body = _blank_grid()
    no_body[-1][0:4] = [2, 3, 4, 2]
    assert any("no nonzero source" in error for error in GEN.self_check(no_body))

    two_colors = GEN.generate(10, 0)
    r, c = GEN._body_cells(two_colors)[0]
    two_colors[r][c] = 9 if two_colors[r][c] != 9 else 8
    assert any("exactly one color" in error for error in GEN.self_check(two_colors))

    disconnected = GEN.generate(11, 0)
    body = GEN._body_cells(disconnected)
    r, c = body[0]
    disconnected[r][c] = 0
    disconnected[0][len(disconnected[0]) - 1] = next(
        disconnected[rr][cc] for rr, cc in GEN._body_cells(disconnected)
    )
    assert any("4-connected" in error for error in GEN.self_check(disconnected))

    symmetric = _blank_grid()
    for r in (0, 1):
        for c in (0, 1):
            symmetric[r][c] = 6
    symmetric[-1][0:4] = [2, 3, 4, 2]
    assert any("distinguish identity" in error for error in GEN.self_check(symmetric))

    invalid_code = GEN.generate(12, 0)
    key_col = next(c for c, value in enumerate(invalid_code[-1]) if value != 0)
    invalid_code[-1][key_col] = 8
    assert any("invalid transform-code" in error for error in GEN.self_check(invalid_code))

    two_keys = GEN.generate(13, 0)
    key_cols = [c for c, value in enumerate(two_keys[-1]) if value != 0]
    two_keys[-1][key_cols[2]] = 0
    two_keys[-1][key_cols[3]] = 0
    assert any("3..4" in error for error in GEN.self_check(two_keys))

    one_class = GEN.generate(14, 0)
    for c, value in enumerate(one_class[-1]):
        if value != 0:
            one_class[-1][c] = 2
    assert any("at least two transform classes" in error for error in GEN.self_check(one_class))


def test_every_declared_lesson_competitor_is_refuted_by_each_demo_window():
    required = {
        "code_2_is_clockwise",
        "code_3_is_identity",
        "code_4_is_identity",
        "five_is_hflip",
        "five_copies_previous_transform",
        "merge_adjacent_duplicates",
        "no_separator_column",
    }
    assert required <= set(GEN.LESSON_COMPETITORS)
    assert set(GEN.CANONICAL_SHORTCUTS) == {"five_copies_previous_transform"}

    period = len(GEN._SEQUENCE_SCHEDULE)
    for band in ("easy", "medium", "hard"):
        for start in range(period):
            demos = [
                GEN.generate(2001, start + offset, difficulty=band)
                for offset in range(3)
            ]
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(
                    rival(grid) != _expected(grid) for grid in demos
                ), (band, start, name)
