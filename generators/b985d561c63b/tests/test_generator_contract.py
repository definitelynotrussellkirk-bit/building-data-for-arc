"""Independent behavioral regressions for the template-stamping generator.

The oracle in this test file is diagnostic only; production labels continue to
come from the unchanged canonical Racket rule.

Explicit None is the inherited unpinned sentinel (GenCtx._override in
shared/runtime/puzzle_generators/base.py), so it must behave like omission.
Other malformed values, including bool and integral float values, are errors.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared/runtime"))
SPEC = importlib.util.spec_from_file_location(
    "b985d561c63b_contract_subject", REPO / "generators/b985d561c63b/generator.py"
)
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)

BANDS = (None, "easy", "medium", "hard")
RULE_HASH = "c86839f15a5d"
INT_DOMAINS = {
    "grid_h": tuple(range(9, 23)), "grid_w": tuple(range(9, 23)),
    "template_h": tuple(range(2, 6)), "template_w": tuple(range(2, 6)),
    "region_count": tuple(range(1, 5)), "palette_size": (2, 3),
    "extra_rows": (0, 1, 2), "extra_cols": (0, 1, 2),
}
DOMAINS = {**INT_DOMAINS, "template_style": ("dense", "punctured")}


def _components(grid, predicate):
    """Test-owned four-neighbor flood fill, independent of generator helpers."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
              if predicate(value)}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component, pending = {start}, [start]
        while pending:
            r, c = pending.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        components.append(component)
    return components


def _bbox(cells):
    rows, cols = zip(*cells)
    r0, c0 = min(rows), min(cols)
    return r0, c0, max(rows) - r0 + 1, max(cols) - c0 + 1


def _measure(grid):
    """Recover all public controls from pixels without trusting module metadata."""
    assert isinstance(grid, list) and grid and isinstance(grid[0], list) and grid[0]
    h, w = len(grid), len(grid[0])
    assert all(isinstance(row, list) and len(row) == w for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    sources = _components(grid, lambda value: value not in (0, 5))
    assert len(sources) == 1, "colored source must be four-connected"
    source = sources[0]
    sr, sc, th, tw = _bbox(source)
    template = [row[sc:sc + tw] for row in grid[sr:sr + th]]
    assert all(value != 5 for row in template for value in row)
    palette = {grid[r][c] for r, c in source}
    targets = _components(grid, lambda value: value == 5)
    assert targets
    target_boxes, padding = [], set()
    for target in targets:
        tr, tc, rh, rw = _bbox(target)
        assert len(target) == rh * rw, "gray target must fill its rectangle"
        assert rh >= th and rw >= tw, "gray target must contain translated template bbox"
        padding.add((rh - th, rw - tw))
        target_boxes.append((tr, tc, rh, rw))
    assert len(padding) == 1, "targets must expose a single pair of padding controls"
    extra_rows, extra_cols = padding.pop()
    boxes = [(sr, sc, th, tw), *target_boxes]
    for i, (ar, ac, ah, aw) in enumerate(boxes):
        for br, bc, bh, bw in boxes[i + 1:]:
            assert ar + ah <= br or br + bh <= ar or ac + aw <= bc or bc + bw <= ac
    observation = {
        "grid_h": h, "grid_w": w, "template_h": th, "template_w": tw,
        "region_count": len(targets), "palette_size": len(palette),
        "template_style": "punctured" if any(0 in row for row in template) else "dense",
        "extra_rows": extra_rows, "extra_cols": extra_cols,
    }
    assert all(value in DOMAINS[axis] for axis, value in observation.items()), observation
    return observation, (sr, sc, th, tw), tuple(target_boxes), frozenset(palette)


def _oracle(grid, *, copy_zero=True, clear_gray=False):
    """Whole-crop top-left stamping; rival modes are deliberately incorrect."""
    colored = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
               if value not in (0, 5)}
    sr, sc, th, tw = _bbox(colored)
    crop = [row[sc:sc + tw] for row in grid[sr:sr + th]]
    targets = _components(grid, lambda value: value == 5)
    out = [[0 if clear_gray and value == 5 else value for value in row] for row in grid]
    for target in targets:
        tr, tc, _, _ = _bbox(target)
        for dr, row in enumerate(crop):
            for dc, value in enumerate(row):
                if copy_zero or value != 0:
                    out[tr + dr][tc + dc] = value
    return out


def _scene(template=None, *, h=12, w=14, source=(1, 1), targets=None):
    template = template or [[2, 3, 2], [3, 2, 3], [2, 3, 2]]
    targets = targets if targets is not None else ((1, 8, 3, 3), (7, 2, 3, 3))
    grid = [[0] * w for _ in range(h)]
    for dr, row in enumerate(template):
        for dc, value in enumerate(row):
            grid[source[0] + dr][source[1] + dc] = value
    for r0, c0, rh, rw in targets:
        for r in range(r0, r0 + rh):
            for c in range(c0, c0 + rw):
                grid[r][c] = 5
    return grid


def _hole_and_surplus_scene():
    # Connected support, an empty top-left bbox corner, and all four canvas edges.
    return _scene([[0, 2, 2, 2], [3, 3, 0, 2], [3, 0, 0, 2]],
                  h=10, w=12, source=(0, 0), targets=((0, 6, 4, 6), (6, 0, 4, 6)))


@pytest.fixture(scope="module")
def canonical_rows():
    rows = []
    with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            if "b985d561c63b" in line:
                row = json.loads(line)
                if row.get("task_id") == "b985d561c63b":
                    rows.append(row)
    assert rows, "public canonical task record is required"
    return rows


@pytest.fixture(scope="module")
def canonical_pairs(canonical_rows):
    pairs = {}
    for row in canonical_rows:
        for split in ("train", "test"):
            entries = row.get(split, [])
            entries = [entries] if isinstance(entries, dict) else entries
            for entry in entries:
                pair = {key: [[int(value) for value in cells] for cells in entry[key]]
                        for key in ("input", "output")}
                key = json.dumps(pair["input"])
                if key in pairs:
                    assert pairs[key]["output"] == pair["output"]
                pairs[key] = pair
    assert len(pairs) == 3, "the augmented row reorders the same three public pairs"
    return list(pairs.values())


@pytest.mark.parametrize("overrides", [
    {"unknown_axis": 1}, {"palette_kind": "warm"}, {"texture": "warm"},
    {"position_bias": "random"}, {"n_distinct_colors": 3},
])
def test_unknown_and_removed_axes_raise(overrides):
    with pytest.raises(ValueError):
        gen.generate(17, 0, **overrides)


@pytest.mark.parametrize("band", BANDS)
def test_formerly_rejected_grid_height_nine_is_legal_in_every_band(band):
    grid = gen.generate(17, 0, difficulty=band, grid_h=9)
    assert len(grid) == 9
    assert gen.self_check(grid, difficulty=band) == []


@pytest.mark.parametrize("value", [True, False, 2.0])
def test_self_check_rejects_numeric_lookalikes(value):
    grid = [[0] * 12 for _ in range(12)]
    for r in range(3):
        for c in range(3):
            grid[r][c] = 2 + ((r + c) % 2)
            grid[r + 6][c + 6] = 5
    grid[5][0] = value
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) for error in errors)


def test_rule_hash_and_public_axis_contract(canonical_rows):
    hashes = {hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
              for row in canonical_rows}
    assert hashes == {RULE_HASH}
    assert gen.RULE_HASH == RULE_HASH
    assert set(gen.AXES) == set(DOMAINS)
    for axis, values in INT_DOMAINS.items():
        assert gen.AXES[axis]["type"] == "int"
        assert gen.AXES[axis]["valid"] == f"{values[0]}..{values[-1]}"
    assert gen.AXES["template_style"]["type"] == "str"
    assert set(gen.AXES["template_style"]["valid"].split("|")) == {"dense", "punctured"}


@pytest.mark.parametrize("axis", tuple(INT_DOMAINS))
@pytest.mark.parametrize("value", [True, False, 3.0, "3", [], {}])
def test_integer_pins_reject_coercion_and_malformed_types(axis, value):
    with pytest.raises(ValueError):
        gen.generate(19, 1, **{axis: value})


@pytest.mark.parametrize("axis", tuple(INT_DOMAINS))
@pytest.mark.parametrize("edge", ("below", "above"))
def test_integer_pins_reject_values_outside_published_domain(axis, edge):
    values = INT_DOMAINS[axis]
    value = values[0] - 1 if edge == "below" else values[-1] + 1
    with pytest.raises(ValueError):
        gen.generate(19, 1, **{axis: value})


@pytest.mark.parametrize("value", [True, 1, 2.0, "holes", "", [], {}])
def test_template_style_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        gen.generate(19, 1, template_style=value)


@pytest.mark.parametrize("axis", tuple(DOMAINS))
def test_none_override_is_the_inherited_unpinned_sentinel(axis):
    for band in BANDS:
        for seed, index in ((0, 0), (17, 3)):
            assert gen.generate(seed, index, difficulty=band, **{axis: None}) == (
                gen.generate(seed, index, difficulty=band)
            )


@pytest.mark.parametrize("value", [None, [], [[]], 7, "grid", {}, [None],
                                       [[0], 7], [[0], [0, 0]]])
def test_malformed_grid_container_returns_diagnostics(value):
    errors = gen.self_check(value)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) for error in errors)


@pytest.mark.parametrize("value", [None, "2", [], {}, -1, 10])
def test_malformed_grid_cell_returns_diagnostics(value):
    grid = _scene()
    grid[5][0] = value
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) for error in errors)


def _malformed_scene(kind):
    grid = _scene()
    if kind == "missing_source":
        grid = [[0 if value not in (0, 5) else value for value in row] for row in grid]
    elif kind == "missing_regions":
        grid = [[0 if value == 5 else value for value in row] for row in grid]
    elif kind == "disconnected_source":
        grid[2][1:4] = [0, 0, 0]
    elif kind == "diagonal_source":
        for r in range(1, 4):
            for c in range(1, 4):
                grid[r][c] = (2 if r % 2 else 3) if r == c else 0
    elif kind == "nonrectangular_target":
        grid[1][8] = 0
    elif kind == "undersized_target":
        grid[3][8:11] = [0, 0, 0]
    elif kind == "unequal_padding":
        grid[4][8:11] = [5, 5, 5]
    elif kind == "gray_inside_source_bbox":
        grid[2][2] = 5
    elif kind == "target_touches_source":
        for r in range(1, 4):
            grid[r][4:7] = [5, 5, 5]
    elif kind == "overlap":
        grid[2][2:9] = [5] * 7
    elif kind == "four_source_colors":
        grid[1][1:3] = [4, 6]
    elif kind == "five_regions":
        grid = _scene(h=22, w=22, source=(0, 0),
                      targets=((0, 6, 3, 3), (0, 12, 3, 3), (6, 0, 3, 3),
                               (6, 6, 3, 3), (6, 12, 3, 3)))
    elif kind == "oversized_grid":
        grid = _scene(h=23)
    elif kind == "oversized_template":
        grid = _scene([[2, 3, 2]] * 6, h=22, w=22, source=(0, 0),
                      targets=((0, 8, 6, 3),))
    else:
        raise AssertionError(kind)
    return grid


@pytest.mark.parametrize("kind", [
    "missing_source", "missing_regions", "disconnected_source", "diagonal_source",
    "nonrectangular_target", "undersized_target", "unequal_padding", "gray_inside_source_bbox",
    "target_touches_source", "overlap", "four_source_colors", "five_regions",
    "oversized_grid", "oversized_template",
])
def test_self_check_rejects_invalid_scene_geometry(kind):
    grid = _malformed_scene(kind)
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors, kind
    assert all(isinstance(error, str) for error in errors)


def test_public_canonical_pairs_are_admitted_and_match_independent_oracle(canonical_pairs):
    shapes, counts = set(), set()
    for pair in canonical_pairs:
        grid = pair["input"]
        obs, _, _, _ = _measure(grid)
        assert _oracle(grid) == pair["output"]
        assert gen.strict_canonical_like(grid) == []
        for band in BANDS:
            assert gen.self_check(grid, difficulty=band) == []
        assert gen.observe_overrides(grid) == obs
        shapes.add((obs["template_h"], obs["template_w"]))
        counts.add(obs["region_count"])
    assert shapes == {(3, 3), (3, 4), (4, 3)}
    assert counts == {2, 3}


def test_holes_are_copied_as_zero_and_gray_surplus_is_retained():
    grid = _hole_and_surplus_scene()
    original = copy.deepcopy(grid)
    obs, _, target_boxes, _ = _measure(grid)
    assert obs == {"grid_h": 10, "grid_w": 12, "template_h": 3, "template_w": 4,
                   "region_count": 2, "palette_size": 2, "template_style": "punctured",
                   "extra_rows": 1, "extra_cols": 2}
    expected = _oracle(grid)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == obs
    assert gen.strict_canonical_like(grid)
    changed = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
               if value != expected[r][c]}
    assert len(changed) == 24
    assert sum(value == 5 for row in expected for value in row) == 24
    assert sum(value == 2 for row in expected for value in row) == 15
    assert sum(value == 3 for row in expected for value in row) == 9
    for tr, tc, rh, rw in target_boxes:
        for dr, dc in ((0, 0), (1, 2), (2, 1), (2, 2)):
            assert grid[tr + dr][tc + dc] == 5 and expected[tr + dr][tc + dc] == 0
        for dr in range(rh):
            for dc in range(rw):
                if dr >= 3 or dc >= 4:
                    assert expected[tr + dr][tc + dc] == 5
    assert grid == original


def test_semantic_helpers_expose_and_refute_canonical_shortcuts(canonical_pairs):
    extension = _hole_and_surplus_scene()
    expected = _oracle(extension)
    rivals = {"nonzero_only": _oracle(extension, copy_zero=False),
              "clear_all_gray": _oracle(extension, clear_gray=True)}
    for name, wrong in rivals.items():
        assert wrong != expected
        for mapping_name in ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
            mapping = getattr(gen, mapping_name)
            assert name in mapping and callable(mapping[name])
            original = copy.deepcopy(extension)
            assert mapping[name](extension) == wrong
            assert extension == original
            assert all(mapping[name](pair["input"]) == pair["output"] for pair in canonical_pairs)
    for name in ("template_zero", "retained_gray"):
        assert gen.SEMANTIC_WITNESSES[name](extension) is True
        assert all(gen.SEMANTIC_WITNESSES[name](pair["input"]) is False
                   for pair in canonical_pairs)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("axis", tuple(DOMAINS))
def test_every_valid_single_axis_pin_is_honored(band, axis):
    # This is a union of one-dimensional sweeps, not a Cartesian parameter grid.
    for value in DOMAINS[axis]:
        for seed, index in ((0, 0), (17, 3)):
            grid = gen.generate(seed, index, difficulty=band, **{axis: value})
            obs, _, _, _ = _measure(grid)
            assert obs[axis] == value, (band, axis, value, seed, index, obs)
            assert gen.observe_overrides(grid) == obs
            assert gen.self_check(grid, difficulty=band) == []


PAIR_PINS = (
    {"grid_h": 9, "grid_w": 9}, {"grid_h": 9, "template_h": 5},
    {"grid_w": 9, "template_w": 5}, {"grid_h": 9, "region_count": 4},
    {"grid_w": 9, "region_count": 4}, {"template_h": 5, "template_w": 5},
    {"template_h": 2, "template_w": 2}, {"region_count": 4, "palette_size": 3},
    {"template_style": "punctured", "palette_size": 3},
    {"extra_rows": 2, "extra_cols": 2}, {"grid_h": 9, "extra_rows": 2},
    {"grid_w": 9, "extra_cols": 2}, {"template_h": 5, "extra_rows": 2},
    {"template_w": 5, "extra_cols": 2}, {"grid_h": 22, "grid_w": 22},
)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("pins", PAIR_PINS)
def test_compatible_pair_edges_are_honored(band, pins):
    grid = gen.generate(911, 3, difficulty=band, **pins)
    obs, _, _, _ = _measure(grid)
    assert all(obs[axis] == value for axis, value in pins.items())
    assert gen.observe_overrides(grid) == obs
    assert gen.self_check(grid, difficulty=band) == []


@pytest.mark.parametrize("pins", [
    {"grid_h": 22, "grid_w": 22, "template_h": 4, "template_w": 4, "region_count": 4,
     "palette_size": 3, "extra_rows": 2, "extra_cols": 2, "template_style": "punctured"},
    {"grid_h": 9, "grid_w": 22, "template_h": 5, "template_w": 2, "region_count": 4,
     "palette_size": 3, "extra_rows": 0, "extra_cols": 1, "template_style": "dense"},
    {"grid_h": 22, "grid_w": 9, "template_h": 2, "template_w": 5, "region_count": 4,
     "palette_size": 2, "extra_rows": 1, "extra_cols": 0, "template_style": "dense"},
    {"grid_h": 9, "grid_w": 9, "template_h": 2, "template_w": 2, "region_count": 4,
     "palette_size": 3, "extra_rows": 0, "extra_cols": 0, "template_style": "punctured"},
])
def test_fully_pinned_geometry_and_palette_are_exact(pins):
    for band in BANDS:
        grid = gen.generate(997, 1, difficulty=band, **pins)
        assert _measure(grid)[0] == pins
        assert gen.observe_overrides(grid) == pins
        assert gen.self_check(grid, difficulty=band) == []


@pytest.mark.parametrize("pins", [
    {"grid_h": 9, "grid_w": 9, "template_h": 5, "template_w": 5, "region_count": 4},
    {"grid_h": 9, "grid_w": 9, "template_h": 5, "region_count": 4},
    {"grid_h": 9, "grid_w": 9, "template_h": 5, "template_w": 5,
     "region_count": 1, "extra_rows": 2, "extra_cols": 2},
])
def test_impossible_geometry_reports_multiple_conflicting_axes(pins):
    for band in BANDS:
        with pytest.raises(ValueError) as captured:
            gen.generate(17, 0, difficulty=band, **pins)
        conflicts = getattr(captured.value, "incompatible_axes", ())
        assert len(conflicts) >= 2, str(captured.value)
        assert set(conflicts) <= set(DOMAINS)


@pytest.mark.parametrize("band", BANDS)
def test_palette_size_three_means_three_realized_source_colors(band):
    for seed in range(24):
        grid = gen.generate(seed, seed % 5, difficulty=band, palette_size=3,
                            template_h=2, template_w=2)
        assert _measure(grid)[0]["palette_size"] == 3


@pytest.mark.parametrize("band", BANDS)
def test_repeated_calls_are_deterministic_and_independent_of_call_order(band):
    for seed, index in ((0, 0), (1, 1), (17, 3), (997, 100)):
        first = gen.generate(seed, index, difficulty=band)
        saved = copy.deepcopy(first)
        gen.generate(seed + 11, index + 7, difficulty=band, palette_size=3)
        assert gen.generate(seed, index, difficulty=band) == saved
        first[0][0] = (first[0][0] + 1) % 10
        assert gen.generate(seed, index, difficulty=band) == saved


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_matches_pixels_and_alternates_with_seed_phase(band):
    assert tuple(gen.SCHEDULE_PROFILES) == ("core", "extension")
    first_profiles = set()
    for seed in range(12):
        previous = None
        for index in range(8):
            profile = gen.schedule_profile(seed, index, difficulty=band)
            assert profile in ("core", "extension") and profile != previous
            assert profile == gen.schedule_profile(seed, index, difficulty=band)
            if index == 0:
                first_profiles.add(profile)
            previous = profile
            grid = gen.generate(seed, index, difficulty=band)
            obs, _, _, _ = _measure(grid)
            assert gen.observe_overrides(grid) == obs
            assert gen.self_check(grid, difficulty=band) == []
            if profile == "core":
                assert (obs["grid_h"], obs["grid_w"]) == (10, 10)
                assert (obs["template_h"], obs["template_w"]) in ((3, 3), (3, 4), (4, 3))
                assert obs["region_count"] in (2, 3) and obs["palette_size"] == 2
                assert obs["template_style"] == "dense"
                assert obs["extra_rows"] == obs["extra_cols"] == 0
                assert gen.strict_canonical_like(grid) == []
            else:
                assert obs["template_style"] == "punctured"
                assert obs["extra_rows"] + obs["extra_cols"] >= 1
                assert gen.strict_canonical_like(grid)
    assert first_profiles == {"core", "extension"}, "fixed query indices need both profiles across seeds"


@pytest.mark.parametrize("band", BANDS)
def test_three_consecutive_defaults_contain_both_semantic_witnesses(band):
    for seed in (0, 17, 997):
        for start in (0, 1, 2, 7, 13, 41, 100):
            observations, outputs = [], []
            for index in range(start, start + 3):
                grid = gen.generate(seed, index, difficulty=band)
                observations.append(_measure(grid)[0])
                outputs.append((grid, _oracle(grid)))
            assert any(obs["template_style"] == "punctured" for obs in observations)
            assert any(obs["extra_rows"] + obs["extra_cols"] > 0 for obs in observations)
            assert any(_oracle(grid, copy_zero=False) != output for grid, output in outputs)
            assert any(_oracle(grid, clear_gray=True) != output for grid, output in outputs)


@pytest.mark.parametrize("band", BANDS)
def test_default_variation_survives_in_every_difficulty_band(band):
    dimensions, shapes, palettes, source_positions, target_layouts, counts = (set() for _ in range(6))
    palette_sizes = set()
    for seed in range(8):
        for index in range(8):
            obs, source, targets, palette = _measure(gen.generate(seed, index, difficulty=band))
            dimensions.add((obs["grid_h"], obs["grid_w"]))
            shapes.add((obs["template_h"], obs["template_w"]))
            palettes.add(palette)
            source_positions.add(source[:2])
            target_layouts.add(targets)
            counts.add(obs["region_count"])
            palette_sizes.add(obs["palette_size"])
    assert len(dimensions) >= 4 and len(shapes) >= 4
    assert len(palettes) >= 4 and len(source_positions) >= 4 and len(target_layouts) >= 4
    assert len(counts) >= 2 and palette_sizes == {2, 3}
