"""Native orbit stamping with a fixed or source-derived orientation frame."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parent
CANONICAL = (HOME / 'canonical.rkt').read_text()
MODES = ('fixed', 'source_side')
BACKGROUND = 0
SIDE_TURNS = {'above': 0, 'right': 1, 'below': 2, 'left': 3}

_spec = importlib.util.spec_from_file_location(
    '_selected_orbit_9a35b20efa99', HOME.parents[1] / 'generator.py')
_selected = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_selected)
normalize = _selected._normalize_cells
rotated = _selected._rotated_cells
dimensions = _selected._shape_size


def parse_settings(settings):
    if (type(settings) is not dict or set(settings) != {'orientation_frame'}
            or type(settings['orientation_frame']) is not str
            or settings['orientation_frame'] not in MODES):
        raise ValueError('settings must contain exactly orientation_frame=fixed or source_side')
    return {'orientation_frame': settings['orientation_frame']}


def validate_grid(grid):
    if (type(grid) is not list or not 6 <= len(grid) <= 30
            or type(grid[0]) is not list or not 6 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError('need an exact-integer rectangular ARC grid with axes 6..30')
    height, width = len(grid), len(grid[0])
    anchors = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 9]
    cells = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,9)}
    colors = {grid[r][c] for r,c in cells}
    if len(anchors) != 1 or len(colors) != 1 or not 3 <= len(cells) <= 196:
        raise ValueError('need one color-9 anchor and one monochrome template of 3..196 cells')
    frontier = [next(iter(cells))]; seen = set(frontier)
    while frontier:
        r,c = frontier.pop()
        for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if q in cells and q not in seen:
                seen.add(q); frontier.append(q)
    if seen != cells:
        raise ValueError('template must be four-connected')
    r0,c0 = min(r for r,c in cells),min(c for r,c in cells)
    r1,c1 = max(r for r,c in cells),max(c for r,c in cells)
    shape = (r1-r0+1,c1-c0+1)
    if not all(2 <= size <= 14 for size in shape):
        raise ValueError('template bbox axes must be 2..14')
    ar,ac = anchors[0]; m = max(shape)
    if not (m+1 <= ar <= height-m-1 and m+1 <= ac <= width-m-1):
        raise ValueError('anchor margin must fit every native orientation')
    sides = []
    if r1 <= ar-2 and c0 <= ac <= c1: sides.append('above')
    if c0 >= ac+2 and r0 <= ar <= r1: sides.append('right')
    if r0 >= ar+2 and c0 <= ac <= c1: sides.append('below')
    if c1 <= ac-2 and r0 <= ar <= r1: sides.append('left')
    if len(sides) != 1:
        raise ValueError('template must lie on one separated, anchor-aligned cardinal side')
    local = normalize(cells); color = next(iter(colors))
    crop = [[color if (r,c) in local else 0 for c in range(shape[1])] for r in range(shape[0])]
    return {'height':height,'width':width,'anchor':anchors[0], 'cells':cells,
            'local':local,'color':color,'bbox':(r0,c0,r1,c1),'side':sides[0],'crop':crop}


def intermediate(grid, settings):
    mode = parse_settings(settings)['orientation_frame']
    info = validate_grid(grid)
    turns = SIDE_TURNS[info['side']] if mode == 'source_side' else 0
    cells = rotated(info['local'], turns)
    return {**info,'source_side':info['side'],'turns':turns,
            'oriented_cells':cells,'shape':dimensions(cells)}


def apply(grid, settings):
    state = intermediate(grid, settings)
    height,width = state['height'],state['width']
    ar,ac = state['anchor']; ch,cw = state['shape']
    offsets = ((-ch-1,-cw-1),(-ch-1,1),(1,-cw-1),(1,1))
    out = [[0]*width for _ in range(height)]; out[ar][ac] = 9
    for turns,(dr,dc) in enumerate(offsets):
        for r,c in rotated(state['oriented_cells'], turns):
            rr,cc = ar+dr+r,ac+dc+c
            if 0 <= rr < height and 0 <= cc < width:
                out[rr][cc] = state['color']
    return out


def _replace(source, needle, replacement):
    if source.count(needle) != 1:
        raise ValueError('native Racket replacement must identify one site: '+needle)
    return source.replace(needle, replacement, 1)


_CROP_SITE = '(crop (normalize-crop gg)) (ch (rows crop)) (cw (cols crop))'
_VARIANTS_SITE = '(variants (list crop (rotate-cw crop) (rotate-180 crop) (rotate-ccw crop)))'
_BASE_SITE = '(base (set-cell (empty-grid (rows g) (cols g) 0) (first anchor) (second anchor) 9))'
_ROTATIONS = ('crop','(rotate-cw crop)','(rotate-180 crop)','(rotate-ccw crop)')
_SIDE = '''(cond ((< (max-list (map first points)) (first anchor)) 0)
                 ((> (min-list (map second points)) (second anchor)) 1)
                 ((> (min-list (map first points)) (first anchor)) 2)
                 (else 3))'''


def variant_program(settings, *, forced_turns=None, turn_map=(0,1,2,3),
                    filled=False, stale_dimensions=False, order=(0,1,2,3),
                    center_anchor=False, keep_source=False, erase_anchor=False,
                    paint_color=None, gap=1, per_variant_offsets=False):
    """Materialize explicit, total bounded rivals and causal counterfactuals."""
    mode = parse_settings(settings)['orientation_frame']
    if forced_turns is not None and (type(forced_turns) is not int or forced_turns not in range(4)):
        raise ValueError('forced_turns must be 0..3')
    if (len(turn_map) != 4 or len(order) != 4
            or any(type(v) is not int or v not in range(4) for v in (*turn_map,*order))
            or type(gap) is not int or gap not in (0,1,2)
            or (paint_color is not None and (type(paint_color) is not int or not 1 <= paint_color <= 9))):
        raise ValueError('invalid bounded counterfactual controls')
    source = CANONICAL
    # Anchor-location rivals still remove the actual marker before cropping.
    source = _replace(source,'(gg (set-cell g (first anchor) (second anchor) 0))',
                      '(gg (set-cell g (first (first anchors)) (second (first anchors)) 0))')
    if center_anchor:
        source = _replace(source,'(anchor (first anchors))',
                          '(anchor (list (quotient (rows g) 2) (quotient (cols g) 2)))')
    if forced_turns is not None:
        turns = str(forced_turns)
    elif mode == 'fixed':
        turns = '0'
    else:
        turns = '(list-ref (list '+' '.join(map(str,turn_map))+') source-side)'
    oriented = '''(cond ((= turns 0) raw-crop) ((= turns 1) (rotate-cw raw-crop))
                         ((= turns 2) (rotate-180 raw-crop)) (else (rotate-ccw raw-crop)))'''
    crop = '(build-grid (rows oriented) (cols oriented) (r c) motif-color)' if filled else 'oriented'
    if paint_color is not None:
        crop = f'(build-grid (rows oriented) (cols oriented) (r c) (if (= (at oriented r c) 0) 0 {paint_color}))'
    dims = 'raw-crop' if stale_dimensions else 'crop'
    binding = f'''(raw-crop (normalize-crop gg))
       (points (filter (lambda (p) (not (= (at gg (first p) (second p)) 0))) (grid-positions gg)))
       (motif-color (at gg (first (first points)) (second (first points))))
       (source-side {_SIDE}) (turns {turns}) (oriented {oriented})
       (crop {crop}) (ch (rows {dims})) (cw (cols {dims}))'''
    source = _replace(source,_CROP_SITE,binding)
    if order != (0,1,2,3):
        source = _replace(source,_VARIANTS_SITE,'(variants (list '+' '.join(_ROTATIONS[i] for i in order)+'))')
    if gap != 1:
        original = '(offsets (list (list (- 0 ch 1) (- 0 cw 1)) (list (- 0 ch 1) 1) (list 1 (- 0 cw 1)) (list 1 1)))'
        replacement = f'(offsets (list (list (- 0 ch {gap}) (- 0 cw {gap})) (list (- 0 ch {gap}) {gap}) (list {gap} (- 0 cw {gap})) (list {gap} {gap})))'
        source = _replace(source,original,replacement)
    if keep_source:
        source = _replace(source,_BASE_SITE,'(base g)')
    elif erase_anchor:
        source = _replace(source,_BASE_SITE,'(base (empty-grid (rows g) (cols g) 0))')
    if per_variant_offsets:
        source = _replace(source,'((var (in-list variants)) (off (in-list offsets)))',
                          '((var (in-list variants)) (off (in-list offsets)) (i (in-range 4)))')
        source = _replace(source,'(paste-crop out var (+ (first anchor) (first off)) (+ (second anchor) (second off)))',
            '(paste-crop out var (+ (first anchor) (if (< i 2) (- 0 (rows var) 1) 1)) (+ (second anchor) (if (or (= i 0) (= i 2)) (- 0 (cols var) 1) 1)))')
    return source


def program(settings):
    mode = parse_settings(settings)['orientation_frame']
    return CANONICAL if mode == 'fixed' else variant_program(settings)


def _literal(value):
    return '('+' '.join(_literal(v) for v in value)+')' if isinstance(value,(list,tuple)) else str(value)


def _gated(source, condition):
    body = source[len('(rule! '):-1]
    return f'''(rule! (let* ((marker (first (filter (lambda (p) (= (at g (first p) (second p)) 9)) (grid-positions g))))
      (cleared (set-cell g (first marker) (second marker) 0))
      (pts (filter (lambda (p) (not (= (at cleared (first p) (second p)) 0))) (grid-positions cleared)))
      (raw (crop-to-content cleared 0)))
      (if {condition} {body} g)))'''


def rivals(settings):
    mode = parse_settings(settings)['orientation_frame']
    source = program(settings)
    result = {
        'filled_template_bbox':variant_program(settings,filled=True),
        'all_unrotated_copies':variant_program(settings,order=(0,0,0,0)),
        'reverse_stamp_order':variant_program(settings,order=(0,3,2,1)),
        'per_variant_offsets':variant_program(settings,per_variant_offsets=True),
        'canvas_center_anchor':variant_program(settings,center_anchor=True),
        'retain_original_source':variant_program(settings,keep_source=True),
        'erase_anchor':variant_program(settings,erase_anchor=True),
        'paint_anchor_color':variant_program(settings,paint_color=9),
        'paint_fixed_two':variant_program(settings,paint_color=2),
        'zero_gap':variant_program(settings,gap=0),
        'double_gap':variant_program(settings,gap=2),
        'above_only':_gated(source,'(< (max-list (map first pts)) (first marker))'),
    }
    masks = []
    for name in ('corner_l3','corner_l4'):
        for turns in range(4):
            cells = rotated(_selected._BASE_SHAPES[name],turns);h,w=dimensions(cells)
            masks.append([[int((r,c) in cells) for c in range(w)] for r in range(h)])
    result['corner_l_only'] = _gated(source,
        "(member (build-grid (rows raw) (cols raw) (r c) (if (= (at raw r c) 0) 0 1)) '"+_literal(masks)+')')
    for turns in (1,2,3):
        result['constant_frame_turn_'+str(turns)] = variant_program(settings,forced_turns=turns)
    if mode == 'source_side':
        result['reverse_source_turns'] = variant_program(settings,turn_map=(0,3,2,1))
        result['stale_unoriented_dimensions'] = variant_program(settings,stale_dimensions=True)
        for side,index in SIDE_TURNS.items():
            wrong = list(range(4));wrong[index]=(index+1)%4
            result['wrong_mapping_'+side] = variant_program(settings,turn_map=tuple(wrong))
    return result
