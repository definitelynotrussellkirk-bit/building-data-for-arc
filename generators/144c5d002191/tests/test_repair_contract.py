"""Behavioral regressions for the canonical stamping sampler; not variant tests."""
from collections import Counter
import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator("144c5d002191", root=ROOT)


def component_sizes(grid):
    """Independent small flood fill for observable object counts."""
    seen = set()
    result = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not value or (r, c) in seen:
                continue
            pending, cells = [(r, c)], []
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr-1,cc), (rr+1,cc), (rr,cc-1), (rr,cc+1)):
                    if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                            and (nr,nc) not in seen and grid[nr][nc] == value):
                        seen.add((nr,nc))
                        pending.append((nr,nc))
            result.append((value, len(cells)))
    return result


def lawful_repeated_markers():
    grid = [[0]*9 for _ in range(7)]
    for r, c in ((3,1), (3,2), (4,1), (4,2)):
        grid[r][c] = 8
    grid[0][0] = grid[1][1] = 2  # Separate 4-components, joined under 8-connectivity.
    return grid


def test_all_canonical_inputs_remain_accepted():
    for pair in canonical_pairs("144c5d002191", root=ROOT):
        assert GEN.self_check(pair["input"]) == []


def test_repeated_diagonal_markers_are_components_not_color_counts():
    grid = lawful_repeated_markers()
    assert sorted(size for _, size in component_sizes(grid)) == [1, 1, 4]
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("kind", ["blank", "no_template", "no_markers", "two_templates",
                                  "illegal_color", "boolean_color", "float_color",
                                  "ragged", "empty"])
def test_validator_rejects_invalid_training_inputs(kind):
    grid = lawful_repeated_markers()
    if kind == "blank":
        grid = [[0]*9 for _ in range(7)]
    elif kind == "no_template":
        grid = [[0]*9 for _ in range(7)]
        grid[0][0], grid[2][2] = 2, 3
    elif kind == "no_markers":
        grid[0][0] = grid[1][1] = 0
    elif kind == "two_templates":
        grid[5][6] = grid[5][7] = 5
    elif kind == "illegal_color":
        grid[0][0] = 10
    elif kind == "boolean_color":
        grid[0][0] = True
    elif kind == "float_color":
        grid[0][0] = 2.0
    elif kind == "ragged":
        grid[-1].pop()
    else:
        grid = []
    assert GEN.self_check(grid), kind


@pytest.mark.parametrize("overrides", [
    {"unknown_axis": 1}, {"palette_kind": "warm"}, {"grid_h": True},
    {"grid_w": 9.5}, {"n": "3"}, {"template_size": False},
    {"template_size": 3}, {"n": 6}, {"grid_h": 6}, {"grid_w": 19},
])
def test_invalid_or_retired_overrides_are_rejected(overrides):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(0, 0, difficulty="medium", **overrides)


@pytest.mark.parametrize("band", [None,"easy","hard"])
@pytest.mark.parametrize("axis,value", [
    *(('seed',v) for v in (True,False,1.0,1.75,'1')),
    *(('sample_index',v) for v in (True,False,1.0,1.75,'1',-1)),
])
def test_invalid_call_scalars_are_rejected(axis,value,band):
    request = dict(seed=991,sample_index=0,difficulty=band)
    request[axis] = value
    with pytest.raises((TypeError,ValueError)):
        GEN.generate(**request)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("n", [2, 3, 4, 5])
@pytest.mark.parametrize("index", [0, 1])
def test_smallest_joint_controls_are_observable_in_every_band(band, n, index):
    requested = {"grid_h": 7, "grid_w": 9, "n": n, "template_size": 7}
    grid = GEN.generate(13, index, difficulty=band, **requested)
    parts = component_sizes(grid)
    assert (len(grid), len(grid[0])) == (7, 9)
    assert sum(size == 1 for _, size in parts) == n
    assert [size for _, size in parts if size > 1] == [7]
    assert GEN.self_check(grid, difficulty=band) == []
    assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_profile_support_is_present_in_each_band(band):
    profiles = {(len(p["input"]), len(p["input"][0]),
                 len({v for row in p["input"] for v in row}))
                for p in canonical_pairs("144c5d002191", root=ROOT)}
    grids = [GEN.generate(0, i, difficulty=band) for i in range(20)]
    measured = [(len(g), len(g[0]), len({v for row in g for v in row})) for g in grids]
    assert sum(profile in profiles for profile in measured) >= 1
    assert sum(9 <= h <= 11 and 12 <= w <= 14 and 4 <= colors <= 5
               for h, w, colors in measured) >= 5


def test_full_arc_palette_and_component_counterexamples_have_support():
    grids = [GEN.generate(0, i, difficulty="medium") for i in range(40)]
    assert set(range(1,10)) <= {v for g in grids for row in g for v in row}
    assert any(len([v for v, size in component_sizes(g) if size == 1])
               > len({v for v, size in component_sizes(g) if size == 1}) for g in grids)


def test_draws_are_deterministic_and_do_not_share_mutable_grids():
    a = GEN.generate(123, 7, difficulty="hard")
    b = GEN.generate(123, 7, difficulty="hard")
    assert a == b
    a[0][0] = 10
    assert GEN.generate(123, 7, difficulty="hard") == b



def exact_component_order_witness():
    grid = [[0]*9 for _ in range(7)]
    for r,c in [(3,2),(3,3),(4,1),(4,2)]:
        grid[r][c] = 2
    for r,c,value in [(0,6,9),(0,7,3),(1,5,9)]:
        grid[r][c] = value
    expected = [[0]*9 for _ in range(7)]
    for r,c,value in [(0,7,9),(0,8,3),(1,6,9),(1,7,9),(1,8,3),(2,5,9),(2,6,9)]:
        expected[r][c] = value
    return grid, expected


def exact_row_color_order_witness():
    grid = [[0]*9 for _ in range(7)]
    for r,c in [(3,2),(3,3),(4,1),(4,2)]:
        grid[r][c] = 2
    for r,c,value in [(0,5,9),(0,6,3),(0,7,9),(1,4,9)]:
        grid[r][c] = value
    expected = [[0]*9 for _ in range(7)]
    for r,c,value in [(0,6,9),(0,7,3),(0,8,9),(1,5,9),(1,6,9),
                      (1,7,9),(1,8,9),(2,4,9),(2,5,9)]:
        expected[r][c] = value
    return grid, expected


def test_row_color_order_regression_witness_is_reachable():
    grid, expected = exact_row_color_order_witness()
    assert GEN.generate(138,1,difficulty="medium",grid_h=7,grid_w=9,n=4,template_size=4) == grid
    assert GEN.self_check(grid) == []
    assert GEN._predict(grid) == expected
    assert len(GEN.CANONICAL_SHORTCUTS) >= 19
    for name,rival in GEN.CANONICAL_SHORTCUTS.items():
        assert rival(grid) != expected, name
    assert GEN.rival_row_ascending_color_order(grid)[0][7] == 9
    assert GEN.rival_row_descending_color_order(grid)[0][8] == 3


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_witnesses_refute_both_row_color_orders(band):
    for index in range(1,40,2):
        grid = GEN.generate(0,index,difficulty=band)
        assert GEN.observe_overrides(grid)["n"] >= 4
        expected = GEN._predict(grid)
        assert GEN.rival_row_ascending_color_order(grid) != expected
        assert GEN.rival_row_descending_color_order(grid) != expected


def test_original_component_regression_remains_reachable_under_explicit_n3():
    grid, expected = exact_component_order_witness()
    assert GEN.generate(138,1,difficulty="medium",grid_h=7,grid_w=9,n=3,template_size=4) == grid
    assert GEN.self_check(grid) == []
    assert len(GEN.CANONICAL_SHORTCUTS) >= 16
    later_order_rivals = {"descending_color_marker_order",
                         "within_row_ascending_color_marker_order",
                         "within_row_descending_color_marker_order"}
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        if name in later_order_rivals:
            continue
        assert rival(grid) != expected, name
    assert GEN.rival_column_order(grid)[1][7] == 3
    assert expected[1][7] == 9


def test_every_declared_canonical_shortcut_fits_all_labeled_canonical_pairs():
    pairs = canonical_pairs("144c5d002191",root=ROOT,labeled_only=True)
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert rival(pair["input"]) == pair["output"], (name,pair["split"],pair["pair_index"])


def test_reference_racket_labels_the_fixed_witness_and_each_schedule_residue():
    import json
    from reviewer_support import canonical_path
    from arc_repl.racket_bridge import RacketBridge
    with canonical_path(ROOT).open() as stream:
        canonical = next(json.loads(line) for line in stream
                         if json.loads(line).get("task_id") == "144c5d002191")
    program = canonical["program_solution"]
    with RacketBridge(timeout=10,startup_timeout=60) as bridge:
        def label(grid):
            bridge.define_grid("__regression_input__",grid)
            return bridge.eval_text(
                "(let ((g __regression_input__) (rule! (lambda (value) value))) "
                + program + ")")
        grid, expected = exact_component_order_witness()
        assert label(grid) == expected
        grid, expected = exact_row_color_order_witness()
        assert label(grid) == expected
        for band in ("easy","medium","hard"):
            pairs = []
            # The two complete starts require five raw accepted pairs.
            for index in range(5):
                inp = GEN.generate(0,index,difficulty=band)
                pairs.append({"input":inp,"output":label(inp)})
            for start in range(GEN.LESSON_SCHEDULE_PERIOD):
                window = pairs[start:start+GEN.EXAMPLES_NEEDED+1]
                for query_index, query in enumerate(window):
                    demos = [pair for i,pair in enumerate(window) if i != query_index]
                    assert GEN.lesson_identifiable(demos,query) == [], (band,start,query_index)
