from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root

TASK = "d78409c82698"
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


def _has_diagonal_singleton_pair(gen, grid):
    singletons = [comp[0] for comp in gen._red_components(grid) if len(comp) == 1]
    return any(
        abs(r1 - r2) == 1 and abs(c1 - c2) == 1
        for i, (r1, c1) in enumerate(singletons)
        for r2, c2 in singletons[i + 1 :]
    )


def test_rule_hash_is_pinned_and_all_original_inputs_are_accepted():
    gen = _load_generator()
    assert gen.RULE_HASH == "f38a8db401a2"
    original = list(_canonical_inputs())
    assert original
    assert all(gen.self_check(grid) == [] for grid in original)


def test_generated_scenes_still_force_diagonal_vs_cardinal_evidence():
    gen = _load_generator()
    for difficulty in (None, "medium", "hard"):
        for sample_index in range(20):
            first = gen.generate(9107, sample_index, difficulty=difficulty)
            second = gen.generate(9107, sample_index, difficulty=difficulty)
            assert first == second
            assert gen.self_check(first, difficulty=difficulty) == []
            assert _has_diagonal_singleton_pair(gen, first)
            components = gen._red_components(first)
            assert any(len(comp) > 1 for comp in components)
            assert sum(len(comp) == 1 for comp in components) >= (6 if difficulty == "hard" else 2 if difficulty == "easy" else 3)


def test_singleton_override_is_honored_and_observable():
    gen = _load_generator()
    grid = gen.generate(31337, 2, difficulty="hard", n_singletons=8)
    observed = gen.observe_overrides(grid)
    assert observed == {"grid_h": len(grid), "grid_w": len(grid[0]), "n_singletons": 8}


def test_non_probeable_metadata_axes_are_explicitly_diagnostic():
    gen = _load_generator()
    for name in ("palette_size", "position_bias", "n_distinct_colors", "density"):
        assert gen.AXES[name].get("probe") == "diagnostic"
