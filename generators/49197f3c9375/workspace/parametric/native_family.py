"""Select the unmatched full D4 shape, then render a region of that object."""
from pathlib import Path

from reviewer_support import load_selected_generator

HERE = Path(__file__).resolve().parent
_selected, _, _ = load_selected_generator('49197f3c9375', root=HERE.parents[3])
MODES = ('boundary', 'whole', 'interior')
CANONICAL = (HERE / 'canonical.rkt').read_text(encoding='utf-8')
REGION = '(obj-boundary-cells target)'
TARGET = '(define target (first (filter (lambda (obj) (equal? (signature obj) target-sig)) objs)))'
TARGET_SIG = '(define target-sig (first (filter (lambda (sig) (= (count-where (lambda (obj) (equal? (signature obj) sig)) objs) 1)) sigs)))'
BOX = '(bbox-of-cells (obj-cells target))'
for _site in (REGION, TARGET, TARGET_SIG, BOX, '(define (signature obj)', '(define objs (objects g 0))', '(obj-color target)'):
    if CANONICAL.count(_site) != 1:
        raise ValueError('selected canonical substitution sites must each be unique')


def parse_settings(settings):
    if (type(settings) is not dict or set(settings) != {'render'}
            or type(settings['render']) is not str or settings['render'] not in MODES):
        raise ValueError('settings must contain exactly render=boundary, whole or interior')
    return {'render': settings['render']}


def validate_grid(grid):
    if (type(grid) is not list or not 8 <= len(grid) <= 30
            or type(grid[0]) is not list or not 15 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError('need a rectangular exact-integer ARC grid of 8..30 by 15..30')
    motifs, groups, target, relations, color_counts = _selected._semantic_facts(grid)
    if (len(motifs) not in (5, 7, 9)
            or sorted(map(len, groups.values())) != [1] + [2] * ((len(motifs) - 1) // 2)
            or target is None):
        raise ValueError('need 5, 7 or 9 components: one singleton full-D4 class and paired remaining classes')
    others = [obj for obj in motifs if obj is not target]
    dims = sorted((target['height'], target['width']))
    if (not any(obj['size'] == target['size'] for obj in others)
            or not any(sorted((obj['height'], obj['width'])) == dims for obj in others)):
        raise ValueError('target area and bbox must each also occur on another component')
    return {'motifs': motifs, 'groups': groups, 'target': target, 'relations': relations,
            'color_counts': color_counts, 'target_rank': motifs.index(target)}


def apply(grid, settings):
    mode = parse_settings(settings)['render']
    target = validate_grid(grid)['target']
    if mode in ('boundary', 'whole'):
        return _selected._render_object(target, boundary_only=mode == 'boundary')
    occupied = set(target['local'])
    return [[target['color'] if (r, c) in occupied and all(
                (r + dr, c + dc) in occupied for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
             else 0 for c in range(target['width'])] for r in range(target['height'])]


def region_expression(mode, obj='target'):
    if mode == 'boundary':
        return f'(obj-boundary-cells {obj})'
    if mode == 'whole':
        return f'(obj-cells {obj})'
    return f'(filter (lambda (p) (not (member p (obj-boundary-cells {obj})))) (obj-cells {obj}))'


def variant_program(settings, *, target_expression=None, signature_expression=None,
                    cells_expression=None, bbox_expression=None, color_expression=None,
                    definitions=''):
    """Guarded native changes and explicit, total audit counterfactuals."""
    mode = parse_settings(settings)['render']
    result = CANONICAL.replace(REGION, cells_expression or region_expression(mode), 1)
    if target_expression is not None:
        result = result.replace(TARGET, f'(define target {target_expression})', 1)
    if signature_expression is not None:
        result = result.replace('(define (signature obj)', '(define (d4-signature obj)', 1)
        definitions += f'\n(define (signature obj) {signature_expression})'
        # A failed grouping heuristic still produces an object, rather than an
        # exception masquerading as a refuted semantic prediction.
        result = result.replace(TARGET_SIG,
            '(define target-sig (let ((singletons (filter (lambda (sig) (= (count-where '
            '(lambda (obj) (equal? (signature obj) sig)) objs) 1)) sigs))) '
            '(if (empty? singletons) (first sigs) (first singletons))))', 1)
    if bbox_expression is not None:
        result = result.replace(BOX, bbox_expression, 1)
    if color_expression is not None:
        result = result.replace('(obj-color target)', color_expression, 1)
    if definitions:
        needle = '(define objs (objects g 0))'
        result = result.replace(needle, definitions + '\n' + needle, 1)
    return result


def program(settings):
    mode = parse_settings(settings)['render']
    return CANONICAL if mode == 'boundary' else variant_program(settings)


def _signature_for(cells, rotations_only=False):
    choices = ('(for/list ((k (in-range 4))) (rotate pts k))' if rotations_only else
        '(apply append (for/list ((k (in-range 4))) '
        '(let ((r (rotate pts k))) (list r (mirror-h r)))))')
    return (f'(let* ((pts (normalize {cells})) (vars (remove-duplicates {choices}))) '
            + '(first (sort vars (lambda (a b) (string<? (format "~a" a) (format "~a" b))))))')


def rivals(settings):
    """Finite plausible shortcuts; the auditor also adds alternative settings."""
    mode = parse_settings(settings)['render']
    box_cells = '(let ((box (bbox-of-cells (obj-cells target)))) (for*/list ((r (in-range (first box) (+ 1 (third box)))) (c (in-range (second box) (+ 1 (fourth box))))) (list r c)))'
    frame = '(let ((box (bbox-of-cells (obj-cells target)))) (filter (lambda (p) (or (= (first p) (first box)) (= (first p) (third box)) (= (second p) (second box)) (= (second p) (fourth box)))) (obj-cells target)))'
    menu = {
        'first_component': variant_program(settings, target_expression='(first objs)'),
        'last_component': variant_program(settings, target_expression='(last objs)'),
        'middle_component': variant_program(settings, target_expression='(list-ref objs (/ (- (length objs) 1) 2))'),
        'smallest_component': variant_program(settings, target_expression='(first (sort objs (lambda (a b) (< (length (obj-cells a)) (length (obj-cells b))))))'),
        'largest_component': variant_program(settings, target_expression='(first (sort objs (lambda (a b) (> (length (obj-cells a)) (length (obj-cells b))))))'),
        'lowest_color': variant_program(settings, target_expression='(first (sort objs (lambda (a b) (< (obj-color a) (obj-color b)))))'),
        'unique_area': variant_program(settings, signature_expression='(length (obj-cells obj))'),
        'unique_bbox': variant_program(settings, signature_expression='(let ((box (bbox-of-cells (obj-cells obj)))) (sort (list (- (third box) (first box)) (- (fourth box) (second box))) <))'),
        'unique_color': variant_program(settings, signature_expression='(obj-color obj)'),
        'translation_grouping': variant_program(settings, signature_expression='(normalize (obj-cells obj))'),
        'rotation_only_grouping': variant_program(settings, signature_expression=_signature_for('(obj-cells obj)', True)),
        'boundary_before_grouping': variant_program(settings, signature_expression=_signature_for('(obj-boundary-cells obj)')),
        'filled_bounding_box': variant_program(settings, cells_expression=box_cells),
        'bbox_frame_only': variant_program(settings, cells_expression=frame),
        'fixed_output_color': variant_program(settings, color_expression='1'),
    }
    if mode == 'interior':
        region = region_expression(mode)
        menu['crop_interior_tightly'] = variant_program(settings,
            bbox_expression=f'(if (empty? {region}) (bbox-of-cells (obj-cells target)) (bbox-of-cells {region}))')
    menu.update(retained_rivals(settings))
    return menu


# Exact protected programs retained from the independent teaching review.
PERIMETER = '''(apply + (map (lambda (p) (count-where
 (lambda (d) (not (member (list (+ (first p) (first d)) (+ (second p) (second d))) (obj-cells obj))))
 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))) (obj-cells obj)))'''

ORBIT_DEFINITION = '''(define (orbit-size obj)
 (let ((pts (normalize (obj-cells obj))))
  (length (remove-duplicates (list pts (rotate pts 1) (rotate pts 2) (rotate pts 3)
   (mirror-h pts) (mirror-h (rotate pts 1)) (mirror-h (rotate pts 2)) (mirror-h (rotate pts 3)))))))'''

INTERIOR_COUNT = '(- (length (obj-cells obj)) (length (obj-boundary-cells obj)))'

PROJECTION = '''(let* ((cells (obj-cells obj))
 (rows (remove-duplicates (map first cells)))
 (cols (remove-duplicates (map second cells)))
 (row-counts (sort (map (lambda (r) (count-where (lambda (p) (= (first p) r)) cells)) rows) <))
 (col-counts (sort (map (lambda (c) (count-where (lambda (p) (= (second p) c)) cells)) cols) <)))
 (sort (list row-counts col-counts) (lambda (a b) (string<? (format "~a" a) (format "~a" b)))))'''


def retained_rivals(settings):
    """Return exact total rivals, preserving the selected rendering setting.

    Feature grouping uses family's explicit first-component fallback when no
    feature class is unique. Minimum-orbit selection uses stable scan-order
    tie breaking. Every program was motivated by an observed baseline hole.
    """
    return {
        'unique_perimeter': variant_program(settings, signature_expression=PERIMETER),
        'unique_perimeter_and_interior': variant_program(
            settings, signature_expression=f'(list {PERIMETER} {INTERIOR_COUNT})'),
        'unique_d4_orbit_size': variant_program(
            settings, signature_expression='(orbit-size obj)', definitions=ORBIT_DEFINITION),
        'unique_projection_histogram': variant_program(settings, signature_expression=PROJECTION),
        'most_symmetric': variant_program(settings, definitions=ORBIT_DEFINITION,
            target_expression='(first (sort objs (lambda (a b) (< (orbit-size a) (orbit-size b)))))'),
    }
