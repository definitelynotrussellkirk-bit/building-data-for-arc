from __future__ import annotations

from pathlib import Path
import sys

import pytest


try:
    from reviewer_support import find_root, load_selected_generator
except ModuleNotFoundError:
    for ancestor in Path(__file__).resolve().parents:
        runtime = ancestor / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    from reviewer_support import find_root, load_selected_generator


TASK_ID = "8d2ecf358469"
gen, _, _ = load_selected_generator(TASK_ID, root=find_root(__file__))


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_public_entry_points_reject_invalid_sample_index_scalars(sample_index):
    with pytest.raises(ValueError, match="sample_index must be a nonnegative integer"):
        gen.schedule_profile(0, sample_index)
    with pytest.raises(ValueError, match="sample_index must be a nonnegative integer"):
        gen.generate(0, sample_index)


def test_zero_sample_index_remains_valid():
    assert gen.schedule_profile(0, 0) == gen.SCHEDULE_PROFILES[0]
    grid = gen.generate(0, 0)
    assert gen.self_check(grid) == []
