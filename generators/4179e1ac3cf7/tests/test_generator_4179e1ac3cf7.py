"""Focused contract and semantics tests for generator 4179e1ac3cf7."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
GENERATOR_PATH = Path(__import__("os").environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location("generator_4179e1ac3cf7", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            cells = []
            while pending:
                current = pending.pop()
                cells.append(current)
                cr, cc = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (cr + dr, cc + dc)
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and nxt not in seen and grid[nxt[0]][nxt[1]] == color):
                        seen.add(nxt)
                        pending.append(nxt)
            result.append(cells)
    return result


def _normalize(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _mirror(shape):
    width = max(col for _, col in shape) + 1
    return tuple(sorted((row, width - 1 - col) for row, col in shape))


def _intended(grid):
    target = _normalize(_components(grid, 1)[0])
    output = [[0 for _ in row] for row in grid]
    for component in _components(grid, 3):
        shape = _normalize(component)
        if shape != target:
            continue
        left = min(col for _, col in component)
        right = max(col for _, col in component)
        for row, col in component:
            output[row][col] = 8
            output[row][left + right - col] = 8
    return output


def _canonical_pairs():
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "4179e1ac3cf7":
            return list(row["train"]) + list(row["test"])
    raise AssertionError("canonical task row not found")


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == "1cfd3e1c42af"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_realized_at_constructive_boundary(band):
    requested = {
        "grid_h": 10,
        "grid_w": 12,
        "n_matches": 3,
        "n_distractors": 2,
        "shape_size": 5,
    }
    grid = gen.generate(17, 31, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize("key,value", [
    ("unknown_axis", 1),
    ("grid_h", True),
    ("grid_w", "12"),
    ("n_matches", 0),
    ("n_matches", 4),
    ("n_distractors", -1),
    ("n_distractors", 3),
    ("shape_size", 2),
    ("shape_size", 6),
])
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("pair", _canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_canonical_inputs_are_owned_and_rule_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert _intended(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_lawful_deterministic_and_teaches_reflection(band):
    saw_mirrored_distractor = False
    seen = set()
    for index in range(96):
        grid = gen.generate(9000 + index, index * 13 + 7, difficulty=band)
        assert grid == gen.generate(9000 + index, index * 13 + 7, difficulty=band)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        assert observed["grid_h"] == len(grid)
        assert observed["grid_w"] == len(grid[0])
        template = _normalize(_components(grid, 1)[0])
        greens = [_normalize(cells) for cells in _components(grid, 3)]
        assert template != _mirror(template)
        assert greens.count(template) == observed["n_matches"]
        assert len(greens) - greens.count(template) == observed["n_distractors"]
        saw_mirrored_distractor |= _mirror(template) in greens
        seen.add(json.dumps(grid, separators=(",", ":")))
    assert saw_mirrored_distractor
    assert len(seen) >= 90


def test_declared_canonical_shortcut_really_fits_canonical_and_generated_witness_refutes_it():
    rival = gen.CANONICAL_SHORTCUTS["match_up_to_lr_reflection"]
    for pair in _canonical_pairs():
        assert rival(pair["input"]) == pair["output"]
    grid = gen.generate(71, 19, n_distractors=1)
    assert gen.SEMANTIC_WITNESSES["lr_mirror_distractor"](grid)
    assert rival(grid) != _intended(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(10)]])
def test_self_check_reports_malformed_grids_without_crashing(bad):
    assert gen.self_check(bad)

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_sample_lesson_window_contains_a_mirror_distractor(band):
    """Four sequential demos must refute reflection-insensitive matching."""
    for ordinal in range(64):
        seed = 120_000 + ordinal
        start = ordinal * 11
        observed = [
            gen.observe_overrides(gen.generate(seed, start + offset, difficulty=band))
            for offset in range(4)
        ]
        assert any(row["n_distractors"] > 0 for row in observed), (band, seed, start)


@pytest.mark.parametrize("sample_index", range(8))
def test_explicit_zero_distractor_override_beats_curriculum_schedule(sample_index):
    grid = gen.generate(991, sample_index, n_distractors=0)
    assert gen.observe_overrides(grid)["n_distractors"] == 0
