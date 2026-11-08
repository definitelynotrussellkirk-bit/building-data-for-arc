"""Request validation and lesson-level shortcut regressions."""
from collections import Counter

import pytest
from reviewer_support import find_root, load_selected_generator

GEN, _, _ = load_selected_generator("a5bda33d14a0", root=find_root(__file__))


def border_rule(grid):
    out = [list(row) for row in grid]
    points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    rows, cols = [r for r, c in points], [c for r, c in points]
    for r in range(min(rows), max(rows) + 1):
        for c in range(min(cols), max(cols) + 1):
            if (r in (min(rows), max(rows)) or c in (min(cols), max(cols))) and not grid[r][c]:
                out[r][c] = 8
    return out


@pytest.mark.parametrize("axis,value", [
    ("seed", True), ("seed", False), ("seed", 1.0), ("seed", 1.75), ("seed", "1"),
    ("sample_index", True), ("sample_index", False), ("sample_index", 1.0),
    ("sample_index", "1"), ("sample_index", -1),
    ("difficulty", True), ("difficulty", False), ("difficulty", 0),
    ("difficulty", 1.0), ("difficulty", 0.25), ("difficulty", 0.75),
    ("difficulty", "__invalid_difficulty__"),
])
def test_call_arguments_reject_invalid_scalars(axis, value):
    kwargs = {"seed": 991, "sample_index": 0, "difficulty": "easy"}
    kwargs[axis] = value
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**kwargs)


def test_sparse_teaching_pairs_distinguish_canvas_border():
    for seed in range(64):
        for index in range(4):
            if GEN.schedule_profile(seed, index) != "sparse":
                continue
            grid = GEN.generate(seed, index)
            assert GEN.LESSON_COMPETITORS["canvas_border"](grid) != border_rule(grid), (seed, index)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_four_pair_windows_and_every_query_holdout(band):
    for seed in range(8):
        grids = [GEN.generate(seed, index, difficulty=band) for index in range(11)]
        truths = [border_rule(grid) for grid in grids]
        predictions = {name: [rival(grid) for grid in grids]
                       for name, rival in GEN.LESSON_COMPETITORS.items()}
        for start in range(8):
            profiles = Counter(GEN.schedule_profile(seed, index, band)
                               for index in range(start, start + 4))
            assert profiles == {"sparse": 2, "distributed": 2}
            for query in range(start, start + 4):
                demonstrations = [i for i in range(start, start + 4) if i != query]
                for name, outputs in predictions.items():
                    fits = all(outputs[i] == truths[i] for i in demonstrations)
                    assert not fits or outputs[query] == truths[query], (seed, start, query, name)
