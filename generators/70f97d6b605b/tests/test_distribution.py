"""Behavioral regressions for the exact monochromatic eight-component selector.

The small Python oracle is independent test code, not a label authority. Its
canonical comparisons and hand witnesses are checked separately through Racket.
These tests work both in the repository and in the public task-test runtime.
"""
from collections import Counter
from copy import deepcopy
import importlib.util
from itertools import product
from pathlib import Path
import sys

import pytest


TASK = "70f97d6b605b"
for _ancestor in Path(__file__).resolve().parents:
    _runtime = _ancestor / "shared" / "runtime"
    if (_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_runtime))
        break
    if (_ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_ancestor))
        break

from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
_sources = [ROOT / "generators" / TASK / "generator.py",
            ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"]
SOURCE = next(path for path in _sources if path.is_file())
_spec = importlib.util.spec_from_file_location("x_selector_under_test", SOURCE)
GEN = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = GEN
_spec.loader.exec_module(GEN)
CANONICAL = canonical_pairs(TASK, root=ROOT, labeled_only=True)

BANDS = ("easy", "medium", "hard")
AUXILIARY = (1, 4, 5, 6, 7, 8, 9)
X3 = frozenset({(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)})
PLUS = frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)})
X5 = frozenset({(i, i) for i in range(5)} | {(i, 4-i) for i in range(5)})


def grid(*rows):
    return [[int(value) for value in row] for row in rows]


def components(value):
    """Read maximal same-color components; no production helpers are imported."""
    seen = set()
    result = []
    for r, row in enumerate(value):
        for c, color in enumerate(row):
            if color == 0 or (r, c) in seen:
                continue
            pending = [(r, c)]
            seen.add((r, c))
            cells = set(pending)
            while pending:
                rr, cc = pending.pop()
                for dr, dc in product((-1, 0, 1), repeat=2):
                    point = (rr + dr, cc + dc)
                    if (0 <= point[0] < len(value)
                            and 0 <= point[1] < len(value[0])
                            and point not in seen
                            and value[point[0]][point[1]] == color):
                        pending.append(point)
                        seen.add(point)
                        cells.add(point)
            top = min(rr for rr, cc in cells)
            left = min(cc for rr, cc in cells)
            offsets = frozenset((rr-top, cc-left) for rr, cc in cells)
            result.append((color, frozenset(cells), offsets, top, left))
    return result


def prediction(value, mode="reference"):
    """An independently stated family of exact, deterministic rival behaviors."""
    output = deepcopy(value)
    if mode in {"all_nonzero", "all_green"}:
        for r, row in enumerate(value):
            for c, color in enumerate(row):
                if (color != 0 if mode == "all_nonzero" else color == 3):
                    output[r][c] = 2
        return output
    if mode in {"local_x", "zero_hole_bitmap"}:
        for top in range(len(value)-2):
            for left in range(len(value[0])-2):
                matches = all(value[top+r][left+c] == 3 for r, c in X3)
                if mode == "zero_hole_bitmap":
                    matches = matches and all(
                        value[top+r][left+c] == 0
                        for r, c in product(range(3), repeat=2) if (r, c) not in X3)
                if matches:
                    for r, c in X3:
                        output[top+r][left+c] = 2
        return output
    objects = components(value)
    x_colors = [color for color, _, shape, _, _ in objects if shape == X3]
    chosen_color = (min(x_colors) if mode == "minimum_x_color" else max(x_colors)) if x_colors else None
    if mode in {"most_common_x_color", "unique_majority_foreground"}:
        counts = (Counter(x_colors) if mode == "most_common_x_color" else
                  Counter(color for row in value for color in row if color != 0))
        largest = max(counts.values(), default=0)
        leaders = [color for color, count in counts.items() if count == largest]
        chosen_color = leaders[0] if len(leaders) == 1 else None
    changed_first = False
    for color, cells, offsets, top, left in objects:
        selected = color == 3 and offsets == X3
        if mode == "any_color_x":
            selected = offsets == X3
        elif mode in {"minimum_x_color", "maximum_x_color", "most_common_x_color",
                      "unique_majority_foreground"}:
            selected = color == chosen_color and offsets == X3
        elif mode == "green_size_five":
            selected = color == 3 and len(cells) == 5
        elif mode == "green_bbox_three":
            selected = (color == 3 and max(r for r, c in offsets) == 2
                        and max(c for r, c in offsets) == 2)
        elif mode == "zero_hole_component":
            selected = selected and all(
                value[top+r][left+c] == 0
                for r, c in product(range(3), repeat=2) if (r, c) not in X3)
        elif mode == "any_odd_size_x":
            size = 1 + max(r for r, c in offsets)
            shape = {(i, i) for i in range(size)} | {(i, size-1-i) for i in range(size)}
            selected = color == 3 and size >= 3 and size % 2 == 1 and offsets == shape
        elif mode == "first_x":
            selected = selected and not changed_first
        if selected:
            changed_first = True
            for r, c in cells:
                output[r][c] = 2
    return output


def observed(value):
    objects = components(value)
    targets = [obj for obj in objects if obj[0] == 3 and obj[2] == X3]
    nonzero = [(r, c) for r, row in enumerate(value) for c, color in enumerate(row) if color]
    scene = "mixed" if any(o[0] == 3 and o[2] == X5 for o in objects) else "core"
    if scene == "mixed":
        auxiliary = {value[top+r][left+c]
                     for _, _, _, top, left in targets
                     for r, c in product(range(3), repeat=2)
                     if (r, c) not in X3 and value[top+r][left+c] != 0}
    else:
        auxiliary = {color for row in value for color in row if color not in (0, 3)}
    assert len(auxiliary) == 1, "the requested auxiliary color must be recoverable from the target hole or core plus"
    padding = min(min(r for r, c in nonzero), min(c for r, c in nonzero),
                  len(value)-1-max(r for r, c in nonzero),
                  len(value[0])-1-max(c for r, c in nonzero))
    return {"n": len(targets), "padding": padding,
            "distractor_color": next(iter(auxiliary)), "scene": scene}


def assert_mixed_contrasts(value):
    objects = components(value)
    assert any(color == 3 and shape == PLUS for color, _, shape, _, _ in objects)
    assert any(color == 3 and shape == X5 for color, _, shape, _, _ in objects)
    assert any(color in AUXILIARY and shape == X3 for color, _, shape, _, _ in objects)
    assert any(color < 3 and shape == X3 for color, _, shape, _, _ in objects)
    assert any(color > 3 and shape == X3 for color, _, shape, _, _ in objects)
    targets = [obj for obj in objects if obj[0] == 3 and obj[2] == X3]
    wrong_x_counts = Counter(color for color, _, shape, _, _ in objects
                             if color != 3 and shape == X3)
    assert sorted(wrong_x_counts.values()) == [1, len(targets) + 1]
    assert any(value[top+r][left+c] in AUXILIARY
               for _, _, _, top, left in targets
               for r, c in product(range(3), repeat=2) if (r, c) not in X3)


WITNESSES = [
    (grid("303", "030", "303"), grid("202", "020", "202")),
    (grid("030", "333", "030"), grid("030", "333", "030")),
    (grid("505", "050", "505"), grid("505", "050", "505")),
    (grid("3030", "0300", "3030", "0003"), grid("3030", "0300", "3030", "0003")),
    (grid("303", "030", "303", "003"), grid("303", "030", "303", "003")),
    (grid("343", "030", "303"), grid("242", "020", "202")),
    (grid("3034", "0300", "3030"), grid("2024", "0200", "2020")),
    (grid("333", "030", "303"), grid("333", "030", "303")),
    (grid("3030303", "0300030", "3030303"), grid("2020202", "0200020", "2020202")),
    (grid("30003", "03030", "00300", "03030", "30003"),
     grid("30003", "03030", "00300", "03030", "30003")),
]

CANONICAL_RIVALS = ("all_green", "any_color_x", "green_size_five", "green_bbox_three",
                    "local_x", "zero_hole_bitmap", "zero_hole_component", "any_odd_size_x",
                    "minimum_x_color", "maximum_x_color", "most_common_x_color")
MIXED_RIVALS = CANONICAL_RIVALS + ("first_x", "all_nonzero")
ALL_RIVALS = MIXED_RIVALS + ("unique_majority_foreground",)


def test_exact_axes_replace_dead_legacy_controls():
    assert set(GEN.AXES) == {"n", "padding", "distractor_color", "scene"}
    assert GEN.RULE_HASH == "76b666ea1233"
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.LESSON_SCHEDULE_PERIOD == 35
    assert GEN.SCHEDULE_PROFILES == ("core", "mixed")


@pytest.mark.parametrize("pair", CANONICAL, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_all_canonical_inputs_are_accepted_and_strict(pair):
    original = deepcopy(pair["input"])
    assert GEN.self_check(pair["input"]) == []
    strict = GEN.strict_canonical_like(pair["input"])
    assert strict is True or strict == []
    assert prediction(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("value,expected", WITNESSES)
def test_small_reference_lawful_component_witnesses_are_accepted(value, expected):
    original = deepcopy(value)
    assert GEN.self_check(value) == []
    assert prediction(value) == expected
    assert value == original


@pytest.mark.parametrize("band,scene,n", list(product(BANDS, ("core", "mixed"), (1, 2, 3))))
def test_every_exact_axis_combination_is_constructive_and_observable(band, scene, n):
    for padding, color in product((0, 1, 2), AUXILIARY):
        request = {"n": n, "padding": padding, "distractor_color": color, "scene": scene}
        value = GEN.generate(173, 19, difficulty=band, **request)
        original = deepcopy(value)
        assert max(len(value), len(value[0])) <= 22
        assert GEN.self_check(value) == [], (band, request)
        assert observed(value) == request, (band, request)
        assert GEN.observe_overrides(value) == request
        assert value == GEN.generate(173, 19, difficulty=band, **request)
        if scene == "mixed":
            assert_mixed_contrasts(value)
        else:
            assert any(color_ == color and shape == PLUS
                       for color_, _, shape, _, _ in components(value))
        assert value == original


@pytest.mark.parametrize("key,value", [
    ("n", 0), ("n", 4), ("n", True), ("n", 1.0), ("n", "1"),
    ("padding", -1), ("padding", 3), ("padding", False), ("padding", 1.0), ("padding", "1"),
    ("distractor_color", 0), ("distractor_color", 2), ("distractor_color", 3),
    ("distractor_color", 10), ("distractor_color", True), ("distractor_color", 4.0),
    ("distractor_color", "4"), ("scene", "unknown"), ("scene", 1),
    ("scene", True), ("typo", 1), ("grid_h", 9), ("grid_w", 9),
    ("texture", "wrong_color"), ("palette_kind", "warm"), ("palette_size", 2),
    ("position_bias", "scattered_x_pentominoes"), ("n_distinct_colors", 2),
    ("density", "sparse"),
])
def test_unknown_legacy_and_invalid_exact_values_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(17, 1, **{key: value})


@pytest.mark.parametrize("value", [None, [], [[]], [[0], [0, 1]], ["303"],
                                    [[True]], [[3.0]], [["3"]], [[None]], [[-1]], [[10]], ((0,),)])
def test_malformed_grids_return_diagnostics_without_raising(value):
    original = deepcopy(value)
    reasons = GEN.self_check(value)
    assert isinstance(reasons, list) and reasons
    assert all(isinstance(reason, str) for reason in reasons)
    assert value == original


@pytest.mark.parametrize("value", [grid("1"), grid("4"), grid("9"),
                                    grid("100", "000", "009"), grid("000", "000")])
def test_foreground_without_a_substantive_motif_is_rejected(value):
    original = deepcopy(value)
    reasons = GEN.self_check(value)
    assert isinstance(reasons, list) and reasons
    assert all(isinstance(reason, str) for reason in reasons)
    assert value == original


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_teaches_contrasts_and_preserves_canonical_profiles(band):
    colors = []
    seen_mixed = []
    profiles = {(len(p["input"]), len(p["input"][0]),
                 frozenset(color for row in p["input"] for color in row)) for p in CANONICAL}
    profile_hits = 0
    for index in range(100):
        value = GEN.generate(137, index, difficulty=band)
        assert GEN.self_check(value) == [], (band, index)
        stats = observed(value)
        assert GEN.observe_overrides(value) == stats
        assert stats["scene"] == ("mixed" if index % 5 in (1, 3) else "core")
        assert GEN.schedule_profile(137, index, band) == stats["scene"]
        if index % 5 in (1, 3):
            assert stats["n"] >= 2
            assert_mixed_contrasts(value)
            colors.append(stats["distractor_color"])
            seen_mixed.append(value)
            expected = prediction(value)
            for name in MIXED_RIVALS:
                assert prediction(value, name) != expected, (band, index, name)
        else:
            assert stats["n"] == (2 if index % 5 == 4 else 1)
            assert stats["padding"] == 0 and stats["distractor_color"] == 4
            assert tuple(sorted((len(value), len(value[0])))) == {
                0: (7, 7), 2: (7, 8), 4: (8, 8)}[index % 5]
            if stats["n"] == 1:
                counts = Counter(color for row in value for color in row if color)
                assert dict(counts) == {3: 5, 4: 5}
                assert prediction(value, "unique_majority_foreground") != prediction(value)
            strict = GEN.strict_canonical_like(value)
            assert strict is True or strict == []
            profile = (len(value), len(value[0]), frozenset(color for row in value for color in row))
            profile_hits += profile in profiles
    assert profile_hits > 0
    for start in range(len(colors)-6):
        assert set(colors[start:start+7]) == set(AUXILIARY), (band, start, colors[start:start+7])
    assert all(a != b for a, b in zip(seen_mixed, seen_mixed[1:]))


@pytest.mark.parametrize("seed,band", list(product((0, 1, 137), BANDS)))
def test_every_five_draw_window_survives_duplicate_filter_and_one_pair_holdout(seed, band):
    # Thirty-nine draws cover every start phase in the full 35-position period.
    # Reuse draws so the 35 overlapping windows do not resample the generator.
    values = [GEN.generate(seed, index, difficulty=band) for index in range(39)]
    observations = [observed(value) for value in values]
    for start in range(35):
        window = values[start:start+5]
        stats = observations[start:start+5]
        assert len({tuple(map(tuple, value)) for value in window}) == 5, (seed, band, start)
        assert Counter(item["scene"] for item in stats) == {"core": 3, "mixed": 2}
        assert sum(item["scene"] == "core" and item["n"] == 1 for item in stats) == 2
        assert sum(item["scene"] == "core" and item["n"] == 2 for item in stats) == 1
        assert len({item["distractor_color"] for item in stats if item["scene"] == "mixed"}) == 2
        # Each possible query leaves a majority-color tie and a full contrast.
        for holdout in range(5):
            demos = stats[:holdout] + stats[holdout+1:]
            assert any(item["scene"] == "core" and item["n"] == 1 for item in demos)
            assert any(item["scene"] == "mixed" and item["n"] >= 2 for item in demos)


def test_rival_declarations_have_the_promised_behaviors_and_canonical_scope():
    inputs = [pair["input"] for pair in CANONICAL] + [value for value, _ in WITNESSES]
    # A single scene with X colors on both sides of 3 distinguishes minimum,
    # maximum, and color-blind selection; isolated wrong-color Xs cannot.
    inputs.append(grid("10103030505", "01000300050", "10103030505"))
    # Two low-color Xs and one each green/high-color X expose a unique most
    # frequent X-component color distinct from the preceding all-color tie.
    inputs.append(grid("101010103030505", "010001000300050", "101010103030505"))

    def signature(fn):
        results = []
        for value in inputs:
            original = deepcopy(value)
            result = fn(value)
            assert value == original, "rivals must not mutate their inputs"
            results.append(result)
        return results

    for attribute, modes in (("SEMANTIC_RIVALS", ALL_RIVALS),
                             ("LESSON_COMPETITORS", ALL_RIVALS),
                             ("CANONICAL_SHORTCUTS", CANONICAL_RIVALS)):
        declarations = getattr(GEN, attribute)
        assert isinstance(declarations, dict) and declarations
        assert len(declarations) == len(modes)
        actual = [signature(fn) for fn in declarations.values()]
        for mode in modes:
            assert signature(lambda value, m=mode: prediction(value, m)) in actual, (attribute, mode)
        if attribute == "CANONICAL_SHORTCUTS":
            for fn in declarations.values():
                assert all(fn(pair["input"]) == pair["output"] for pair in CANONICAL)

