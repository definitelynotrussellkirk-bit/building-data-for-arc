from __future__ import annotations

import json

import pytest

from reviewer_support import find_root, load_selected_generator

TASK_ID = "250a48232c34"
ROOT = find_root(__file__)
GEN, _PATH, _SHA = load_selected_generator(TASK_ID, root=ROOT)


def test_unknown_override_typo_fails_closed_instead_of_being_silently_ignored():
    valid = GEN.generate(0, 3, difficulty="easy", n_anchors=2)
    assert GEN.self_check(valid, difficulty="easy") == []
    assert sum(1 for row in valid for value in row if 1 <= value <= 4) == 2

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 3, difficulty="easy", n_anchors=2, n_anchor=999)


def test_unknown_override_rejection_does_not_change_the_valid_draw():
    before = GEN.generate(0, 3, difficulty="easy", n_anchors=2)
    with pytest.raises(ValueError):
        GEN.generate(0, 3, difficulty="easy", n_anchors=2, n_anchor=999)
    after = GEN.generate(0, 3, difficulty="easy", n_anchors=2)
    assert json.dumps(before, separators=(",", ":")) == json.dumps(after, separators=(",", ":"))
