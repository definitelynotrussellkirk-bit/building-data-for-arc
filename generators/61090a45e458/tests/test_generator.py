"""Focused regression suite for the frame-seed recolor generator."""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "61090a45e458"
HOME = Path(__file__).resolve().parents[1]
GEN_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GEN_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
ROOT = find_root(__file__)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _color_components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append((color, cells))
    return components


def _frame_boxes(grid):
    frames = []
    for color, cells in _color_components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
        height, width = r2 - r1 + 1, c2 - c1 + 1
        border = 2 * height + 2 * width - 4
        if (
            height >= 3
            and width >= 3
            and len(cells) == border
            and all(r in (r1, r2) or c in (c1, c2) for r, c in cells)
        ):
            frames.append((r1, c1, r2, c2, color))
    return sorted(frames)


def intended_output(grid):
    """Independent mirror of the selected Racket authority on lawful inputs."""
    out = deepcopy(grid)
    for r1, c1, r2, c2, _ in _frame_boxes(grid):
        by_color = {}
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                value = grid[r][c]
                if value:
                    by_color.setdefault(value, []).append((r, c))
        seeds = [color for color, cells in by_color.items() if len(cells) == 1]
        assert len(seeds) == 1
        seed = seeds[0]
        for color, cells in by_color.items():
            if color != seed:
                for r, c in cells:
                    out[r][c] = seed
    return out


def _profile(grid):
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def _pinned_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_rule_pin_and_declared_exact_axes():
    assert GEN.RULE_HASH == "1041403d0f0a"
    assert GEN.VERSION == "2.0.0"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {"n_frames", "target_size"}


@pytest.mark.parametrize("pair", CANONICAL)
def test_accepts_and_solves_every_canonical_pair(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("n_frames", [1, 2, 3])
@pytest.mark.parametrize("target_size", [2, 5])
def test_exact_overrides_are_constructive_and_observable(
    band, n_frames, target_size
):
    grid = GEN.generate(
        83,
        17,
        difficulty=band,
        n_frames=n_frames,
        target_size=target_size,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "n_frames": n_frames,
        "target_size": target_size,
    }
    assert intended_output(grid) != grid


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("n_frames", 0),
        ("n_frames", 4),
        ("target_size", 1),
        ("target_size", 6),
        ("n_frames", True),
        ("target_size", 2.5),
        ("target_size", "3"),
    ],
)
def test_rejects_unknown_or_invalid_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{key: value})


def test_top_left_target_shortcut_fits_canonical_but_generated_schedule_refutes_it():
    rival = GEN.CANONICAL_SHORTCUTS["top_left_target_only"]
    assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL)

    for start in (0, 11, 22, 33):
        lesson = [GEN.generate(700 + start, start + offset) for offset in range(3)]
        labels = [intended_output(grid) for grid in lesson]
        firings = [GEN.SEMANTIC_WITNESSES["target_not_top_left"](grid) for grid in lesson]
        assert sum(firings) >= 2
        for grid, fires in zip(lesson, firings):
            assert GEN.self_check(grid) == []
            if fires:
                assert rival(grid) != intended_output(grid)
        for query_index in range(3):
            demos = [
                {"input": lesson[i], "output": labels[i]}
                for i in range(3)
                if i != query_index
            ]
            query = {
                "input": lesson[query_index],
                "output": labels[query_index],
            }
            assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_pinned_profile_floor_has_an_exact_hit_in_every_band(band):
    canonical_profiles = {_profile(pair["input"]) for pair in CANONICAL}
    generated = []
    for index in range(20):
        seed = _pinned_seed(band, index)
        generated.append(
            GEN.generate(seed, seed % 7919 + index, difficulty=band)
        )
    assert any(_profile(grid) in canonical_profiles for grid in generated)


def test_difficulty_bands_change_default_target_complexity():
    """The advertised difficulty knob must affect generation, not be inert."""
    for seed in range(1, 13):
        sample_index = seed * 7
        easy = GEN.generate(seed, sample_index, difficulty="easy")
        hard = GEN.generate(seed, sample_index, difficulty="hard")
        assert easy != hard
        assert GEN.observe_overrides(easy)["target_size"] in {2, 3}
        assert GEN.observe_overrides(hard)["target_size"] in {4, 5}


def test_default_distribution_covers_frame_counts_sizes_and_both_layouts():
    counts = set()
    sizes = set()
    layouts = set()
    shapes = set()
    for index in range(180):
        grid = GEN.generate(9000 + index, index)
        assert grid == GEN.generate(9000 + index, index)
        assert GEN.self_check(grid) == []
        observed = GEN.observe_overrides(grid)
        counts.add(observed["n_frames"])
        sizes.add(observed["target_size"])
        boxes = _frame_boxes(grid)
        if len(boxes) > 1:
            rows = [(r1, r2) for r1, _, r2, _, _ in boxes]
            cols = [(c1, c2) for _, c1, _, c2, _ in boxes]
            horizontal = all(cols[i][1] < cols[i + 1][0] for i in range(len(cols) - 1))
            vertical = all(rows[i][1] < rows[i + 1][0] for i in range(len(rows) - 1))
            if horizontal:
                layouts.add("horizontal")
            if vertical:
                layouts.add("vertical")
        shapes.add((len(grid), len(grid[0])))
    assert counts == {1, 2, 3}
    assert sizes == {2, 3, 4, 5}
    assert layouts == {"horizontal", "vertical"}
    assert len(shapes) >= 8


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 5 for _ in range(5)]])
def test_malformed_inputs_return_diagnostics(bad):
    assert GEN.self_check(bad)


def test_validator_rejects_stray_nonzero_cell():
    grid = GEN.generate(18, 1, n_frames=2, target_size=4)
    changed = deepcopy(grid)
    assert changed[0][0] == 0
    changed[0][0] = 9
    assert GEN.self_check(changed)
