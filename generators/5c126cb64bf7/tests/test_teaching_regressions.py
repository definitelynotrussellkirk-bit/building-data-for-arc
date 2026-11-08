"""Regressions for defects reproduced on the pinned 2.1.1 baseline."""
import importlib.util
import pytest

from reviewer_support import find_root


def load_generator():
    root = find_root(__file__)
    candidates = [root / "generators/5c126cb64bf7/generator.py",
                  root / "puzzle_generators/per_puzzle/5c126cb64bf7/generator.py"]
    path = next(path for path in candidates if path.is_file())
    spec = importlib.util.spec_from_file_location("rotation_generator_regression", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = load_generator()


def panel(grid, start):
    return [[int(value != 0) for value in row[start:start + 5]] for row in grid]


def cropped(array):
    rows = [i for i, row in enumerate(array) if any(row)]
    cols = [j for j in range(len(array[0])) if any(row[j] for row in array)]
    return tuple(tuple(row[min(cols):max(cols) + 1])
                 for row in array[min(rows):max(rows) + 1])


def orbit(array):
    states = []
    for _ in range(4):
        states.append(cropped(array))
        array = [list(row) for row in zip(*array[::-1])]
    return min(states)


def test_equal_cell_counts_do_not_determine_rotation_class():
    collisions = []
    for index in range(30):
        grid = GEN.generate(17, index, difficulty="medium")
        panels = [panel(grid, start) for start in (0, 6, 12)]
        for i in range(3):
            for j in range(i + 1, 3):
                if sum(map(sum, panels[i])) == sum(map(sum, panels[j])):
                    collisions.append(orbit(panels[i]) != orbit(panels[j]))
    assert any(collisions), "equal-count non-equivalent shapes must be generated"


def test_default_shapes_are_translated_inside_panels():
    for index in range(30):
        grid = GEN.generate(17, index, difficulty="medium")
        for start in (0, 6, 12):
            cells = [(r, c) for r, row in enumerate(panel(grid, start))
                     for c, value in enumerate(row) if value]
            if min(r for r, c in cells) > 0 and min(c for r, c in cells) > 0:
                return
    raise AssertionError("all generated panels remain anchored at the top-left")


def test_nonzero_separator_is_rejected():
    grid = GEN.generate(17, 0, difficulty="medium")
    grid[0][5] = 9
    assert GEN.self_check(grid)


def test_palette_size_one_is_observable():
    grid = GEN.generate(17, 0, difficulty="medium", palette_size=1)
    assert len({v for row in grid for v in row if v}) == 1


def test_unknown_axis_is_not_silently_ignored():
    with pytest.raises((ValueError, TypeError, KeyError)):
        GEN.generate(17, 0, difficulty="medium", typo_axis=7)


@pytest.mark.parametrize("seed,start,band", [
    (5, 0, "easy"),
    (3944080271, 27, "easy"),
    (1873861243, 45, "medium"),
])
def test_halfturn_witness_is_not_lost_to_rotational_symmetry(seed, start, band):
    pairs = []
    for index in range(start, start + 10):
        grid = GEN.generate(seed, index, difficulty=band)
        keys = [orbit(panel(grid, col)) for col in (0, 6, 12)]
        output = [[8 if i == j else 2 if keys[i] == keys[j] else 0
                   for j in range(3)] for i in range(3)]
        pairs.append({"input": grid, "output": output})
    rival = GEN.LESSON_COMPETITORS["no_halfturn"]
    mismatches = [rival(pair["input"]) != pair["output"] for pair in pairs]
    assert sum(mismatches) >= 2, "one refutation can become the sole query"


def test_free_slots_emit_mixed_canonical_connectivity():
    seen = set()
    for seed in range(10):
        for index in range(10):
            grid = GEN.generate(seed, index, difficulty="medium")
            seen.add(GEN.observe_overrides(grid)["texture"])
    assert "mixed" in seen


def test_free_slots_do_not_fix_the_output_class_histogram():
    histograms = set()
    for seed in range(10):
        counts = [0, 0, 0]
        for index in range(10):
            observed = GEN.observe_overrides(GEN.generate(seed, index, difficulty="medium"))
            counts[observed["n_classes"] - 1] += 1
        histograms.add(tuple(counts))
    assert len(histograms) > 1
