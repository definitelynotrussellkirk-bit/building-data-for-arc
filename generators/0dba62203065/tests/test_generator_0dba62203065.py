from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_0dba62203065", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        1 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(sorted(cells))
    return sorted(result, key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells)))


def _canonical_fixture() -> list[list[int]]:
    grid = [[0] * 10 for _ in range(8)]
    grid[0] = [2, 3, 4, 5, 6, 7, 8, 2, 3, 4]
    for r, c in ((2, 0), (3, 0), (3, 1), (3, 4), (3, 5), (4, 4), (5, 7), (6, 7)):
        grid[r][c] = 1
    return grid


def test_rule_identity_and_full_header_summary() -> None:
    assert GEN.RULE_HASH == "75437b07b887"
    assert "full" in GEN.SUMMARY.lower()
    assert "cyclic" in GEN.SUMMARY.lower()


def test_canonical_profile_schedule_and_generated_grammar() -> None:
    profiles = ((8, 10), (9, 11), (10, 12))
    saw_origin = set()
    for difficulty in ("easy", "medium", "hard"):
        for sample_index, expected_shape in enumerate(profiles):
            grid = GEN.generate(100 + sample_index, sample_index, difficulty=difficulty)
            assert (len(grid), len(grid[0])) == expected_shape
            assert GEN.self_check(grid) == []
            assert set(grid[0]) == set(range(2, 9))
            assert all(row[-1] == 0 for row in grid[1:])
            components = _components(grid)
            assert len(components) == 3
            saw_origin.add(min(r for cells in components for r, _ in cells))
            assert any(
                min(c for _, c in cells) != min(c for r, c in cells if r == min(rr for rr, _ in cells))
                for cells in components
            )
    assert saw_origin == {1, 2}


def test_exact_overrides_are_observable_and_unknown_keys_fail() -> None:
    requested = {
        "grid_h": 12,
        "grid_w": 13,
        "header_start": 8,
        "header_direction": "descending",
        "body_origin": 1,
        "blob_profile": "extended",
    }
    grid = GEN.generate(17, 9, difficulty="hard", **requested)
    assert GEN.observe_overrides(grid) == requested
    assert GEN.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(17, 9, typo_axis=3)


def test_self_check_rejects_structural_impostors() -> None:
    valid = _canonical_fixture()
    assert GEN.self_check(valid) == []

    flat_header = [row[:] for row in valid]
    flat_header[0] = [2] * len(flat_header[0])
    assert GEN.self_check(flat_header)

    illegal_body_color = [row[:] for row in valid]
    illegal_body_color[7][3] = 4
    assert GEN.self_check(illegal_body_color)

    last_column_body = [row[:] for row in valid]
    last_column_body[6][9] = 1
    last_column_body[7][9] = 1
    assert GEN.self_check(last_column_body)

    missing_blob = [row[:] for row in valid]
    missing_blob[5][7] = 0
    missing_blob[6][7] = 0
    assert GEN.self_check(missing_blob)


def test_rule_mirror_uses_each_objects_leftmost_column() -> None:
    grid = _canonical_fixture()
    output = GEN.rule_mirror(grid)
    assert output[0] == grid[0]
    for cells in _components(grid):
        left = min(c for _, c in cells)
        assert {output[r][c] for r, c in cells} == {grid[0][left]}
    assert grid[2][0] == 1  # mirror must not mutate input


def test_semantic_witnesses_have_real_rival_counterexamples() -> None:
    expected = {
        "topmost_cell_not_leftmost",
        "multi_column_object",
        "row_one_body",
    }
    assert set(GEN.SEMANTIC_WITNESSES) == expected
    assert set(GEN.WITNESS_RIVALS) == expected

    firings = {name: 0 for name in expected}
    for sample_index in range(12):
        grid = GEN.generate(900 + sample_index, sample_index, difficulty=("easy", "medium", "hard")[sample_index % 3])
        truth = GEN.rule_mirror(grid)
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            firings[name] += 1
            rivals = GEN.WITNESS_RIVALS[name]
            assert any(GEN.SEMANTIC_RIVALS[rival](grid) != truth for rival in rivals)
    assert all(count > 0 for count in firings.values())


def test_two_demo_window_refutes_all_declared_competitors() -> None:
    for start in range(8):
        demos = []
        for sample_index in (start, start + 1):
            grid = GEN.generate(1200 + start, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(1200 + start, start + 2, difficulty="medium")
        query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
        assert GEN.lesson_identifiable(demos, query) == []


def test_difficulty_bands_are_not_a_dead_control() -> None:
    for seed in range(5):
        for sample_index in range(4):
            easy = GEN.generate(seed, sample_index, difficulty="easy")
            medium = GEN.generate(seed, sample_index, difficulty="medium")
            hard = GEN.generate(seed, sample_index, difficulty="hard")
            assert GEN.self_check(easy) == []
            assert GEN.self_check(medium) == []
            assert GEN.self_check(hard) == []
            assert easy != hard
