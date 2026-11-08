from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "a9f315ca9cc7"
ROOT = find_root(__file__)
GEN, _SOURCE, _SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def test_scalar_override_types_reject_bool_float_and_string_before_generation():
    for bad in (True, 4.0, 9.75, "4"):
        with pytest.raises(TypeError, match="fg_color must be an integer color"):
            GEN.generate(41, 3, difficulty="hard", fg_color=bad)


def test_scene_profile_override_is_strict_and_declared():
    with pytest.raises(TypeError, match="scene_profile must be a string"):
        GEN.generate(41, 3, difficulty="hard", scene_profile=True)
    with pytest.raises(ValueError, match="scene_profile must be one of"):
        GEN.generate(41, 3, difficulty="hard", scene_profile="unknown")


def test_every_declared_canonical_shortcut_reproduces_all_canonical_pairs():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "memorize_public_masks_else_pixel_scale"
    }
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert shortcut(copy.deepcopy(pair["input"])) == pair["output"], name


def test_call_arguments_reject_non_integer_seed_and_negative_or_non_integer_index():
    for bad_seed in (True, False, 1.0, 1.75, "1"):
        with pytest.raises(TypeError, match="seed must be an integer"):
            GEN.generate(bad_seed, 0, difficulty="easy")
    for bad_index in (True, False, 1.0, 1.75, "1"):
        with pytest.raises(TypeError, match="sample_index must be an integer"):
            GEN.generate(991, bad_index, difficulty="easy")
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        GEN.generate(991, -1, difficulty="easy")


def test_retained_generalized_counterexample_refutes_declared_memorizer():
    path = (
        Path(__file__).resolve().parent.parent
        / "counterexamples"
        / "memorize-public-mask-shortcut.json"
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    grid = record["input"]
    name = record["shortcut_name"]
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid)
    assert GEN.rule_mirror(grid) == record["intended_output"]
    assert GEN.CANONICAL_SHORTCUTS[name](grid) == record["shortcut_output"]
    assert record["intended_output"] != record["shortcut_output"]
