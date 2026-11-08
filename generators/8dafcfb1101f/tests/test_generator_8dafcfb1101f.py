from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root

TASK = "8dafcfb1101f"
HERE = Path(__file__).resolve().parents[1]
SOURCE = HERE / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"generator_{TASK}", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_inputs():
    root = find_root(__file__)
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK:
            continue
        for split in ("train", "test"):
            pairs = row.get(split, [])
            if isinstance(pairs, dict):
                pairs = [pairs]
            for pair in pairs:
                yield pair["input"]


def _vector(grid):
    src = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1)
    dst = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
    return dst[0] - src[0], dst[1] - src[1]


def _sign(value):
    return -1 if value < 0 else 1


def test_rule_hash_is_pinned_and_original_inputs_remain_lawful():
    gen = _load_generator()
    assert gen.RULE_HASH == "8ab33123477f"
    original = list(_canonical_inputs())
    assert original
    assert all(gen.self_check(grid) == [] for grid in original)


def test_default_generation_is_deterministic_valid_and_covers_all_vector_quadrants():
    gen = _load_generator()
    for difficulty in (None, "medium", "hard"):
        grids = [gen.generate(20261026, i, difficulty=difficulty) for i in range(16)]
        assert grids == [gen.generate(20261026, i, difficulty=difficulty) for i in range(16)]
        assert all(gen.self_check(grid, difficulty=difficulty) == [] for grid in grids)
        signs = {(_sign(dr), _sign(dc)) for dr, dc in map(_vector, grids)}
        assert signs == {(-1, -1), (-1, 1), (1, -1), (1, 1)}


def test_first_four_samples_break_the_absolute_displacement_shortcut():
    gen = _load_generator()
    vectors = [_vector(gen.generate(17, i, difficulty="medium")) for i in range(4)]
    assert {(_sign(dr), _sign(dc)) for dr, dc in vectors} == {
        (-1, -1), (-1, 1), (1, -1), (1, 1)
    }
    assert any((dr, dc) != (abs(dr), abs(dc)) for dr, dc in vectors)


def test_blob_size_override_is_honored_and_observable():
    gen = _load_generator()
    grid = gen.generate(31337, 2, difficulty="hard", blob_size=5)
    observed = gen.observe_overrides(grid)
    assert observed["grid_h"] == len(grid)
    assert observed["grid_w"] == len(grid[0])
    assert observed["blob_size"] == 5
    counts = {}
    for row in grid:
        for value in row:
            if value not in (0, 1, 2):
                counts[value] = counts.get(value, 0) + 1
    assert counts and set(counts.values()) == {5}


def test_non_probeable_metadata_axes_are_explicitly_diagnostic():
    gen = _load_generator()
    for name in ("palette_size", "position_bias", "n_distinct_colors", "density"):
        assert gen.AXES[name].get("probe") == "diagnostic"
