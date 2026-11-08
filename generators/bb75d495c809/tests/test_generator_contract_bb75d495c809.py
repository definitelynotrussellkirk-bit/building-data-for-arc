from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator

TASK_ID = "bb75d495c809"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def test_generate_rejects_unknown_difficulty_and_override_before_sampling():
    """A typo must not silently produce plausible data under another distribution."""
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="extreme")
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 0, bogus=1)
