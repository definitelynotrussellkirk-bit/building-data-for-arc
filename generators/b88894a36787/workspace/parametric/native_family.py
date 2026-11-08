"""Reuse the exact missing-extension rules; add routes followed by first-hit fill."""
import importlib.util
from pathlib import Path

MODES = ('bottom', 'penultimate', 'first_hit')
HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / 'canonical.rkt').read_text(encoding='utf-8')
_spec = importlib.util.spec_from_file_location('native_route_legacy', HERE / 'missing_extension.py')
_legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_legacy)
if _legacy.program_for('bottom') != CANONICAL:
    raise ValueError('Legacy rule differs from the selected exact canonical resource')
FALLBACK = '(if dot (first dot) (- h 1))'
MATCH = '(find (lambda (d) (= (third d) hcol)) dots)'


def parse_settings(settings):
    if (type(settings) is not dict or set(settings) != {'missing_extension'}
            or type(settings['missing_extension']) is not str
            or settings['missing_extension'] not in MODES):
        raise ValueError('settings must contain exactly missing_extension=bottom, penultimate or first_hit')
    return {'missing_extension': settings['missing_extension']}


def entries(grid):
    """Header-order entries with the canonical first body-color match."""
    dots = [(r, c, v) for r, row in enumerate(grid) if r
            for c, v in enumerate(row) if v]
    result = []
    for hc, color in enumerate(grid[0]):
        if color:
            dot = next((d for d in dots if d[2] == color), None)
            result.append((hc, color, dot[0] if dot else len(grid) - 1,
                           dot[1] if dot else None))
    return result


def validate_grid(grid):
    if (type(grid) is not list or not 8 <= len(grid) <= 30
            or type(grid[0]) is not list or not 8 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError('grid must be rectangular 8..30 with exact integer colors 0..9')
    h, w = len(grid), len(grid[0])
    headers = [c for c, v in enumerate(grid[0]) if v]
    if (not 2 <= len(headers) <= min(8, w - 2)
            or headers[0] == 0 or headers[-1] == w - 1
            or headers != list(range(headers[0], headers[-1] + 1))):
        raise ValueError('need 2..8 contiguous interior headers')
    colors = [grid[0][c] for c in headers]
    if len(set(colors)) != len(colors):
        raise ValueError('header colors must be distinct')
    dots = [(r, c, v) for r, row in enumerate(grid) if r
            for c, v in enumerate(row) if v]
    if any(c not in (0, w - 1) for r, c, v in dots):
        raise ValueError('body dots must be on the two side edges')
    counts = {color: sum(v == color for r, c, v in dots) for color in colors}
    if any(n > 1 for n in counts.values()):
        raise ValueError('a header color can have at most one matching side dot')
    missing_count = sum(n == 0 for n in counts.values())
    if missing_count > min(2, len(headers) - 1):
        raise ValueError('at most two missing headers and at least one match are required')
    ignored = [d for d in dots if d[2] not in colors]
    if len(ignored) > 2:
        raise ValueError('at most two ignored edge dots are supported')
    parsed = entries(grid)
    return {'height': h, 'width': w, 'headers': headers, 'entries': parsed,
            'missing': [e for e in parsed if e[3] is None], 'ignored_dots': ignored}


def _render(grid, parsed, missing_row):
    out = [[0] * len(grid[0]) for _ in grid]
    # Later entries are painted first, so the leftmost header wins every overlap.
    for hc, color, row, col in reversed(parsed):
        stop = missing_row if col is None else row
        for r in range(stop + 1):
            out[r][hc] = color
        if col is not None:
            for c in range(min(hc, col), max(hc, col) + 1):
                out[row][c] = color
    return out


def render_matched(grid):
    info = validate_grid(grid)
    return _render(grid, info['entries'], 0)


def first_hits(grid):
    stage = render_matched(grid)
    return {hc: next((r for r in range(1, len(grid)) if stage[r][hc]), None)
            for hc, color, row, col in entries(grid) if col is None}


def apply(grid, settings):
    mode = parse_settings(settings)['missing_extension']
    info = validate_grid(grid)
    if mode != 'first_hit':
        return _render(grid, info['entries'], len(grid) - (1 if mode == 'bottom' else 2))
    stage = _render(grid, info['entries'], 0)
    out = [row[:] for row in stage]
    for hc, color, row, col in info['missing']:
        stop = next((r for r in range(1, len(grid)) if stage[r][hc]), len(grid))
        for r in range(1, stop):
            out[r][hc] = color
    return out


def _body(program):
    if not program.startswith('(rule!') or not program.endswith(')'):
        raise ValueError('expected one complete rule wrapper')
    return program[len('(rule!'):-1].strip()


def routing_program(fallback='(- h 1)', *, priority='left', matcher=None, vertical_only=False):
    """Exact-source substitution for the intermediate and bounded audit variants."""
    if CANONICAL.count(FALLBACK) != 1:
        raise ValueError('canonical missing fallback is not unique')
    result = CANONICAL.replace(FALLBACK, f'(if dot (first dot) {fallback})', 1)
    if priority == 'right':
        if result.count('entries)))') != 1:
            raise ValueError('canonical entry priority site is not unique')
        result = result.replace('entries)))', '(reverse entries))))', 1)
    elif priority != 'left':
        raise ValueError('unknown priority')
    if matcher is not None:
        if result.count(MATCH) != 1:
            raise ValueError('canonical matching site is not unique')
        result = result.replace(MATCH, matcher, 1)
    if vertical_only:
        needle = '(and\n                                                tcol'
        if result.count(needle) != 1:
            raise ValueError('canonical horizontal branch is not unique')
        result = result.replace(needle, '(and\n                                                #f', 1)
    return result


_BINDINGS = '''((h (rows g)) (w (cols g))
    (headers (filter (lambda (c) (not (= (at g 0 c) 0))) (range 0 w)))
    (dots (filter (lambda (x) x)
      (for*/list ((r (range 1 h)) (c (range 0 w)))
        (and (not (= (at g r c) 0)) (list r c (at g r c))))))
    (missing (filter (lambda (hc)
      (not (find (lambda (d) (= (third d) (at g 0 hc))) dots))) headers)))'''


def first_hit_program(*, observed='stage', route=None, stop_expression=None,
                      missing_expression='missing', paint_zero_only=True):
    """Compose a complete Racket rule; optional arguments name audit ablations."""
    if observed not in ('stage', 'g', 'canonical'):
        raise ValueError('unknown observed intermediate')
    renderer = route or routing_program('0')
    observed_expression = f'({_body(CANONICAL)} g)' if observed == 'canonical' else observed
    stop = stop_expression or '(if (empty? hits) h (first hits))'
    paint = '(set-cell out r hc (at g 0 hc))'
    if paint_zero_only:
        paint = f'(if (= (at stage r hc) 0) {paint} out)'
    return f'''(rule! (lambda (g) (let* {_BINDINGS}
      (let* ((stage ({_body(renderer)} g)) (observed {observed_expression}))
        (for/fold ((out stage)) ((hc (in-list {missing_expression})))
          (let* ((hits (filter (lambda (r) (not (= (at observed r hc) 0))) (range 1 h)))
                 (stop {stop}))
            (for/fold ((out out)) ((r (in-range 1 stop))) {paint})))))))'''


def program(settings):
    mode = parse_settings(settings)['missing_extension']
    return first_hit_program() if mode == 'first_hit' else _legacy.program_for(mode)


def _conditional(first, predicate, second):
    return f'(rule! (lambda (g) (let* {_BINDINGS} (if {predicate} ({_body(first)} g) ({_body(second)} g)))))'


def rivals(settings):
    """Finite executable alternatives; diagnostics, never additional gold rules."""
    mode = parse_settings(settings)['missing_extension']
    # The reusable audit adds declared-setting alternatives exactly once.
    menu = {}
    menu['identity'] = '(rule! (lambda (g) g))'
    menu['all_columns_to_bottom'] = '''(rule! (lambda (g)
      (grid-from-fn (rows g) (cols g) (lambda (r c) (at g 0 c)))))'''
    menu['omit_unmatched_headers'] = routing_program('-1')
    fallback = {'bottom': '(- h 1)', 'penultimate': '(- h 2)', 'first_hit': '0'}[mode]
    for name, options in {
        'rightmost_header_priority': {'priority': 'right'},
        'vertical_segments_only': {'vertical_only': True},
        'ignore_color_choose_first_dot': {'matcher': '(if (empty? dots) #f (first dots))'},
    }.items():
        route = routing_program(fallback, **options)
        menu[name] = first_hit_program(route=route) if mode == 'first_hit' else route
    correct = program(settings)
    menu['preserve_ignored_dots'] = f'''(rule! (lambda (g) (let* {_BINDINGS}
      (let ((out ({_body(correct)} g)))
        (for/fold ((result out)) ((d (in-list dots)))
          (if (member (third d) (map (lambda (c) (at g 0 c)) headers)) result
              (set-cell result (first d) (second d) (third d))))))))'''
    if mode == 'first_hit':
        menu.update({
            'scan_original_input': first_hit_program(observed='g'),
            'scan_fully_completed_default': first_hit_program(observed='canonical'),
            'last_hit': first_hit_program(stop_expression='(if (empty? hits) h (last hits))'),
            'topmost_dot_row': first_hit_program(stop_expression='(apply min (map first dots))'),
            'paint_through_blocker': first_hit_program(stop_expression='(if (empty? hits) h (+ 1 (first hits)))', paint_zero_only=False),
            'no_hit_no_extension': first_hit_program(stop_expression='(if (empty? hits) 1 (first hits))'),
            'first_missing_only': first_hit_program(missing_expression="(if (empty? missing) '() (list (first missing)))"),
            'only_when_one_missing': _conditional(correct, '(= (length missing) 1)', CANONICAL),
            'only_when_two_missing': _conditional(correct, '(= (length missing) 2)', CANONICAL),
            'ignore_stops_on_left_half': first_hit_program(stop_expression='(if (or (< (* hc 2) w) (empty? hits)) h (first hits))'),
            'ignore_stops_on_right_half': first_hit_program(stop_expression='(if (or (>= (* hc 2) w) (empty? hits)) h (first hits))'),
            'ignore_stops_in_lower_half': first_hit_program(stop_expression='(if (or (empty? hits) (>= (* 2 (first hits)) h)) h (first hits))'),
            'ignore_boundary_stops': first_hit_program(stop_expression='(if (or (= hc (first headers)) (= hc (last headers)) (empty? hits)) h (first hits))'),
            'ignore_interior_stops': first_hit_program(stop_expression='(if (or (and (not (= hc (first headers))) (not (= hc (last headers)))) (empty? hits)) h (first hits))'),
        })
    return menu
