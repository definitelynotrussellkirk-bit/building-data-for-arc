"""Behavioral contract for the solid-rectangle -> hollow-frame curriculum."""
from collections import Counter, deque
from itertools import product

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "ec491e97a5d5"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)


def components(grid):
    """Return same-color four-connected components as (color, frozenset(cells))."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = set()
            while queue:
                r, c = queue.popleft()
                cells.add((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            found.append((color, frozenset(cells)))
    return found


def oracle(grid):
    """Independent Python mirror used only by tests; Racket remains authority."""
    out = [[0] * len(grid[0]) for _ in grid]
    for color, cells in components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        for col in range(left, right + 1):
            out[top][col] = color
            out[bottom][col] = color
        for row in range(top, bottom + 1):
            out[row][left] = color
            out[row][right] = color
    return out


def test_canonical_inputs_are_owned_and_oracle_matches_all_labels():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 8 for _ in range(8)],
        [[4] * 8 for _ in range(8)],
        [[10, 0], [0, 0]],
        [[True, 0], [0, 0]],
        [[1.0, 0], [0, 0]],
        [[0, 0], [0]],
        [[4, 4, 4], [0, 0, 0], [0, 0, 0]],
    ],
)
def test_self_check_rejects_malformed_or_non_teaching_inputs(grid):
    assert GEN.self_check(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True},
        {"seed": 1.0},
        {"seed": "1"},
        {"sample_index": False},
        {"sample_index": -1},
        {"difficulty": True},
        {"difficulty": False},
        {"difficulty": 0},
        {"difficulty": 1.0},
        {"difficulty": "__invalid_difficulty__"},
    ],
)
def test_call_arguments_are_strict(kwargs):
    args = {"seed": 0, "sample_index": 0, "difficulty": "easy", **kwargs}
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**args)


@pytest.mark.parametrize("axis", ["grid_h", "grid_w", "n_rects", "n_colors"])
@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1"])
def test_exact_axis_scalars_never_coerce(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{axis: value})


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown"):
        GEN.generate(0, 0, typo_axis=2)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_full_dimension_domain_is_available_in_every_band(band):
    for height, width in product((8, 16), (9, 18)):
        grid = GEN.generate(7, 3, difficulty=band, grid_h=height, grid_w=width)
        assert (len(grid), len(grid[0])) == (height, width)
        assert GEN.observe_overrides(grid)["grid_h"] == height
        assert GEN.observe_overrides(grid)["grid_w"] == width
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_joint_object_and_color_controls_are_realized_or_declared_impossible(band):
    for n_rects in range(2, 5):
        for n_colors in range(1, 5):
            kwargs = {"n_rects": n_rects, "n_colors": n_colors,
                      "grid_h": 8, "grid_w": 9}
            if n_colors > n_rects:
                with pytest.raises(ValueError):
                    GEN.generate(19, 5, difficulty=band, **kwargs)
                continue
            grid = GEN.generate(19, 5, difficulty=band, **kwargs)
            observed = GEN.observe_overrides(grid)
            assert observed["n_rects"] == n_rects
            assert observed["n_colors"] == n_colors
            assert GEN.self_check(grid) == []
            assert oracle(grid) != grid


def test_default_draws_are_deterministic_lawful_and_non_identity():
    for band, seed, index in product(("easy", "medium", "hard"), range(4), range(12)):
        grid = GEN.generate(seed, index, difficulty=band)
        assert grid == GEN.generate(seed, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert oracle(grid) != grid
        assert Counter(v for row in oracle(grid) for v in row)[0] > Counter(
            v for row in grid for v in row
        )[0]


def test_declared_by_color_shortcut_fits_every_canonical_pair():
    shortcut = GEN.CANONICAL_SHORTCUTS["by_color"]
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert shortcut(pair["input"]) == pair["output"]


def test_every_default_four_pair_window_teaches_against_by_color_under_rotation():
    rival = GEN.LESSON_COMPETITORS["by_color"]
    for band, seed, start in product(("easy", "medium", "hard"), range(4), range(6)):
        pairs = []
        for offset in range(4):
            grid = GEN.generate(seed, start + offset, difficulty=band)
            pairs.append((grid, oracle(grid)))
        for query_index in range(4):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert any(rival(grid) != output for grid, output in demos), (
                band,
                seed,
                start,
                query_index,
            )


def test_racket_matches_oracle_on_canonical_and_generated_inputs():
    from arcpuzzles import Catalog

    inputs = [pair["input"] for pair in canonical_pairs(TASK_ID, root=ROOT)]
    inputs.extend(
        GEN.generate(31, index, difficulty=band)
        for band in ("easy", "medium", "hard")
        for index in range(6)
    )
    receipt = Catalog(ROOT).apply(TASK_ID, inputs, check_generator_domain=True)
    assert receipt["generator_sha256"] == SOURCE_SHA
    assert receipt["executed_rule_hash"] == GEN.RULE_HASH
    for row in receipt["results"]:
        assert row["error"] is None
        assert row["generator_domain"]["status"] == "valid"
        assert row["output"] == oracle(row["input"])


def test_difficulty_bands_change_default_geometry_without_changing_domains():
    for seed, sample_index in product(range(3), range(6)):
        grids = [
            GEN.generate(seed, sample_index, difficulty=band)
            for band in ("easy", "medium", "hard")
        ]
        frozen = {tuple(tuple(row) for row in grid) for grid in grids}
        assert len(frozen) == 3, (seed, sample_index)


def test_author_lesson_hook_accepts_every_default_four_pair_rotation():
    for band, seed, start in product(("easy", "medium", "hard"), range(3), range(4)):
        pairs = []
        for offset in range(4):
            grid = GEN.generate(seed, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": oracle(grid)})
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, pairs[query_index]) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_count_axis_reaches_its_full_domain_when_overridden_alone(band):
    for n_rects in range(2, 5):
        grid = GEN.generate(41, 1, difficulty=band, n_rects=n_rects)
        observed = GEN.observe_overrides(grid)
        assert observed["n_rects"] == n_rects
        assert observed["n_colors"] <= n_rects
    for n_colors in range(1, 5):
        grid = GEN.generate(43, 1, difficulty=band, n_colors=n_colors)
        observed = GEN.observe_overrides(grid)
        assert observed["n_colors"] == n_colors
        assert observed["n_rects"] >= n_colors


def test_retained_by_color_counterexample_matches_authority_and_declared_rival():
    import json

    path = ROOT / "generators" / TASK_ID / "counterexamples" / "by_color_shortcut.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    grid = record["input"]
    assert GEN.self_check(grid) == []
    assert oracle(grid) == record["intended_output"]
    assert GEN.CANONICAL_SHORTCUTS["by_color"](grid) == record["rival_output"]
    assert record["intended_output"] != record["rival_output"]
    assert record["generator_sha256"] == SOURCE_SHA
    assert record["rule_hash"] == GEN.RULE_HASH
