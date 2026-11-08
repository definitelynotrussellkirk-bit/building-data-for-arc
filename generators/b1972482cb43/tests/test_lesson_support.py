"""Regression for retaining useful easy shapes while adding teaching witnesses."""
from reviewer_support import find_root, load_selected_generator

G, _, _ = load_selected_generator('b1972482cb43', root=find_root(__file__))


def test_production_retains_domino_and_square_shapes():
    observed = set()
    for index in range(150):
        grid = G.generate(29, index, difficulty='easy')
        cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)}
        if len(cells) == 2:
            observed.add('domino')
        if len(cells) == 4 and len({r for r, c in cells}) == len({c for r, c in cells}) == 2:
            observed.add('square')
    assert observed == {'domino', 'square'}, 'new lesson witnesses must retain original easy-shape support'


def test_production_retains_fully_visible_asymmetric_reflections():
    count = 0
    for index in range(100):
        grid = G.generate(37, index, difficulty='medium')
        (ar, ac), = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
        cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)}
        reflected = {(2*ar-r, 2*ac-c) for r, c in cells}
        rsum = min(r for r, c in cells) + max(r for r, c in cells)
        csum = min(c for r, c in cells) + max(c for r, c in cells)
        asymmetric = cells != {(rsum-r, csum-c) for r, c in cells}
        full_copy = all(0 <= r < len(grid) and 0 <= c < len(grid[0]) for r, c in reflected)
        count += asymmetric and full_copy
    assert count > 0, 'clipping witnesses must not remove complete asymmetric copies from production'
