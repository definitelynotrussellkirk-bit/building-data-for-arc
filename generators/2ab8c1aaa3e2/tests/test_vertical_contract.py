"""Portable regression tests: run through the task_tests stage, not root pytest."""
from collections import Counter
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = '2ab8c1aaa3e2'
HOME = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('vertical_markers_under_test', HOME / 'generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def groups(grid):
    return [Counter(row[c] for row in grid if row[c]) for c in range(len(grid[0]))]


def oracle(grid):
    """Independent test oracle. Dataset labels still come from Racket."""
    out = [row[:] for row in grid]
    for c in range(len(grid[0])):
        # Racket traverses colors in first-appearance order on the original grid.
        colors = list(dict.fromkeys(row[c] for row in grid if row[c]))
        for color in colors:
            hits = [r for r in range(len(grid)) if grid[r][c] == color]
            if len(hits) == 2:
                for r in range(hits[0], hits[1] + 1):
                    out[r][c] = color
    return out


def test_rule_authority_pin():
    assert getattr(gen, 'RULE_HASH', None) == 'ad1f1fa8669a'


@pytest.mark.parametrize('bad', [True, -1, 10, 2.0, '2', None])
def test_validator_checks_every_cell(bad):
    grid = [[0] * 4 for _ in range(6)]
    grid[0][0] = grid[5][0] = 1
    grid[1][3] = bad
    assert gen.self_check(grid), 'A valid early column must not hide malformed later cells'


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('axis,value', [('grid_h', 4), ('grid_h', 22), ('grid_w', 4),
                                       ('grid_w', 20), ('pairs', 1), ('pairs', 12),
                                       ('n_distinct_colors', 1), ('n_distinct_colors', 9)])
def test_single_override_is_exact_in_every_band(band, axis, value):
    g = gen.generate(81, 1, difficulty=band, **{axis: value})
    observed = {'grid_h': len(g), 'grid_w': len(g[0]),
                'pairs': sum(n == 2 for col in groups(g) for n in col.values()),
                'n_distinct_colors': len({v for row in g for v in row} - {0})}
    assert observed[axis] == value
    assert gen.self_check(g) == []


def test_unknown_overrides_rejected():
    with pytest.raises(ValueError, match='unknown'):
        gen.generate(0, 0, bogus_axis=3)


@pytest.mark.parametrize('bad', [True, 4.0, '4'])
def test_numeric_axes_do_not_coerce(bad):
    with pytest.raises(ValueError):
        gen.generate(0, 0, grid_h=bad)


def test_contrast_examples_actually_occur():
    grids = [gen.generate(91, i, difficulty='medium') for i in range(30)]
    assert any(any(3 in col.values() for col in groups(g)) for g in grids), 'No exact-count negatives'
    assert any(any(sorted(col.values()) == [1, 1] for col in groups(g)) for g in grids), 'No unlike-color endpoints'
    assert any(any(sorted(col.values()) == [1, 2] for col in groups(g)) for g in grids), 'No pair-with-interior-noise examples'


def test_canonical_acceptance_and_declared_shortcut_fit():
    pairs = canonical_pairs(TASK, root=find_root(__file__))
    assert len(pairs) >= 5
    rivals = getattr(gen, 'CANONICAL_SHORTCUTS', {})
    assert rivals, 'Canonical-fitting rivals must be executable rather than comments'
    for pair in pairs:
        inp, out = pair["input"], pair["output"]
        assert gen.self_check(inp) == []
        assert oracle(inp) == out
        for name, rival in rivals.items():
            assert rival(inp) == out, name


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_every_short_cyclic_start_and_query_rotation_has_a_witness(band):
    rivals = gen.LESSON_COMPETITORS
    for seed in (0, 91, 2026):
        grids = [gen.generate(seed, i, difficulty=band) for i in range(15)]
        outputs = [oracle(g) for g in grids]
        predictions = {name: [rival(g) for g in grids] for name, rival in rivals.items()}
        for start in range(12):
            for query in range(start, start + 4):
                for name, preds in predictions.items():
                    assert any(preds[i] != outputs[i] for i in range(start, start + 4) if i != query), (seed, start, query, name)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_joint_support_at_geometric_and_palette_boundaries(band):
    import itertools
    for phase, w, p, k in itertools.product(range(3), (4, 20), (1, 2, 6, 12), (1, 2, 5, 9)):
        ovs = dict(grid_h=4, grid_w=w, pairs=p, n_distinct_colors=k)
        allowed = (p <= w and k <= p) or (p + 2 <= w and 2 <= k <= (p + 3 if p >= 2 else 5))
        if not allowed:
            with pytest.raises(ValueError) as caught:
                gen.generate(409, phase, difficulty=band, **ovs)
            assert len(caught.value.incompatible_axes) >= 2
        else:
            g = gen.generate(409, phase, difficulty=band, **ovs)
            assert gen.observe_overrides(g) == ovs
            assert gen.self_check(g) == []


def test_prior_audit_triple_is_now_an_explicit_lawful_negative():
    g = [[0] * 4 for _ in range(7)]
    g[0][0] = g[6][0] = 1
    g[0][1] = g[2][1] = g[6][1] = 2
    assert gen.self_check(g) == []
    out = oracle(g)
    assert [r[1] for r in out] == [r[1] for r in g]
    assert gen.SEMANTIC_RIVALS['at_least_two'](g) != out
    # Unsupported multiplicity is rejected even with a valid earlier column.
    g[4][1] = 2
    assert gen.self_check(g)


def test_metadata_cannot_bypass_validation():
    g = [[0] * 4 for _ in range(6)]
    assert gen.self_check(g, meta={'texture': 'no_endpoints'})


@pytest.mark.parametrize('axis', ['palette_kind', 'palette_size', 'position_bias', 'density', 'texture'])
def test_removed_inoperative_controls_fail_instead_of_being_silently_ignored(axis):
    with pytest.raises(ValueError, match='unknown'):
        gen.generate(0, 0, **{axis: 'legacy'})


def test_generation_and_rivals_are_pure_and_reproducible():
    import copy
    import random
    state = random.getstate()
    for i in range(12):
        grid = gen.generate(712, i)
        saved = copy.deepcopy(grid)
        assert gen.generate(712, i) == grid
        for name, rival in gen.LESSON_COMPETITORS.items():
            a = rival(grid)
            assert grid == saved, name
            assert a == rival(grid), name
            assert a is not grid
    assert random.getstate() == state


def test_horizontal_position_and_color_names_do_not_define_the_rule():
    for i in range(12):
        g = gen.generate(23, i)
        out = oracle(g)
        perm = [0, 6, 3, 8, 1, 9, 7, 2, 5, 4]
        recolor = lambda a: [[perm[v] for v in row] for row in a]
        assert oracle(recolor(g)) == recolor(out)
        assert oracle([row[::-1] for row in g]) == [row[::-1] for row in out]
        assert oracle(g[::-1]) == out[::-1]
