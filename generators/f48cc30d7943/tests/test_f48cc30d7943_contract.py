"""Portable regressions for the repaired two-red-chamber teaching contract.

The independent oracle is checked against 36 retained Racket labels and all
five exact canonical pairs.  It never calls a generator labeling helper.  Rival
expectations below implement literal alternative rules; declaration names are
diagnostics rather than an inventory snapshot.  See TEST_RATIONALE.md for scope.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest


# The public stage exposes reviewer_support directly.  This local-only fallback
# also permits direct pytest from an independently copied library checkout.
try:
    from reviewer_support import canonical_pairs, find_root
except ModuleNotFoundError:
    for ancestor in Path(__file__).resolve().parents:
        runtime = ancestor / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    from reviewer_support import canonical_pairs, find_root


TASK = "f48cc30d7943"
ROOT = find_root(__file__)
for relative in (
    f"generators/{TASK}/generator.py",
    f"puzzle_generators/per_puzzle/{TASK}/generator.py",
):
    source = ROOT / relative
    if source.is_file():
        break
else:
    raise FileNotFoundError(f"No selected {TASK} generator under {ROOT}")
spec = importlib.util.spec_from_file_location("f48cc30d7943_contract_subject", source)
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)

CANONICAL = canonical_pairs(TASK, root=ROOT)
REFERENCE = json.loads(
    Path(__file__).with_name("reference_cases_f48cc30d7943.json").read_text()
)["cases"]
BANDS = (None, "easy", "medium", "hard")
D4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
D8 = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c)


def groups(grid, *, directions=D4, passable=lambda value: value != 5):
    """Independent finite-grid flood fill; no path outside the canvas exists."""
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
               if passable(value)}
    result = []
    while pending:
        start = min(pending)
        pending.remove(start)
        chamber, queue = {start}, deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in directions:
                cell = r + dr, c + dc
                if cell in pending:
                    pending.remove(cell)
                    chamber.add(cell)
                    queue.append(cell)
        result.append(chamber)
    return result


def red_count(grid, cells):
    return sum(grid[r][c] == 2 for r, c in cells)


def has_zero(grid, cells):
    return any(grid[r][c] == 0 for r, c in cells)


def box_cells(cells):
    rows, columns = zip(*cells)
    return {(r, c) for r in range(min(rows), max(rows) + 1)
            for c in range(min(columns), max(columns) + 1)}


def oracle(grid):
    answer = deepcopy(grid)
    for chamber in groups(grid):
        if red_count(grid, chamber) == 2:
            for r, c in chamber:
                if grid[r][c] == 0:
                    answer[r][c] = 8
    return answer


def grid_errors(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        return ["height or outer container"]
    if any(type(row) is not list for row in grid):
        return ["row container"]
    width = len(grid[0])
    if not 1 <= width <= 30 or any(len(row) != width for row in grid):
        return ["width or rectangularity"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["exact digit integers"]
    return []


def teaching_errors(grid):
    if errors := grid_errors(grid):
        return errors
    chambers = groups(grid)
    errors = []
    if len(chambers) < 2:
        errors.append("at least two chambers")
    if not any(red_count(grid, cells) == 2 and has_zero(grid, cells)
               for cells in chambers):
        errors.append("visible positive chamber")
    if not any(red_count(grid, cells) != 2 and has_zero(grid, cells)
               for cells in chambers):
        errors.append("visible negative chamber")
    return errors


def accepted_strict(result):
    assert type(result) is bool or isinstance(result, list), type(result)
    return result if type(result) is bool else result == []


def require_callable(name):
    result = getattr(gen, name, None)
    assert callable(result), f"Missing callable {name}"
    return result


def registry(name):
    value = getattr(gen, name, None)
    assert isinstance(value, dict) and value, f"Missing nonempty {name}"
    assert all(isinstance(key, str) and key and callable(fn)
               for key, fn in value.items()), name
    return value


def predict_pure(fn, grid):
    original = deepcopy(grid)
    supplied = deepcopy(grid)
    answer = fn(supplied)
    assert supplied == original, "rival mutated its input"
    assert grid_errors(answer) == [], "rival returned a malformed grid"
    assert answer == fn(deepcopy(grid)), "rival is not deterministic"
    return answer


def red_objects(grid, cells):
    pending = {cell for cell in cells if grid[cell[0]][cell[1]] == 2}
    count = 0
    while pending:
        count += 1
        queue = [pending.pop()]
        for r, c in queue:
            for dr, dc in D4:
                cell = r + dr, c + dc
                if cell in pending:
                    pending.remove(cell)
                    queue.append(cell)
    return count


def literal_rival(grid, mode):
    """Alternative operations, without consulting the subject declarations."""
    answer = deepcopy(grid)
    if mode == "full line partition":
        walls_r = [r for r, row in enumerate(grid) if all(v == 5 for v in row)]
        walls_c = [c for c in range(len(grid[0]))
                   if all(row[c] == 5 for row in grid)]
        partitions = {}
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value != 5:
                    key = sum(w < r for w in walls_r), sum(w < c for w in walls_c)
                    partitions.setdefault(key, set()).add((r, c))
        chambers = list(partitions.values())
    elif mode == "eight connected":
        chambers = groups(grid, directions=D8)
    elif mode == "zero red traversal":
        chambers = groups(grid, passable=lambda value: value in (0, 2))
    elif mode == "eight as wall":
        chambers = groups(grid, passable=lambda value: value not in (5, 8))
    else:
        chambers = groups(grid)
    for cells in chambers:
        scanned = box_cells(cells) if mode == "bbox seed count" else cells
        reds = {cell for cell in scanned if grid[cell[0]][cell[1]] == 2}
        count = len(reds)
        if mode == "all marks count":
            count = sum(grid[r][c] not in (0, 5) for r, c in scanned)
        if mode == "red plus eight count":
            count = sum(grid[r][c] in (2, 8) for r, c in scanned)
        if mode == "red objects four":
            count = red_objects(grid, scanned)
        qualifies = count == 2
        if mode == "positive even":
            qualifies = count > 0 and count % 2 == 0
        elif mode == "two modulo three":
            qualifies = count % 3 == 2
        elif mode == "two or at least four":
            qualifies = count == 2 or count >= 4
        elif mode == "at least two":
            qualifies = count >= 2
        elif mode == "one or two":
            qualifies = 1 <= count <= 2
        elif mode == "nearby red pair":
            qualifies = count == 2 and max(
                abs(r - rr) + abs(c - cc) for r, c in reds for rr, cc in reds
            ) <= 8
        elif mode == "boundary activates":
            qualifies = qualifies or any(
                r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1) for r, c in cells
            )
        elif mode == "shape selector" and cells != box_cells(cells):
            qualifies = any(r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1)
                            for r, c in cells) or any(
                {(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)} <= cells
                for r, c in cells
            )
        if mode == "rectangles only" and cells != box_cells(cells):
            qualifies = False
        if mode == "enclosed only" and any(
            r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1) for r, c in cells
        ):
            qualifies = False
        if not qualifies:
            continue
        painted = box_cells(cells) if mode == "bbox fill" else cells
        for r, c in painted:
            if mode == "radius eight" and min(abs(r - sr) + abs(c - sc)
                                              for sr, sc in reds) > 8:
                continue
            if grid[r][c] == 0 or (
                mode == "paint nonwall nonred" and grid[r][c] not in (2, 5)
            ):
                answer[r][c] = 8
    return answer


PRIMARY_RULES = (
    "full line partition", "eight connected", "zero red traversal",
    "bbox fill", "bbox seed count", "rectangles only", "positive even",
    "two modulo three", "two or at least four", "all marks count",
    "paint nonwall nonred", "radius eight", "enclosed only",
    "eight as wall", "red plus eight count",
    "nearby red pair", "boundary activates", "shape selector",
)
SECONDARY_RULES = ("red objects four", "at least two", "one or two")


def prediction_signature(fn, grids):
    return tuple(json.dumps(fn(deepcopy(grid)), separators=(",", ":")) for grid in grids)


@pytest.mark.parametrize("case", REFERENCE, ids=lambda case: case["id"])
def test_independent_oracle_matches_retained_racket_labels(case):
    assert oracle(case["input"]) == case["output"]


@pytest.mark.parametrize("pair", CANONICAL,
                         ids=lambda pair: f"v{pair['variant']}_{pair['split']}_{pair['pair_index']}")
def test_exact_canonical_pairs_remain_accepted(pair):
    original = deepcopy(pair)
    assert oracle(pair["input"]) == pair["output"]
    assert teaching_errors(pair["input"]) == []
    assert gen.self_check(pair["input"]) == []
    assert accepted_strict(require_callable("strict_canonical_like")(pair["input"]))
    assert pair == original


def test_public_axes_are_the_two_exact_size_controls():
    assert set(gen.AXES) == {"grid_h", "grid_w"}
    for name, bounds in (("grid_h", "7..26"), ("grid_w", "7..28")):
        assert gen.AXES[name]["type"] == "int"
        assert gen.AXES[name]["valid"] == bounds


@pytest.mark.parametrize("band", BANDS)
def test_all_joint_size_overrides(band):
    """440 combinations per band; finish all draws even when dimensions fail."""
    failures, checked = [], 0
    observe = getattr(gen, "observe_overrides", None)
    for height in range(7, 27):
        for width in range(7, 29):
            checked += 1
            sample_index = (height + width) % 3
            try:
                grid = gen.generate(20261008, sample_index, difficulty=band,
                                    grid_h=height, grid_w=width)
                assert grid_errors(grid) == [], grid_errors(grid)
                assert (len(grid), len(grid[0])) == (height, width), "wrong dimensions"
                assert len({id(row) for row in grid}) == height, "aliased rows"
                assert teaching_errors(grid) == [], teaching_errors(grid)
                assert gen.self_check(grid, difficulty=band) == []
                assert callable(observe), "missing observe_overrides"
                assert observe(grid) == {"grid_h": height, "grid_w": width}
            except Exception as exc:
                failures.append((height, width, sample_index, type(exc).__name__, str(exc)))
    assert checked == 20 * 22
    assert not failures, f"{len(failures)}/{checked} failures; first cases: {failures[:12]}"


@pytest.mark.parametrize("band", BANDS)
def test_size_endpoints_and_interior_work_in_each_schedule_residue(band):
    for height, width in ((7, 7), (7, 28), (26, 7), (26, 28), (11, 12), (12, 11),
                          (12, 12), (17, 19)):
        for index in range(3):
            grid = gen.generate(3901, index, difficulty=band, grid_h=height, grid_w=width)
            assert (len(grid), len(grid[0])) == (height, width)
            assert teaching_errors(grid) == []
            assert gen.self_check(grid, difficulty=band) == []


@pytest.mark.parametrize("name,bad", [
    (name, value) for name, high in (("grid_h", 26), ("grid_w", 28))
    for value in (False, True, 7.0, 12.5, "12", "varies", [], {}, 6, high + 1, -1)
])
def test_size_overrides_reject_noninteger_or_out_of_domain_values(name, bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(901, 1, **{name: bad})


@pytest.mark.parametrize("name", ["typo", "rooms_r", "rooms_c", "texture",
                                  "palette_size", "seed_per_region"])
@pytest.mark.parametrize("value", [None, 1, "default"])
def test_unknown_overrides_are_rejected_even_when_none(name, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(901, 1, **{name: value})


@pytest.mark.parametrize("difficulty", [False, True, 0, 1, "", "invalid", "Easy", [], {}])
def test_unknown_difficulties_are_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(901, 1, difficulty=difficulty)


@pytest.mark.parametrize("band", BANDS)
def test_determinism_none_controls_and_mutation_isolation(band):
    state = random.getstate()
    try:
        random.seed(61008)
        untouched = random.getstate()
        for seed, index in ((0, 0), (0, 1), (31, 2), (31, 7)):
            baseline = gen.generate(seed, index, difficulty=band)
            original = deepcopy(baseline)
            assert gen.generate(seed, index, difficulty=band) == original
            for controls in ({"grid_h": None}, {"grid_w": None},
                             {"grid_h": None, "grid_w": None}):
                unchanged_controls = deepcopy(controls)
                assert gen.generate(seed, index, difficulty=band, **controls) == original
                assert controls == unchanged_controls
            assert random.getstate() == untouched
            assert len({id(row) for row in baseline}) == len(baseline)
            baseline[0][0] = (baseline[0][0] + 1) % 10
            assert gen.generate(seed, index, difficulty=band) == original
        assert random.getstate() == untouched
    finally:
        random.setstate(state)


@pytest.mark.parametrize("case", REFERENCE, ids=lambda case: case["id"])
def test_rule_grid_validator_accepts_checked_rule_domain(case):
    original = deepcopy(case["input"])
    assert require_callable("rule_grid_errors")(case["input"]) == []
    assert case["input"] == original


@pytest.mark.parametrize("grid", [
    None, (), [], [[]], [[0], []], [[0], [0, 2]], [[True]], [[2.0]], [["2"]],
    [[None]], [[-1]], [[10]], [(0,)], [[0] * 31], [[0] for _ in range(31)],
])
def test_rule_grid_validator_rejects_malformed_grids_without_raising(grid):
    before = deepcopy(grid)
    errors = require_callable("rule_grid_errors")(grid)
    assert isinstance(errors, list) and errors
    assert grid == before


@pytest.mark.parametrize("grid", [
    [[0] * 30], [[0] for _ in range(30)], [[v % 10 for v in range(30)] for _ in range(30)],
])
def test_rule_grid_validator_accepts_runtime_dimension_endpoints(grid):
    assert require_callable("rule_grid_errors")(grid) == []


TEACHING_GRIDS = [
    [[2, 0, 0], [5, 5, 2], [0, 5, 0]],
    [[2, 2, 0, 5, 5], [5, 5, 5, 2, 0]],
    [[2, 2, 0, 5, 2, 2, 2, 2, 0]],
    [[2, 2, 0, 5, 2, 2, 2, 2, 2, 0]],
    [[2, 2, 0, 5, 2, 0]],
] + [[[2, 0, color, 0, 2, 5, 0]] for color in (1, 3, 4, 6, 7, 8, 9)]


@pytest.mark.parametrize("grid", TEACHING_GRIDS)
def test_teaching_selfcheck_accepts_nonrectangles_bridges_and_high_negative_counts(grid):
    original = deepcopy(grid)
    assert teaching_errors(grid) == []
    assert gen.self_check(grid) == []
    assert grid == original


@pytest.mark.parametrize("grid", [
    [[5, 5]], [[0, 0]], [[2, 2, 0]], [[2, 2, 5, 0]],
    [[2, 2, 0, 5, 2, 2, 2]], [[2, 2, 0, 5, 2, 2, 0]],
])
def test_teaching_selfcheck_requires_visible_positive_and_negative_chambers(grid):
    assert teaching_errors(grid)
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors


def test_strict_canonical_profile_rejects_general_rule_extensions():
    strict = require_callable("strict_canonical_like")
    cases = []
    # Frame, palette, room-count, and size mutations retain the source geometry
    # where possible; their rejection is about canonical likeness only.
    grid = deepcopy(CANONICAL[0]["input"])
    grid[0][0] = 0
    cases.append(grid)
    grid = deepcopy(CANONICAL[0]["input"])
    cell = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0)
    grid[cell[0]][cell[1]] = 6
    cases.append(grid)
    grid = deepcopy(CANONICAL[0]["input"])
    positive = next(cells for cells in groups(grid) if red_count(grid, cells) == 2)
    for r, c in sorted(cell for cell in positive if grid[cell[0]][cell[1]] == 0)[:2]:
        grid[r][c] = 2
    cases.append(grid)
    grid = deepcopy(CANONICAL[0]["input"])
    grid.extend([[5] * len(grid[0]) for _ in range(4)])
    cases.append(grid)
    cases.extend(deepcopy(TEACHING_GRIDS))
    for grid in cases:
        assert not accepted_strict(strict(grid)), grid


def test_declared_rivals_execute_literal_alternatives_and_fit_canonical_claims():
    shortcuts = registry("CANONICAL_SHORTCUTS")
    semantic = registry("SEMANTIC_RIVALS")
    lesson = registry("LESSON_COMPETITORS")
    grids = [pair["input"] for pair in CANONICAL] + [case["input"] for case in REFERENCE]
    grids += [gen.generate(seed, 1, difficulty="hard") for seed in (0, 73, 991)]
    observed_primary = {prediction_signature(fn, grids) for fn in shortcuts.values()}
    observed_lesson = {prediction_signature(fn, grids) for fn in lesson.values()}
    for rule in PRIMARY_RULES:
        expected = prediction_signature(lambda grid: literal_rival(grid, rule), grids)
        assert expected in observed_primary, f"Missing literal canonical alternative: {rule}"
    for rule in PRIMARY_RULES + SECONDARY_RULES:
        expected = prediction_signature(lambda grid: literal_rival(grid, rule), grids)
        assert expected in observed_lesson, f"Missing literal lesson alternative: {rule}"
    for name, fn in shortcuts.items():
        for pair in CANONICAL:
            assert predict_pure(fn, pair["input"]) == pair["output"], name
    for name, fn in {**semantic, **lesson}.items():
        for case in REFERENCE:
            predict_pure(fn, case["input"])
    for rule in SECONDARY_RULES:
        assert any(literal_rival(pair["input"], rule) != pair["output"] for pair in CANONICAL)


@pytest.mark.parametrize("band", BANDS)
def test_schedule_profiles_track_canonical_and_rich_geometry(band):
    profile = require_callable("schedule_profile")
    strict = require_callable("strict_canonical_like")
    assert type(gen.EXAMPLES_NEEDED) is int and gen.EXAMPLES_NEEDED == 3
    assert type(gen.LESSON_SCHEDULE_PERIOD) is int and gen.LESSON_SCHEDULE_PERIOD == 3
    strict_support = 0
    framed_room_counts = set()
    for seed in (0, 1729, 8191):
        labels = [profile(seed, index, difficulty=band) for index in range(9)]
        assert labels[:3] == labels[3:6] == labels[6:9]
        assert labels[0] != labels[1] and labels[0] != labels[2]
        for index in range(9):
            grid = gen.generate(seed, index, difficulty=band)
            assert teaching_errors(grid) == []
            assert gen.self_check(grid, difficulty=band) == []
            if index % 3 == 0:
                strict_support += accepted_strict(strict(grid))
                assert 10 <= len(grid) <= 12 and 10 <= len(grid[0]) <= 12
                assert all(v == 5 for v in grid[0] + grid[-1])
                assert all(row[0] == row[-1] == 5 for row in grid)
                chambers = groups(grid)
                framed_room_counts.add(len(chambers))
                assert 2 <= len(chambers) <= 9
                assert all(cells == box_cells(cells) for cells in chambers)
                assert all(red_count(grid, cells) <= 3 for cells in chambers)
                assert {value for row in grid for value in row} <= {0, 2, 5}
            else:
                assert 12 <= len(grid) <= 26 and 12 <= len(grid[0]) <= 28
                assert not accepted_strict(strict(grid))
    assert strict_support > 0, "Framed draws never supplied a strict canonical profile"
    assert framed_room_counts


def rich_geometry_errors(grid):
    chambers = groups(grid)
    positive = [cells for cells in chambers if red_count(grid, cells) == 2 and has_zero(grid, cells)]
    negatives = {red_count(grid, cells) for cells in chambers
                 if red_count(grid, cells) != 2 and has_zero(grid, cells)}
    errors = []
    if not {1, 4, 5} <= negatives:
        errors.append("missing visible one-, four-, or five-red negative")
    nonrectangles = [cells for cells in positive if cells != box_cells(cells)]
    open_region = lambda cells: any(r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1)
                                    for r, c in cells)
    if not any(open_region(cells) for cells in positive):
        errors.append("missing open positive")
    negative_chambers = [cells for cells in chambers
                         if red_count(grid, cells) != 2 and has_zero(grid, cells)]
    if not any(open_region(cells) for cells in negative_chambers):
        errors.append("missing open negative")
    if not any(cells != box_cells(cells) and any(
        {(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)} <= cells for r, c in cells
    ) for cells in negative_chambers):
        errors.append("missing nonrectangular thick negative")
    if not any(max(abs(r - rr) + abs(c - cc)
                   for r, c in cells if grid[r][c] == 2
                   for rr, cc in cells if grid[rr][cc] == 2) > 8 for cells in positive):
        errors.append("missing widely separated positive red pair")
    if not any(not open_region(cells) for cells in nonrectangles):
        errors.append("missing enclosed nonrectangular positive")
    if not any(red_objects(grid, cells) == 1 for cells in positive):
        errors.append("missing adjacent two-red cells")
    if not any(any(grid[r][c] == 8 for r, c in cells) for cells in positive):
        errors.append("missing original cyan eight in a positive chamber")
    if not any(any(grid[r][c] == 0 and all(abs(r - sr) + abs(c - sc) > 8
                                         for sr, sc in cells if grid[sr][sc] == 2)
                   for r, c in cells) for cells in positive):
        errors.append("missing zero farther than radius eight")
    if not any(any(grid[r][c] == 0 for r, c in box_cells(cells) - cells)
               and any(grid[r][c] == 2 for r, c in box_cells(cells) - cells)
               for cells in nonrectangles):
        errors.append("missing foreign zero and red inside a positive bbox")
    bridge_found = False
    for cells in positive:
        for r, c in cells:
            if grid[r][c] in (0, 2, 5, 8):
                continue
            blocked = deepcopy(grid)
            blocked[r][c] = 5
            pieces = [part for part in groups(blocked) if part <= cells]
            if len(pieces) > 1 and all(red_count(blocked, part) < 2 for part in pieces):
                bridge_found = True
    if not bridge_found:
        errors.append("missing preserved foreign-color articulation separating the red cells")
    return errors


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("seed", [0, 991, 20261008])
def test_rich_default_draws_visibly_refute_literal_and_declared_rivals(band, seed):
    declared = [(f"{namespace}/{name}", fn)
                for namespace in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS")
                for name, fn in registry(namespace).items()]
    for index in (1, 2, 4, 5):
        grid = gen.generate(seed, index, difficulty=band)
        answer = oracle(grid)
        assert rich_geometry_errors(grid) == [], rich_geometry_errors(grid)
        for rule in PRIMARY_RULES + SECONDARY_RULES:
            assert literal_rival(grid, rule) != answer, (seed, index, band, rule)
        for name, fn in declared:
            assert predict_pure(fn, grid) != answer, (seed, index, band, name)


def test_witness_claims_are_real_disagreements_on_supplied_grids():
    witnesses = registry("SEMANTIC_WITNESSES")
    rivals = registry("SEMANTIC_RIVALS")
    links = getattr(gen, "WITNESS_RIVALS", None)
    assert isinstance(links, dict) and links
    for witness, names in links.items():
        assert witness in witnesses
        assert isinstance(names, (list, tuple)) and names
        assert all(name in rivals for name in names)
    grids = [pair["input"] for pair in CANONICAL] + [case["input"] for case in REFERENCE]
    grids += [gen.generate(812, index, difficulty=band) for band in BANDS for index in range(6)]
    firings = set()
    for grid in grids:
        answer = oracle(grid)
        for name, fn in witnesses.items():
            supplied = deepcopy(grid)
            fires = fn(supplied)
            assert type(fires) is bool, name
            assert supplied == grid, name
            if fires:
                firings.add(name)
                assert name in links, f"Unclaimed witness {name}"
                assert any(predict_pure(rivals[rival], grid) != answer for rival in links[name]), name
    assert set(witnesses) <= firings, f"Unexercised witnesses: {set(witnesses) - firings}"


@pytest.mark.parametrize("band", BANDS)
def test_every_four_draw_window_remains_identifiable_after_any_single_query_holdout(band):
    hook = require_callable("lesson_identifiable")
    declared = [(f"{namespace}/{name}", fn)
                for namespace in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS")
                for name, fn in registry(namespace).items()]
    for seed in (0, 73, 8191):
        grids = [gen.generate(seed, index, difficulty=band) for index in range(12)]
        pairs = [{"input": grid, "output": oracle(grid)} for grid in grids]
        predictions = {name: [predict_pure(fn, grid) for grid in grids] for name, fn in declared}
        for start in range(9):
            for query_index in range(start, start + 4):
                demo_indices = [i for i in range(start, start + 4) if i != query_index]
                assert any(i % 3 != 0 for i in demo_indices)
                for name, outputs in predictions.items():
                    fits = all(outputs[i] == pairs[i]["output"] for i in demo_indices)
                    assert not fits or outputs[query_index] == pairs[query_index]["output"], (
                        seed, band, start, query_index, name)
                demos = deepcopy([pairs[i] for i in demo_indices])
                query = deepcopy(pairs[query_index])
                before = deepcopy((demos, query))
                assert hook(demos, query) == [], (seed, band, start, query_index)
                assert (demos, query) == before


def test_lesson_hook_scores_supplied_labels_instead_of_relabeling_inputs():
    hook = require_callable("lesson_identifiable")
    rivals = registry("LESSON_COMPETITORS")
    grid = gen.generate(991, 1, difficulty="hard")
    true_answer = oracle(grid)
    for name, fn in rivals.items():
        alternative = predict_pure(fn, grid)
        assert alternative != true_answer, name
        demo = {"input": deepcopy(grid), "output": deepcopy(alternative)}
        # A rival that fits these supplied demonstration labels contradicts the
        # supplied query label, even though its demonstration is nonauthoritative.
        query = {"input": deepcopy(grid), "output": deepcopy(true_answer)}
        reasons = hook([deepcopy(demo)], query)
        assert isinstance(reasons, list) and reasons, f"Ignored supplied demo label: {name}"
        assert all(isinstance(reason, str) for reason in reasons)
        # Repeating exactly the demonstrated labeled pair is unambiguous among
        # deterministic rivals.  Disagreement with an internal oracle is irrelevant.
        assert hook([deepcopy(demo)], deepcopy(demo)) == [], name


def test_exact_discovered_seed31_lesson_now_refutes_nearby_pair_shortcut():
    """The independently found pre-fix lesson is a permanent seed regression."""
    pairs = [{"input": gen.generate(31, index, difficulty="easy")} for index in range(4)]
    for pair in pairs:
        pair["output"] = oracle(pair["input"])
    assert any(literal_rival(pair["input"], "nearby red pair") != pair["output"]
               for pair in pairs[:3]), "Old teaching gap survives in its original lesson"
    assert require_callable("lesson_identifiable")(deepcopy(pairs[:3]), deepcopy(pairs[3])) == []

