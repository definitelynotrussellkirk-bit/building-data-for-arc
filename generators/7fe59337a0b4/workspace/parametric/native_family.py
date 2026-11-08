"""Orbit a cropped motif; optionally connect the marker to the rendered arms.

This separate grammar extends canvas/motif sizes without changing production.
Python labels are claims; qualification and audit execute the Racket programs.
"""
from collections import deque
from pathlib import Path

LINKS = ('none', 'first_hit')
CANONICAL = Path(__file__).with_name('canonical.rkt').read_text(encoding='utf-8')
if not CANONICAL.startswith('(rule! ') or not CANONICAL.endswith(')'):
    raise ValueError('Expected the exact selected canonical rule! resource')
CANONICAL_BODY = CANONICAL[len('(rule! '):-1]


def parse_settings(settings):
    if (type(settings) is not dict or set(settings) != {'links'}
            or type(settings['links']) is not str or settings['links'] not in LINKS):
        raise ValueError('settings must be exactly links=none or links=first_hit')
    return {'links': settings['links']}


def rotate_cw(shape):
    return [list(row) for row in zip(*shape[::-1])]


def _placements(shape, marker):
    mr, mc = marker
    parts = [shape]
    for _ in range(3):
        parts.append(rotate_cw(parts[-1]))
    tops = [(mr - 1 - len(parts[0]), mc - len(parts[0][0]) // 2),
            (mr - len(parts[1]) // 2, mc + 2),
            (mr + 2, mc - len(parts[2][0]) // 2),
            (mr - len(parts[3]) // 2, mc - 1 - len(parts[3][0]))]
    return [{(top + r, left + c): value
             for r, row in enumerate(part) for c, value in enumerate(row) if value}
            for part, (top, left) in zip(parts, tops)]


def validate_grid(grid):
    if (type(grid) is not list or not 9 <= len(grid) <= 30
            or any(type(row) is not list or len(row) != len(grid)
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError('grid must be square 9..30 with exact integer colors 0..9')
    markers = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)}
    if len(markers) != 1 or len(cells) < 3:
        raise ValueError('need one marker and at least three motif cells')
    colors = {grid[r][c] for r, c in cells}
    if len(colors) != 1:
        raise ValueError('motif must have one color distinct from 0 and 9')
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p = (r + dr, c + dc)
            if p in cells and p not in seen:
                seen.add(p); queue.append(p)
    if seen != cells:
        raise ValueError('motif must be four-connected')
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    r1, c1 = max(r for r, c in cells), max(c for r, c in cells)
    mr, mc = markers[0]
    if r1 == r0 or c1 == c0 or (r0 <= mr <= r1 and c0 <= mc <= c1):
        raise ValueError('motif must span two axes and its box must exclude the marker')
    shape = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    rotations = []
    part = shape
    for _ in range(4):
        rotations.append(tuple(map(tuple, part))); part = rotate_cw(part)
    if len(set(rotations)) != 4:
        raise ValueError('motif must have four distinct quarter turns')
    placements = _placements(shape, markers[0])
    occupied = {markers[0]}
    for placement in placements:
        if any(not (0 <= r < len(grid) and 0 <= c < len(grid)) for r, c in placement):
            raise ValueError('rendered copies must not be clipped')
        if occupied.intersection(placement):
            raise ValueError('rendered copies and marker must not overlap')
        occupied.update(placement)
    return {'marker': markers[0], 'shape': shape, 'motif_cells': cells,
            'motif_color': next(iter(colors)), 'bbox': (r0, c0, r1, c1),
            'placements': placements}


def orbit(grid):
    info = validate_grid(grid)
    out = [[0] * len(grid) for _ in grid]
    for part in info['placements']:
        for (r, c), v in part.items(): out[r][c] = v
    mr, mc = info['marker']; out[mr][mc] = 9
    return out


def link_cells(occupancy, marker):
    """Blank cells before the first occupied hit; a no-hit ray paints nothing."""
    result = []
    mr, mc = marker
    for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
        r, c = mr + dr, mc + dc
        pending = []
        while 0 <= r < len(occupancy) and 0 <= c < len(occupancy[0]):
            if occupancy[r][c]:
                result.extend(pending); break
            pending.append((r, c)); r += dr; c += dc
    return result


def apply(grid, settings):
    settings = parse_settings(settings)
    out = orbit(grid)
    if settings['links'] == 'first_hit':
        marker = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9)
        for r, c in link_cells(out, marker): out[r][c] = 9
    return out


def linked_program(body=CANONICAL_BODY, *, occupancy='base', mode='first_hit', paint='9'):
    """Private executable counterfactual builder, also used for the real setting.

    `occupancy=g` deliberately computes stop cells before rendering the orbit.
    Modes are bounded audit alternatives; only first_hit is a declared setting.
    """
    if occupancy not in ('base', 'g') or mode not in ('first_hit', 'one_cell', 'two_cells', 'to_edge', 'overwrite_hit', 'last_hit', 'north_length'):
        raise ValueError('unknown private ray counterfactual')
    if paint not in ('9', '(at shape 0 0)'):
        raise ValueError('unknown paint expression')
    if paint != '9':
        paint = '(first (filter (lambda (v) (and (not (= v 0)) (not (= v 9)))) (flatten g)))'
    commit = f'''(for/fold ((painted out)) ((p pending))
       (if (= (at base (first p) (second p)) 0)
           (set-cell painted (first p) (second p) {paint}) painted))'''
    if mode in ('one_cell', 'two_cells', 'to_edge', 'north_length'):
        bound = {'one_cell':'1', 'two_cells':'2', 'to_edge':'(max (rows g) (cols g))',
                 'north_length': '''(let loop ((r (- mr 1)) (n 0))
                    (cond ((< r 0) 0) ((not (= (at base r mc) 0)) n)
                          (else (loop (- r 1) (+ n 1)))))'''}[mode]
        rays = f'''(for*/fold ((out base)) ((delta '((-1 0) (0 1) (1 0) (0 -1)))
                    (n (in-range 1 (+ {bound} 1))))
          (let ((r (+ mr (* n (first delta)))) (c (+ mc (* n (second delta)))))
            (if (and (in-bounds? r c (rows g) (cols g)) (= (at base r c) 0))
                (set-cell out r c {paint}) out)))'''
    elif mode == 'last_hit':
        rays = f'''(for/fold ((out base)) ((delta '((-1 0) (0 1) (1 0) (0 -1))))
          (let walk ((r (+ mr (first delta))) (c (+ mc (second delta))) (pending '()) (latest out))
            (cond ((not (in-bounds? r c (rows g) (cols g))) latest)
                  ((not (= (at observed r c) 0))
                   (walk (+ r (first delta)) (+ c (second delta)) pending {commit}))
                  (else (walk (+ r (first delta)) (+ c (second delta))
                              (cons (list r c) pending) latest)))))'''
    else:
        hit = commit
        if mode == 'overwrite_hit': hit = f'(set-cell {commit} r c {paint})'
        rays = f'''(for/fold ((out base)) ((delta '((-1 0) (0 1) (1 0) (0 -1))))
          (let walk ((r (+ mr (first delta))) (c (+ mc (second delta))) (pending '()))
            (cond ((not (in-bounds? r c (rows g) (cols g))) out)
                  ((not (= (at observed r c) 0)) {hit})
                  (else (walk (+ r (first delta)) (+ c (second delta))
                              (cons (list r c) pending))))))'''
    return f'''(rule! (lambda (g)
      (let* ((base {body}) (observed {occupancy})
             (marker (first (find-color g 9))) (mr (first marker)) (mc (second marker)))
        {rays})))'''


def program(settings):
    mode = parse_settings(settings)['links']
    return CANONICAL if mode == 'none' else linked_program()


def rivals(settings):
    """Finite, total private shortcut programs; failures never count as teaching."""
    links = parse_settings(settings)['links']
    def finish(body):
        return f'(rule! (lambda (g) {body}))' if links == 'none' else linked_program(body)
    rotations = '(r1 (rotate-cw r0)) (r2 (rotate-cw r1)) (r3 (rotate-cw r2))'
    if CANONICAL_BODY.count(rotations) != 1:
        raise ValueError('canonical resource no longer matches the reviewed construction')
    unrotated = CANONICAL_BODY.replace(rotations, '(r1 r0) (r2 r0) (r3 r0)')
    reversed_turns = CANONICAL_BODY.replace(rotations,
        '(r1 (rotate-cw (rotate-cw (rotate-cw r0)))) '
        '(r2 (rotate-cw (rotate-cw r0))) (r3 (rotate-cw r0))')
    keep_source = f'''(let ((result {CANONICAL_BODY}))
      (grid-from-fn (rows g) (cols g) (lambda (r c)
        (if (= (at result r c) 0) (at g r c) (at result r c)))))'''
    source_points = '''(filter (lambda (p) (let ((v (at g (first p) (second p))))
      (and (not (= v 0)) (not (= v 9))))) (grid-positions g))'''
    diagonal = '''(and (or (< (third bb) mr) (> (first bb) mr))
                       (or (< (fourth bb) mc) (> (second bb) mc)))'''
    gate = f'''(let* ((bb (bbox-of-cells {source_points}))
      (center (first (find-color g 9))) (mr (first center)) (mc (second center)))
      (if {diagonal} {CANONICAL_BODY} {unrotated}))'''
    opposite_gate = gate.replace(f'(if {diagonal}', f'(if (not {diagonal})')
    miscenter = CANONICAL_BODY.replace('(quotient (cols r0) 2)', '(quotient (+ (cols r0) 1) 2)')
    canvas_center = CANONICAL_BODY.replace('(center (first (find-color g 9)))',
        '(center (list (quotient (rows g) 2) (quotient (cols g) 2)))')
    drop_marker = f'''(let ((result {CANONICAL_BODY}))
      (grid-from-fn (rows g) (cols g) (lambda (r c)
        (if (= (at result r c) 9) 0 (at result r c)))))'''
    result = {'unrotated_copies': finish(unrotated),
              'reverse_quarter_turns': finish(reversed_turns),
              'retain_original_source': finish(keep_source),
              'diagonal_source_only': finish(gate),
              'cardinal_source_only': finish(opposite_gate),
              'ceil_north_centering': finish(miscenter),
              'use_canvas_center': finish(canvas_center),
              'drop_marker': finish(drop_marker)}
    for side, predicate in {'above': '(< (third bb) mr)',
                            'below': '(> (first bb) mr)',
                            'left': '(< (fourth bb) mc)',
                            'right': '(> (second bb) mc)'}.items():
        gated = f'''(let* ((bb (bbox-of-cells {source_points}))
          (center (first (find-color g 9))) (mr (first center)) (mc (second center)))
          (if {predicate} {reversed_turns} {CANONICAL_BODY}))'''
        result['reverse_if_source_' + side] = finish(gated)
    if links == 'first_hit':
        result.update({'rays_before_orbit': linked_program(occupancy='g'),
                       'fixed_one_cell_links': linked_program(mode='one_cell'),
                       'fixed_two_cell_links': linked_program(mode='two_cells'),
                       'continue_to_edge': linked_program(mode='to_edge'),
                       'continue_to_last_hit': linked_program(mode='last_hit'),
                       'copy_north_ray_length': linked_program(mode='north_length'),
                       'overwrite_hit_cell': linked_program(mode='overwrite_hit'),
                       'paint_motif_color': linked_program(paint='(at shape 0 0)')})
    return result
