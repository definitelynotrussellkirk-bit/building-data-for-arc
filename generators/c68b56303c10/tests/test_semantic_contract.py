"""Finite rival and joint-control regressions for bbox-overlap lessons."""

from itertools import product

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "c68b56303c10"


@pytest.fixture(scope="module")
def generator():
    return load_selected_generator(TASK_ID, root=find_root(__file__))[0]


def _label(grid):
    bounds = []
    for color in (2, 3):
        points = [(r, c) for r, row in enumerate(grid)
                  for c, value in enumerate(row) if value == color]
        rows, cols = zip(*points)
        bounds.append((min(rows), min(cols), max(rows), max(cols)))
    red, green = bounds
    height = min(red[2], green[2]) - max(red[0], green[0]) + 1
    width = min(red[3], green[3]) - max(red[1], green[1]) + 1
    assert height > 0 and width > 0
    return [[8] * width for _ in range(height)]


def test_declared_shortcuts_fit_all_canonical_pairs(generator):
    rivals = getattr(generator, "CANONICAL_SHORTCUTS", {})
    assert len(rivals) >= 4, "The four observed canonical coincidences need executable rivals"
    for pair in canonical_pairs(TASK_ID, root=find_root(__file__)):
        for name, rival in rivals.items():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
@pytest.mark.parametrize("seed", (0, 17, 10007))
def test_every_short_window_and_query_rotation_refutes_declared_rivals(generator, difficulty, seed):
    rivals = getattr(generator, "LESSON_COMPETITORS", {})
    assert rivals, "A lesson contract must name its finite alternatives"
    pairs = []
    for index in range(12):
        grid = generator.generate(seed, index, difficulty=difficulty)
        pairs.append({"input": grid, "output": _label(grid)})
    for start in range(8):
        lesson = pairs[start:start + 4]
        for query_index in range(4):
            query = lesson[query_index]
            demos = [pair for i, pair in enumerate(lesson) if i != query_index]
            assert generator.lesson_identifiable(demos, query) == [], (seed, difficulty, start, query_index)
            for name, rival in rivals.items():
                if all(rival(pair["input"]) == pair["output"] for pair in demos):
                    assert rival(query["input"]) == query["output"], (seed, difficulty, start, query_index, name)


def test_minimal_wide_overlap_distinguishes_canonical_shortcuts(generator):
    rows = ["0000000000", "0200002000", "0000000000", "0003000000",
            "0020000300", "0000000000", "0003000000", "0000000000"]
    grid = [[int(value) for value in row] for row in rows]
    expected = [[8] * 4 for _ in range(2)]
    assert _label(grid) == expected
    assert generator.self_check(grid) == []
    rivals = getattr(generator, "CANONICAL_SHORTCUTS", {})
    assert rivals, "Missing executable shortcut contract"
    disagreements = [name for name, rival in rivals.items() if rival(grid) != expected]
    assert len(disagreements) >= 3, disagreements


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_joint_axis_endpoints_are_observable_and_lawful(generator, difficulty):
    observer = getattr(generator, "observe_overrides", None)
    assert callable(observer), "Exact controls must be measured from returned pixels"
    for height, width, red, green in product((7, 18), (8, 22), (2, 8), (2, 8)):
        requested = {"grid_h": height, "grid_w": width, "n_red": red, "n_green": green}
        for index in (0, 1):
            grid = generator.generate(17, index, difficulty=difficulty, **requested)
            assert observer(grid) == requested
            assert generator.self_check(grid, difficulty=difficulty) == []
            _label(grid)
