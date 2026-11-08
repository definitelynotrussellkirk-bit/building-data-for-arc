"""Regression tests for strict call scalars and semantic declaration scope."""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "ae0a295c2271"
ROOT = find_root(__file__)


def _generator():
    module, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    return module


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
@pytest.mark.parametrize("difficulty", ["easy", None, "hard"])
def test_generate_rejects_nonliteral_integer_seed(seed, difficulty):
    generator = _generator()
    with pytest.raises((TypeError, ValueError), match="seed"):
        generator.generate(seed, 0, difficulty=difficulty)


@pytest.mark.parametrize("sample_index", [True, False, -1])
@pytest.mark.parametrize("difficulty", ["easy", None, "hard"])
def test_generate_rejects_invalid_sample_index(sample_index, difficulty):
    generator = _generator()
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        generator.generate(991, sample_index, difficulty=difficulty)


def test_every_declared_canonical_shortcut_fits_every_labeled_canonical_pair():
    generator = _generator()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    assert generator.CANONICAL_SHORTCUTS
    failures = {
        name: [index for index, pair in enumerate(pairs) if rival(pair["input"]) != pair["output"]]
        for name, rival in generator.CANONICAL_SHORTCUTS.items()
    }
    assert failures == {name: [] for name in generator.CANONICAL_SHORTCUTS}


def test_partial_rivals_remain_lesson_competitors_not_canonical_shortcuts():
    generator = _generator()
    assert set(generator.LESSON_COMPETITORS) == set(generator.SEMANTIC_RIVALS)
    assert set(generator.CANONICAL_SHORTCUTS) == {
        "apply_rule_only_when_input_color_is_8"
    }
