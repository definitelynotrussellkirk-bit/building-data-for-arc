"""Regression and semantic contract tests for 8d7d1364cf11."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "8d7d1364cf11"
RULE_HASH = "0a9706fafc20"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed_scalars(bad_seed):
    with pytest.raises(TypeError, match="seed must be an integer"):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, -1])
def test_generate_rejects_invalid_sample_index_scalars(bad_index):
    error = TypeError if type(bad_index) is not int else ValueError
    with pytest.raises(error, match="sample_index must be"):
        gen.generate(991, bad_index)


@pytest.mark.parametrize("bad_difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_generate_rejects_unknown_difficulty_scalars(bad_difficulty):
    with pytest.raises(ValueError, match="difficulty must be"):
        gen.generate(991, 0, difficulty=bad_difficulty)


def _components(grid):
    """Independent row-major 8-connected non-background components."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 4 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c, grid[r][c]))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if (
                            0 <= nr < h
                            and 0 <= nc < w
                            and grid[nr][nc] != 4
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            result.append(sorted(cells))
    return result


def _scene(grid):
    comps = _components(grid)
    shapes = [comp for comp in comps if len(comp) > 1]
    dots = [comp[0] for comp in comps if len(comp) == 1]
    matches = {}
    for si, shape in enumerate(shapes):
        for r, c, color in shape:
            matches.setdefault(color, []).append((si, r, c))
    active = []
    decoys = []
    per_shape = Counter()
    for r, c, color in dots:
        found = matches.get(color, [])
        if len(found) == 1:
            si, ar, ac = found[0]
            active.append((r, c, color, si, ar, ac))
            per_shape[si] += 1
        elif not found:
            decoys.append((r, c, color))
        else:
            active.append((r, c, color, None, None, None))
    return shapes, dots, matches, active, decoys, per_shape


def _oracle(grid):
    """Independent solver on the intended unique-anchor domain."""
    h, w = len(grid), len(grid[0])
    shapes, dots, matches, _active, _decoys, _counts = _scene(grid)
    out = [[4] * w for _ in range(h)]
    for dr, dc, color in dots:
        found = matches.get(color, [])
        if not found:
            continue
        assert len(found) == 1, f"ambiguous anchor color {color}: {found}"
        si, ar, ac = found[0]
        for r, c, value in shapes[si]:
            nr, nc = dr + r - ar, dc + c - ac
            if 0 <= nr < h and 0 <= nc < w:
                out[nr][nc] = value
    return out


def _bbox_anchor(shape):
    return min(r for r, _c, _v in shape), min(c for _r, c, _v in shape)


def _dihedral(grid):
    cur = deepcopy(grid)
    for _ in range(4):
        yield cur
        yield [row[::-1] for row in cur]
        cur = [list(row) for row in zip(*cur[::-1])]


@pytest.mark.parametrize("pair", canonical_pairs(TASK, root=find_root(__file__), labeled_only=True))
def test_canonical_pairs_are_accepted_and_oracle_matches(pair):
    assert gen.RULE_HASH == RULE_HASH
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert _oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_joint_overrides_are_honored_in_every_band(band):
    options = dict(
        grid_h=16,
        grid_w=17,
        n_shapes=3,
        copies_per_shape=2,
        n_decoy_dots=3,
        shape_variant=5,
        shared_body=False,
    )
    grid = gen.generate(17, 9, difficulty=band, **options)
    shapes, dots, matches, active, decoys, per_shape = _scene(grid)
    assert (len(grid), len(grid[0])) == (16, 17)
    assert len(shapes) == options["n_shapes"]
    assert len(decoys) == options["n_decoy_dots"]
    assert len(active) == options["n_shapes"] * options["copies_per_shape"]
    assert set(per_shape.values()) == {options["copies_per_shape"]}
    assert all(len(matches[color]) == 1 for _r, _c, color, *_ in active)
    body_colors = []
    for si, shape in enumerate(shapes):
        active_colors = {color for _r, _c, color, mapped, *_ in active if mapped == si}
        bodies = {value for _r, _c, value in shape if value not in active_colors}
        assert len(bodies) == 1
        body_colors.append(next(iter(bodies)))
    assert len(set(body_colors)) == options["n_shapes"]
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []


@pytest.mark.parametrize(
    "name,value",
    [
        ("typo", 1),
        ("grid_h", 15),
        ("grid_w", 25),
        ("n_shapes", 1),
        ("n_shapes", 4),
        ("copies_per_shape", 0),
        ("copies_per_shape", 3),
        ("n_decoy_dots", 0),
        ("n_decoy_dots", 4),
        ("shape_variant", -1),
        ("shape_variant", 6),
        ("shared_body", 1),
        ("shared_body", "true"),
        ("grid_h", True),
        ("n_shapes", 2.0),
    ],
)
def test_invalid_overrides_are_rejected(name, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{name: value})


def test_each_advertised_axis_changes_observable_pixels():
    base = dict(
        grid_h=18,
        grid_w=18,
        n_shapes=2,
        copies_per_shape=1,
        n_decoy_dots=1,
        shape_variant=0,
        shared_body=True,
    )
    alternatives = {
        "grid_h": 19,
        "grid_w": 19,
        "n_shapes": 3,
        "copies_per_shape": 2,
        "n_decoy_dots": 3,
        "shape_variant": 5,
        "shared_body": False,
    }
    original = gen.generate(91, 4, **base)
    for name, value in alternatives.items():
        changed = gen.generate(91, 4, **(base | {name: value}))
        assert changed != original, name
        assert gen.self_check(changed) == [], name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_has_unique_anchors_decoys_and_varied_source_positions(band):
    anchors = set()
    quadrants = set()
    inputs = set()
    core_profiles = 0
    for index in range(160):
        grid = gen.generate(1000 + index, index, difficulty=band)
        assert grid == gen.generate(1000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        shapes, _dots, matches, active, decoys, per_shape = _scene(grid)
        assert len(shapes) in (2, 3)
        assert decoys
        assert all(mapped is not None for *_head, mapped, _ar, _ac in active)
        assert all(len(matches[color]) == 1 for _r, _c, color, *_ in active)
        assert set(per_shape) == set(range(len(shapes)))
        h, w = len(grid), len(grid[0])
        core_profiles += (h, w) == (18, 18) and {1, 3, 4, 5, 6} <= {v for row in grid for v in row}
        for shape in shapes:
            r, c = _bbox_anchor(shape)
            anchors.add((r, c))
            quadrants.add((r >= h // 2, c >= w // 2))
        inputs.add(tuple(tuple(row) for row in grid))
    assert len(anchors) >= 45
    assert quadrants == {(False, False), (False, True), (True, False), (True, True)}
    assert len(inputs) >= 155
    assert core_profiles >= 20



def test_difficulty_bands_enter_generation_draws():
    for seed, sample_index in ((5, 1), (19, 7), (101, 13)):
        grids = [
            gen.generate(seed, sample_index, difficulty=band)
            for band in ("easy", "medium", "hard")
        ]
        assert len({tuple(map(tuple, grid)) for grid in grids}) == 3
        assert all(gen.self_check(grid, difficulty=band) == [] for grid, band in zip(grids, ("easy", "medium", "hard")))


def test_ignore_productive_color_five_shortcut_fits_canonical_but_broad_profile_refutes_it():
    rival = gen.SEMANTIC_RIVALS["ignore_productive_color5"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs(TASK, root=find_root(__file__), labeled_only=True))
    for index in (1, 2, 3, 5, 6, 7):
        grid = gen.generate(700 + index, index, difficulty="medium")
        active_colors = {item[2] for item in gen._scene(grid)["active"]}
        assert 5 in active_colors
        assert rival(grid) != _oracle(grid)

def test_declared_rivals_are_real_counterexamples_on_generated_inputs():
    expected = {"preserve_sources", "top_left_alignment", "first_template_only", "stamp_decoys"}
    assert expected <= set(gen.SEMANTIC_RIVALS)
    assert expected <= set(gen.LESSON_COMPETITORS)
    for index in range(32):
        grid = gen.generate(73, index, n_shapes=3, copies_per_shape=2, n_decoy_dots=2)
        intended = _oracle(grid)
        assert intended != grid
        for name in expected:
            assert gen.SEMANTIC_RIVALS[name](grid) != intended, (index, name)
        pair = {"input": grid, "output": intended}
        assert gen.lesson_identifiable([pair], pair) == []


def test_semantic_witnesses_fire_and_map_to_rivals():
    assert set(gen.WITNESS_RIVALS) <= set(gen.SEMANTIC_WITNESSES)
    witnessed = Counter()
    for index in range(24):
        grid = gen.generate(812, index, n_shapes=3, copies_per_shape=2, n_decoy_dots=2)
        intended = _oracle(grid)
        for witness, rivals in gen.WITNESS_RIVALS.items():
            if not gen.SEMANTIC_WITNESSES[witness](grid):
                continue
            witnessed[witness] += 1
            names = [rivals] if isinstance(rivals, str) else list(rivals)
            assert any(gen.SEMANTIC_RIVALS[name](grid) != intended for name in names)
    assert set(witnessed) == set(gen.WITNESS_RIVALS)
    assert all(count > 0 for count in witnessed.values())


def test_global_dihedral_equivariance_of_domain_and_oracle():
    for index in range(8):
        grid = gen.generate(903, index, n_shapes=3, copies_per_shape=2, n_decoy_dots=2)
        expected = _oracle(grid)
        for transformed, transformed_out in zip(_dihedral(grid), _dihedral(expected)):
            assert gen.self_check(transformed) == []
            assert gen.strict_canonical_like(transformed) == []
            assert _oracle(transformed) == transformed_out


def test_validator_rejects_duplicate_anchor_and_missing_decoys():
    grid = gen.generate(41, 7, n_shapes=2, copies_per_shape=1, n_decoy_dots=1)
    shapes, _dots, _matches, active, decoys, _per_shape = _scene(grid)
    _dr, _dc, color, si, _ar, _ac = active[0]
    # Turn another body cell in the same source into the active accent color.
    r, c, _old = next(cell for cell in shapes[si] if cell[2] != color)
    duplicate = deepcopy(grid)
    duplicate[r][c] = color
    assert gen.self_check(duplicate)
    # Remove every absent-color singleton, leaving no negative teaching example.
    no_decoys = deepcopy(grid)
    for r, c, _color in decoys:
        no_decoys[r][c] = 4
    assert gen.self_check(no_decoys)


@pytest.mark.parametrize("bad", [None, [], [[]], [[4], [4, 4]], [[True] * 18 for _ in range(18)]])
def test_malformed_inputs_return_diagnostics_not_exceptions(bad):
    assert gen.self_check(bad)
    assert gen.strict_canonical_like(bad)


def test_observe_overrides_recovers_exact_joint_controls():
    options = dict(
        grid_h=20,
        grid_w=21,
        n_shapes=3,
        copies_per_shape=2,
        n_decoy_dots=3,
        shape_variant=4,
        shared_body=False,
    )
    grid = gen.generate(551, 13, difficulty="easy", **options)
    assert gen.observe_overrides(grid) == options
