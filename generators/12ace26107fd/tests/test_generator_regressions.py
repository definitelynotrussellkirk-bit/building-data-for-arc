"""Domain and teaching regressions for the selected onion-histogram sampler.

The independent distance oracle is diagnostic. Retained batteries and lesson
censuses execute the unchanged Racket authority for label verification.
"""
from collections import Counter, deque
import json

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "12ace26107fd"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def retained_counterexample(name):
    identity = f"generators/{TASK_ID}/counterexamples/{name}"
    manifest = ROOT / "RUNTIME_MANIFEST.json"
    if manifest.is_file():
        entries = [entry for entry in json.loads(manifest.read_text())["files"]
                   if entry["library_path"] == identity]
        assert entries, "portable runtime must retain the counterexample"
        path = ROOT / entries[0]["runtime_path"]
    else:
        path = ROOT / identity
    return json.loads(path.read_text())


def diagnostic_output(grid):
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
             if v not in (0, 9)}
    distance = {p: 1 for p in cells
                if any((p[0] + dr, p[1] + dc) not in cells for dr, dc in DELTAS)}
    queue = deque(distance)
    while queue:
        r, c = queue.popleft()
        for dr, dc in DELTAS:
            p = r + dr, c + dc
            if p in cells and p not in distance:
                distance[p] = distance[(r, c)] + 1
                queue.append(p)
    counts = Counter(distance.values())
    return [[counts[d] for d in range(1, max(counts, default=0) + 1)]]


def mask(rows, color=2):
    return [[color if x == "1" else 0 for x in row] for row in rows]


def test_all_canonical_inputs_accepted_including_13_cell_diamond():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert diagnostic_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("grid", [
    [[0] * 5 for _ in range(5)],
    [[2, 2, 0, 2, 2]],
    mask(("111", "101", "111")),
    [[2] * 5 for _ in range(2)],
    [[2, 2, 3]],
    [[9, 9, 9]],
    [[True, True, True]],
    [[2.0, 2.0, 2.0]],
    [[-1, -1, -1]],
    [[10, 10, 10]],
    [[2]],
])
def test_invalid_shape_domain_is_rejected(grid):
    assert GEN.self_check(grid), "invalid shape was accepted"


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_dimensions_and_area_are_honored_in_every_band(band):
    for size in range(3, 15):
        for h, w in ((5, 5), (7, 9), (16, 16)):
            grid = GEN.generate(41, 7, difficulty=band, grid_h=h, grid_w=w,
                                shape_size=size, color=6)
            assert (len(grid), len(grid[0])) == (h, w)
            assert sum(v != 0 for row in grid for v in row) == size
            assert {v for row in grid for v in row} == {0, 6}
            assert GEN.self_check(grid) == []
            assert all(1 <= v <= 9 for v in diagnostic_output(grid)[0])


@pytest.mark.parametrize("axis", ["grid_h", "grid_w", "shape_size", "color"])
@pytest.mark.parametrize("value", [True, 7.0, "7", -1, 40])
def test_exact_scalar_axes_reject_coercion_and_out_of_range(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **{axis: value})


def test_unknown_axis_is_not_silently_ignored():
    with pytest.raises(ValueError, match="unknown"):
        GEN.generate(1, 2, not_a_real_axis=7)


@pytest.mark.parametrize("argument,value", [
    ("seed", True), ("seed", False),
    ("seed", 1.0), ("seed", "1"),
    ("sample_index", True), ("sample_index", False), ("sample_index", -1),
    ("sample_index", 1.0), ("sample_index", "1"),
    ("difficulty", True), ("difficulty", False), ("difficulty", 0),
    ("difficulty", 1.0), ("difficulty", "unknown"),
])
def test_request_arguments_reject_silent_coercion(argument, value):
    arguments = {"seed": 991, "sample_index": 0, "difficulty": "easy"}
    arguments[argument] = value
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**arguments)


@pytest.mark.parametrize("seed", [-1, 2**32, 157627732520886, 2**128])
def test_public_integer_seed_contract_has_no_artificial_word_size(seed):
    """GenCtx hashes integer text; official profile/semantic seeds use 48 bits."""
    grid = GEN.generate(seed, 664, difficulty="easy")
    assert GEN.self_check(grid) == []
    assert grid == GEN.generate(seed, 664, difficulty="easy")


def test_rivals_are_total_on_retained_digit_domain_counterexamples():
    cases = retained_counterexample("rival_digit_domain.json")["cases"]
    assert cases
    for case in cases:
        for name in case["invalid_rival_predictions"]:
            prediction = GEN.CANONICAL_SHORTCUTS[name](case["input"])
            assert prediction == [[0]], "invalid counts use an impossible lawful-output sentinel"
            assert prediction != case["racket_output"]


def test_named_shortcuts_fit_the_complete_labeled_canonical_population():
    rivals = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert rivals, "canonical-fitting rivals need executable declarations"
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        for name, solve in rivals.items():
            assert solve(pair["input"]) == pair["output"], name


def test_default_demonstrations_contradict_every_area_only_function():
    """Same-area/different-output demos refute even unlisted area lookup tables."""
    for band in ("easy", "medium", "hard"):
        for seed in (0, 17, 1181072585):
            for start in range(9):
                grids = [GEN.generate(seed, start + i, difficulty=band) for i in range(6)]
                signatures = [(sum(v != 0 for row in grid for v in row),
                               tuple(diagnostic_output(grid)[0])) for grid in grids]
                for held_out in range(6):
                    by_area = {}
                    for i, (area, output) in enumerate(signatures):
                        if i != held_out:
                            by_area.setdefault(area, set()).add(output)
                    assert any(len(outputs) > 1 for outputs in by_area.values()), (
                        band, seed, start, held_out, signatures)


def test_nine_cell_concavity_is_scheduled_and_refutes_area_lookup():
    grid = mask(("101", "111", "100", "111"))
    assert GEN.self_check(grid) == []
    assert diagnostic_output(grid) == [[9]]
    assert GEN.LESSON_COMPETITORS["area_lookup"](grid) == [[8, 1]]
    assert GEN.LESSON_COMPETITORS["row_fill_then_peel"](grid) != [[9]]
    assert GEN.LESSON_COMPETITORS["column_fill_then_peel"](grid) != [[9]]
    sampled = GEN.generate(0, 1, difficulty="medium")
    assert sum(v != 0 for row in sampled for v in row) == 9
    assert diagnostic_output(sampled) == [[9]]


def test_retained_area_lookup_teaching_failure_is_now_detected():
    case = retained_counterexample("area_lookup_lesson_4_0_1.json")
    instance = case["lesson"]["instance"]
    demos, query = instance["train"], instance["test"][0]
    assert all(GEN.self_check(pair["input"]) == [] for pair in demos + [query])
    rival = GEN.LESSON_COMPETITORS["area_lookup"]
    assert all(rival(pair["input"]) == pair["output"] for pair in demos)
    assert rival(query["input"]) == [[8, 1]]
    assert query["output"] == [[9]]
    assert any("area_lookup" in reason for reason in GEN.lesson_identifiable(demos, query))


def test_exact_axial_and_concavity_counterexamples_are_lawful():
    axial = mask(("00100", "00100", "11111", "00100", "00100"))
    gaps = mask(("101", "111", "100", "110"))
    assert GEN.self_check(axial) == GEN.self_check(gaps) == []
    assert diagnostic_output(axial) == [[8, 1]]
    assert diagnostic_output(gaps) == [[8]]
    rivals = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert {"axial_ray_depth", "row_fill_then_peel", "column_fill_then_peel"} <= set(rivals)
    assert rivals["axial_ray_depth"](axial) == [[8, 0, 1]]
    assert rivals["row_fill_then_peel"](gaps) == [[9]]
    assert rivals["column_fill_then_peel"](gaps) == [[9]]


def test_default_lessons_and_every_query_rotation_refute_declared_rivals():
    assert getattr(GEN, "EXAMPLES_NEEDED", None) == 5
    assert getattr(GEN, "LESSON_SCHEDULE_PERIOD", None) == 3
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 17):
            for start in range(9):
                pairs = []
                for i in range(start, start + 6):
                    grid = GEN.generate(seed, i, difficulty=band)
                    assert GEN.self_check(grid) == []
                    pairs.append({"input": grid, "output": diagnostic_output(grid)})
                assert len({tuple(map(tuple, p["input"])) for p in pairs}) == 6
                for query_index, query in enumerate(pairs):
                    demos = [p for i, p in enumerate(pairs) if i != query_index]
                    assert GEN.lesson_identifiable(demos, query) == []
                    for name, solve in GEN.LESSON_COMPETITORS.items():
                        assert any(solve(p["input"]) != p["output"] for p in demos), name


def test_default_draws_retain_deep_shapes_and_multiple_histograms():
    for band in ("easy", "medium", "hard"):
        outputs = set()
        depths = set()
        for i in range(180):
            grid = GEN.generate(1201, i, difficulty=band)
            assert GEN.self_check(grid) == []
            result = diagnostic_output(grid)[0]
            assert all(1 <= value <= 9 for value in result)
            outputs.add(tuple(result))
            depths.add(len(result))
        assert {1, 2, 3} <= depths
        assert len(outputs) >= 8


def test_fixed_area_does_not_determine_the_histogram():
    outputs = set()
    for seed in range(40):
        grid = GEN.generate(seed, 0, shape_size=9, grid_h=7, grid_w=7)
        outputs.add(tuple(diagnostic_output(grid)[0]))
    assert len(outputs) >= 2
