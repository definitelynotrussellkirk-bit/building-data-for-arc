from __future__ import annotations

from collections import deque
import importlib
import json
import importlib.util

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "97b3f59b5cc4"
ROOT = find_root(__file__)
LOCAL_SOURCE = ROOT / "generators" / TASK / "generator.py"
if LOCAL_SOURCE.is_file():
    SPEC = importlib.util.spec_from_file_location("generator_97b3f59b5cc4", LOCAL_SOURCE)
    assert SPEC and SPEC.loader
    generator = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(generator)
else:
    generator = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK}.generator"
    )

CANONICAL = canonical_pairs(TASK, root=ROOT)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def components(grid):
    """Independent same-color four-component oracle."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for row0 in range(h):
        for col0 in range(w):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            todo = deque([(row0, col0)])
            seen.add((row0, col0))
            cells = set()
            while todo:
                row, col = todo.popleft()
                cells.add((row, col))
                for dr, dc in CARDINAL:
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            border = any(
                row in (0, h - 1) or col in (0, w - 1)
                for row, col in cells
            )
            result.append((color, cells, border))
    return result


def observed_counts(grid):
    objects = components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_border": sum(border for _, _, border in objects),
        "n_interior": sum(not border for _, _, border in objects),
    }


def shared_color_opposite_fates(grid):
    objects = components(grid)
    border = {color for color, _, touches in objects if touches}
    interior = {color for color, _, touches in objects if not touches}
    return bool(border & interior)


def test_contract_metadata_is_pinned_and_probeable():
    assert generator.RULE_HASH == "e3401b50999e"
    assert set(generator.AXES) == {"grid_h", "grid_w", "n_border", "n_interior"}
    assert generator.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert callable(generator.observe_overrides)
    assert callable(generator.strict_canonical_like)
    assert callable(generator.rule_mirror)


def test_all_canonical_pairs_are_valid_and_match_component_rule():
    assert CANONICAL
    for pair in CANONICAL:
        assert generator.self_check(pair["input"]) == []
        assert generator.strict_canonical_like(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]


def test_canonical_profiles_are_scheduled_in_every_band():
    expected = [(5, 7), (6, 7), (6, 8)]
    for difficulty in ("easy", "medium", "hard"):
        observed = [
            (len(generator.generate(17, index, difficulty=difficulty)),
             len(generator.generate(17, index, difficulty=difficulty)[0]))
            for index in range(3)
        ]
        assert observed == expected


def test_ordinary_generation_is_deterministic_valid_and_nontrivial():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(12):
            first = generator.generate(8128, sample_index, difficulty=difficulty)
            second = generator.generate(8128, sample_index, difficulty=difficulty)
            assert first == second
            assert generator.self_check(first, difficulty=difficulty) == []
            facts = observed_counts(first)
            assert facts["n_border"] >= 1
            assert facts["n_interior"] >= 1
            assert generator.observe_overrides(first) == facts
            assert generator.rule_mirror(first) != first


def test_every_contiguous_three_profile_window_refutes_global_color_shortcut():
    for difficulty in ("easy", "medium", "hard"):
        lessons = [generator.generate(404, index, difficulty=difficulty) for index in range(8)]
        for start in range(4):
            window = lessons[start : start + 3]
            assert any(shared_color_opposite_fates(grid) for grid in window)
            assert any(
                generator.SEMANTIC_RIVALS["keep_border_colors_globally"](grid)
                != generator.rule_mirror(grid)
                for grid in window
            )


def test_scheduled_border_object_propagates_beyond_literal_edge_cells():
    for difficulty in ("easy", "medium", "hard"):
        grid = generator.generate(2026, 0, difficulty=difficulty)
        h, w = len(grid), len(grid[0])
        assert any(
            touches
            and any(0 < row < h - 1 and 0 < col < w - 1 for row, col in cells)
            for _, cells, touches in components(grid)
        )
        assert (
            generator.SEMANTIC_RIVALS["edge_cells_only"](grid)
            != generator.rule_mirror(grid)
        )


def test_exact_override_boundaries_are_realized():
    cases = (
        {"grid_h": 5, "grid_w": 7, "n_border": 1, "n_interior": 1},
        {"grid_h": 5, "grid_w": 14, "n_border": 4, "n_interior": 4},
        {"grid_h": 12, "grid_w": 7, "n_border": 4, "n_interior": 4},
        {"grid_h": 12, "grid_w": 14, "n_border": 4, "n_interior": 4},
    )
    for sample_index, expected in enumerate(cases):
        grid = generator.generate(991, sample_index, difficulty="hard", **expected)
        assert generator.self_check(grid) == []
        assert observed_counts(grid) == expected
        assert generator.observe_overrides(grid) == expected


def test_unknown_invalid_and_conflicting_overrides_fail_loudly():
    with pytest.raises(ValueError, match="seed must be an integer"):
        generator.generate(True, 0)
    for bad_index in (True, False, 1.0, "1", -1):
        with pytest.raises(ValueError, match="sample_index must be a nonnegative integer"):
            generator.generate(1, bad_index)
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="outside"):
        generator.generate(1, 0, grid_h=4)
    for bad in (
        {"grid_h": "5"},
        {"grid_w": True},
        {"n_border": 2.0},
        {"n_interior": "1"},
    ):
        with pytest.raises(ValueError, match="must be an integer"):
            generator.generate(1, 0, **bad)
    with pytest.raises(ValueError, match="incompatible"):
        generator.generate(1, 0, texture="all_border", n_border=2)


def test_self_check_rejects_missing_roles_and_malformed_cells():
    no_interior = [[0] * 7 for _ in range(5)]
    no_interior[0][2] = 3
    assert any("interior" in message for message in generator.self_check(no_interior))

    malformed = [[0] * 7 for _ in range(5)]
    malformed[0][1] = 2
    malformed[3][3] = True
    assert any("integer ARC colors" in message for message in generator.self_check(malformed))


def test_exact_override_path_is_bounded_and_skips_backtracking(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("exact override realization entered combinatorial search")

    monkeypatch.setattr(generator, "_try_place_components", forbidden)
    expected = {"grid_h": 5, "grid_w": 7, "n_border": 4, "n_interior": 4}
    grid = generator.generate(77, 1, difficulty="hard", **expected)
    assert observed_counts(grid) == expected
    assert generator.self_check(grid) == []


def test_retained_shared_color_counterexample_matches_authority_and_refutes_rival():
    path = ROOT / "generators" / TASK / "counterexamples" / "shared-color-opposite-fates.json"
    row = json.loads(path.read_text(encoding="utf-8"))
    grid = row["input"]
    assert row["generator_sha256"] == __import__("hashlib").sha256(LOCAL_SOURCE.read_bytes()).hexdigest()
    assert row["rule_hash"] == generator.RULE_HASH
    assert generator.self_check(grid, difficulty=row["origin"]["difficulty"]) == []
    assert generator.observe_overrides(grid) == row["observed_axes"]
    assert generator.rule_mirror(grid) == row["intended_output"]
    rival = generator.SEMANTIC_RIVALS[row["rival"]["name"]](grid)
    assert rival == row["rival"]["output"]
    assert rival != row["intended_output"]
    assert row["differing_cells"]
