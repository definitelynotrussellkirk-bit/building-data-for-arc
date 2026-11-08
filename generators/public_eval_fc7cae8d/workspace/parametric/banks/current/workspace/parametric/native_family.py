"""General framed-picture rule; Python claims are re-executed through Racket."""
from pathlib import Path

SIDE_MAPS = ((0, 1, 2, 3), (1, 2, 3, 0), (2, 3, 0, 1), (3, 0, 1, 2),
             (0, 3, 2, 1), (2, 1, 0, 3), (3, 2, 1, 0), (1, 0, 3, 2))
TRANSFORM_NAMES = ('identity', 'clockwise', 'half_turn', 'counterclockwise',
                   'left_right', 'up_down', 'transpose', 'antidiagonal')
DEFAULT = {'marker_pairing': 'match'}
HOME = Path(__file__).resolve().parents[2]


def normalize_settings(settings):
    if type(settings) is not dict or set(settings) != {'marker_pairing'}:
        raise ValueError('settings must contain exactly marker_pairing')
    value = settings['marker_pairing']
    if type(value) is not str or value not in ('match', 'swap'):
        raise ValueError('marker_pairing must be match or swap')
    return {'marker_pairing': value}


def normalize_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError('grid must have 1..30 exact-list rows')
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('grid must have 1..30 columns')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError('grid must be rectangular exact lists')
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError('colors must be exact integers 0..9')
    return [row[:] for row in grid]


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(height):
        for c in range(width):
            if not grid[r][c] or (r, c) in seen:
                continue
            cells, stack = [], [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def inspect_grid(grid):
    """Validate the admitted grammar and return the input-dependent frame."""
    grid = normalize_grid(grid)
    height, width = len(grid), len(grid[0])
    interiors = [cells for cells in _components(grid)
                 if all(0 < r < height-1 and 0 < c < width-1 for r, c in cells)]
    if len(interiors) != 1:
        raise ValueError('expected exactly one interior nonzero component')
    cells = interiors[0]
    r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
    c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
    cell_set = set(cells)
    if any(grid[r][c] and (r, c) not in cell_set
           for r in range(r0, r1+1) for c in range(c0, c1+1)):
        raise ValueError('boundary components intrude into the picture box')
    edges = (grid[0][1:-1], [row[-1] for row in grid[1:-1]],
             grid[-1][1:-1], [row[0] for row in grid[1:-1]])
    border_colors = {v for edge in edges for v in edge if v}
    markers = sorted(border_colors & {grid[r][c] for r, c in cells})
    if len(markers) != 2:
        raise ValueError('expected exactly two reserved marker colors')
    inner, outer = [], []
    for color in markers:
        positions = {(r, c) for r, c in cells if grid[r][c] == color}
        possible = []
        if all(r == r0 for r, c in positions): possible.append(0)
        if all(c == c1 for r, c in positions): possible.append(1)
        if all(r == r1 for r, c in positions): possible.append(2)
        if all(c == c0 for r, c in positions): possible.append(3)
        if len(possible) != 1:
            raise ValueError('marker must be one unambiguous straight side bar')
        inner.append(possible[0])
        counts = [edge.count(color) for edge in edges]
        if counts.count(max(counts)) != 1 or max(counts) < 2:
            raise ValueError('marker needs a unique dominant outer side')
        outer.append(counts.index(max(counts)))
    if (inner[0]-inner[1]) % 2 != 1 or (outer[0]-outer[1]) % 2 != 1:
        raise ValueError('inner and outer marker sides must each be adjacent')
    top, bottom = r0 + (0 in inner), r1 - (2 in inner)
    left, right = c0 + (3 in inner), c1 - (1 in inner)
    if bottom-top+1 < 2 or right-left+1 < 2:
        raise ValueError('picture axes must contain at least two cells')
    for color, side in zip(markers, inner):
        actual = {(r, c) for r, c in cells if grid[r][c] == color}
        expected = ({(r0, c) for c in range(left, right+1)} if side == 0 else
                    {(r, c1) for r in range(top, bottom+1)} if side == 1 else
                    {(r1, c) for c in range(left, right+1)} if side == 2 else
                    {(r, c0) for r in range(top, bottom+1)})
        if actual != expected:
            raise ValueError('marker must fill its complete side and no picture cells')
    corner = (r0 if 0 in inner else r1, c0 if 3 in inner else c1)
    if grid[corner[0]][corner[1]] != 0:
        raise ValueError('the two bars have an empty shared corner')
    picture = [row[left:right+1] for row in grid[top:bottom+1]]
    if any(v in border_colors for row in picture for v in row if v):
        raise ValueError('frame colors are reserved outside the picture')
    return {'picture': picture, 'picture_bbox': [top, left, bottom, right],
            'component_bbox': [r0, c0, r1, c1], 'marker_colors': markers,
            'inner_sides': inner, 'outer_sides': outer}


def transform_grid(picture, index):
    if type(index) is not int or not 0 <= index < 8:
        raise ValueError('D4 transform index must be 0..7')
    p = [row[:] for row in picture]
    transposed = [list(row) for row in zip(*p)]
    return (p, [row[::-1] for row in transposed], [row[::-1] for row in p[::-1]],
            transposed[::-1], [row[::-1] for row in p], p[::-1],
            transposed, [row[::-1] for row in transposed[::-1]])[index]


def transform_index(frame, settings):
    settings = normalize_settings(settings)
    targets = frame['outer_sides'][:]
    if settings['marker_pairing'] == 'swap': targets.reverse()
    matches = [i for i, mapping in enumerate(SIDE_MAPS)
               if [mapping[side] for side in frame['inner_sides']] == targets]
    if len(matches) != 1:
        raise ValueError('frame correspondence must identify exactly one D4 transform')
    return matches[0]


def solve(grid, settings):
    settings = normalize_settings(settings)
    frame = inspect_grid(grid)
    return transform_grid(frame['picture'], transform_index(frame, settings))


def program(settings):
    settings = normalize_settings(settings)
    source = (HOME / 'reference.rkt').read_text()
    if settings['marker_pairing'] == 'match': return source
    needle = '(define swap-markers? #f)'
    if source.count(needle) != 1:
        raise ValueError('canonical marker setting declaration is not unique')
    return source.replace(needle, '(define swap-markers? #t)', 1)


def rival_programs(settings):
    """Nearby executable alternatives; auditing uses demos before any queries."""
    source = program(settings)
    start = source.index('   (define chosen-transform\n')
    stop = source.index('   (cond\n    [(= chosen-transform', start)
    def replace_choice(expression):
        return source[:start] + '   (define chosen-transform ' + expression + ')\n' + source[stop:]
    result = {f'constant_{name}': replace_choice(str(i)) for i, name in enumerate(TRANSFORM_NAMES)}
    result['first_marker_rotations'] = replace_choice(
        '(for/first ([k (range 0 4)] #:when (= (list-ref (list-ref side-maps k) (first inner-sides)) (first target-sides))) k)')
    result['second_marker_rotations'] = replace_choice(
        '(for/first ([k (range 0 4)] #:when (= (list-ref (list-ref side-maps k) (second inner-sides)) (second target-sides))) k)')
    result['first_marker_reflections'] = replace_choice(
        '(for/first ([k (range 4 8)] #:when (= (list-ref (list-ref side-maps k) (first inner-sides)) (first target-sides))) k)')
    result['second_marker_reflections'] = replace_choice(
        '(for/first ([k (range 4 8)] #:when (= (list-ref (list-ref side-maps k) (second inner-sides)) (second target-sides))) k)')
    result['inverse_alignment'] = replace_choice(
        '(for/first ([k (range 0 8)] #:when (equal? (map (lambda (side) (list-ref (list-ref side-maps k) side)) target-sides) inner-sides)) k)')
    other = {'marker_pairing': 'swap' if settings['marker_pairing'] == 'match' else 'match'}
    result['other_pairing'] = program(other)
    begin = source.index('   (define picture\n')
    end = source.index('   (define side-maps\n', begin)
    result['include_bars'] = source[:begin] + '   (define picture (subgrid g rlo clo rhi chi))\n' + source[end:]
    # Replace zero cells by the modal nonzero picture color before orientation.
    result['fill_black_notches'] = source[:end] + (
        '   (define picture-values (filter (lambda (v) (> v 0)) (apply append picture)))\n'
        '   (define fill-color (pick-max (range 1 10) (lambda (color) (count (lambda (v) (= v color)) picture-values))))\n'
        '   (define filled (recolor picture 0 fill-color))\n') + source[end:]
    # Rename only the final transformation operand, preserving the parsed crop.
    marker = result['fill_black_notches'].index('   (cond\n    [(= chosen-transform')
    result['fill_black_notches'] = result['fill_black_notches'][:marker] + result['fill_black_notches'][marker:].replace('picture', 'filled')
    return result
