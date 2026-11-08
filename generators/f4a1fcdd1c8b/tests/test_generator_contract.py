from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = REPO_ROOT / "generators/f4a1fcdd1c8b/generator.py"
CANONICAL_PATH = (
    REPO_ROOT
    / "shared/data/base/solutions/banks/545aa94c7c6c/S13_E2__f4a1fcdd1c8b.json"
)


def _load_generator():
    spec = importlib.util.spec_from_file_location("review_f4a1fcdd1c8b", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_generator()


@pytest.fixture(scope="module")
def canonical_pairs():
    payload = json.loads(CANONICAL_PATH.read_text())
    samples = json.loads(payload["visible_context"]["samples_text"])
    return samples["train"]


def test_contract_metadata_is_pinned_and_probeable(gen):
    assert gen.RULE_HASH == "9a57908e9c92"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_border", "n_interior"}
    assert callable(gen.self_check)
    assert callable(gen.observe_overrides)
    assert callable(gen.strict_canonical_like)
    assert callable(gen.rule_mirror)


def test_canonical_training_pairs_pass_contract_and_python_mirror(gen, canonical_pairs):
    for pair in canonical_pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_ordinary_generation_is_deterministic_valid_and_exact(gen):
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(12):
            first = gen.generate(8128, sample_index, difficulty=difficulty)
            second = gen.generate(8128, sample_index, difficulty=difficulty)
            assert first == second
            assert gen.self_check(first, difficulty=difficulty) == []
            observed = gen.observe_overrides(first)
            assert observed["n_border"] >= 1
            assert observed["n_interior"] >= 1
            assert gen.rule_mirror(first) != first


def test_exact_override_boundaries_are_realized(gen):
    cases = (
        {"grid_h": 8, "grid_w": 9, "n_border": 1, "n_interior": 1},
        {"grid_h": 8, "grid_w": 18, "n_border": 4, "n_interior": 4},
        {"grid_h": 16, "grid_w": 9, "n_border": 4, "n_interior": 4},
        {"grid_h": 16, "grid_w": 18, "n_border": 4, "n_interior": 4},
    )
    for sample_index, expected in enumerate(cases):
        grid = gen.generate(991, sample_index, difficulty="hard", **expected)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == expected


def test_unknown_invalid_and_conflicting_overrides_fail_loudly(gen):
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(1, 0, grid_h=7)
    with pytest.raises(ValueError, match="incompatible"):
        gen.generate(1, 0, texture="all_border", n_border=2)


def test_scheduled_shared_color_scene_refutes_global_color_shortcut(gen):
    for difficulty in ("easy", "medium", "hard"):
        grid = gen.generate(404, 1, difficulty=difficulty)
        assert gen.SEMANTIC_WITNESSES["shared_color_opposite_fates"](grid)
        intended = gen.rule_mirror(grid)
        rival = gen.SEMANTIC_RIVALS["keep_border_colors_globally"](grid)
        assert rival != intended


def test_each_band_schedules_a_non_top_survivor(gen):
    for difficulty in ("easy", "medium", "hard"):
        grid = gen.generate(2026, 2, difficulty=difficulty)
        assert gen.SEMANTIC_WITNESSES["non_top_border_survivor"](grid)
        assert gen.SEMANTIC_RIVALS["top_border_only"](grid) != gen.rule_mirror(grid)


def test_self_check_rejects_missing_roles_and_malformed_cells(gen):
    no_interior = [[0] * 9 for _ in range(8)]
    no_interior[0][2] = 3
    assert any("interior" in message for message in gen.self_check(no_interior))

    malformed = [[0] * 9 for _ in range(8)]
    malformed[0][1] = 2
    malformed[4][4] = True
    errors = gen.self_check(malformed)
    assert any("integer ARC colors" in message for message in errors)


def test_exact_override_path_is_bounded_and_does_not_use_backtracking(gen, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("exact override realization must not enter combinatorial search")

    monkeypatch.setattr(gen, "_try_place_components", forbidden)
    expected = {"grid_h": 8, "grid_w": 9, "n_border": 4, "n_interior": 4}
    grid = gen.generate(77, 1, difficulty="hard", **expected)
    assert gen.observe_overrides(grid) == expected
    assert gen.self_check(grid) == []
