"""Exact color-selection shortcuts motivated by the bounded native review."""

INNER_BINDINGS = '''(points (map (lambda (cell) (list (first cell) (second cell))) cells))
 (inner? (lambda (cell) (andmap (lambda (d)
   (member (list (+ (first cell) (first d)) (+ (second cell) (second d))) points))
   (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))))
 (inside-count (lambda (color) (count-where (lambda (cell)
   (and (= (third cell) color) (inner? cell))) cells)))'''

EXPRESSIONS = {
 'most_components_numeric_tie': '''(let* ((components (objects g 8))
  (score (lambda (color) (count-where (lambda (obj) (= (obj-color obj) color)) components))))
  (car (sort (hash-keys freq) (lambda (a b)
   (if (= (score a) (score b)) (< a b) (> (score a) (score b)))))))''',
 'fewest_interior_cells': f'''(let* ({INNER_BINDINGS})
  (car (sort (hash-keys freq) (lambda (a b)
   (if (= (inside-count a) (inside-count b)) (< a b) (< (inside-count a) (inside-count b)))))))''',
 'highest_fully_enclosed': f'''(let* ({INNER_BINDINGS}
  (enclosed? (lambda (color) (= (inside-count color) (hash-ref freq color 0)))))
  (car (sort (hash-keys freq) (lambda (a b)
   (if (equal? (enclosed? a) (enclosed? b)) (> a b) (enclosed? a))))))''',
}


def programs(family, settings):
    return {name: family.variant_program(settings, color_expression=expression)
            for name, expression in EXPRESSIONS.items()}
