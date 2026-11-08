"""Finite executable shortcut rivals for the marker-assignment family.

The inventory is intentionally bounded and explicit.  ``assignment`` and
``output`` provide Python predictions for fast lesson censuses; ``programs``
materializes independent complete Racket rules so the audit can prove those
predictions against the same protected runtime used for qualification.
"""
from __future__ import annotations

NAMES = (
    "greedy_unique",
    "spatial_pairing",
    "reverse_spatial_pairing",
    "nearest_shape_cell",
    "independent_farthest",
    "first_marker_all",
    "color_order",
    "center_nearest",
)

DESCRIPTIONS = {
    "greedy_unique": "assign each output-ordered shape its nearest unused marker",
    "spatial_pairing": "pair output-ordered shapes with markers in the same axis order",
    "reverse_spatial_pairing": "pair output-ordered shapes with markers in reverse axis order",
    "nearest_shape_cell": "choose the marker nearest an occupied shape cell, not its bounding box",
    "independent_farthest": "independently choose the farthest marker",
    "first_marker_all": "reuse the first reverse-row-major marker for every shape",
    "color_order": "pair output-ordered shapes with markers in ascending color order",
    "center_nearest": "independently choose the marker nearest the integer bbox center",
}

_TEMPLATE = r"""(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g)))
    (let* ((all-objs (objects g 0))
           (shapes (filter (lambda (o) (= (obj-color o) 6)) all-objs))
           (markers (let ((s (list)))
                      (for* ((r (range 0 h)) (c (range 0 w)))
                        (let ((v (at g r c)))
                          (when (and (!= v 0) (!= v 6))
                            (set! s (cons (list r c v) s)))))
                      s))
           (dist-to-bbox
             (lambda (mr mc r1 r2 c1 c2)
               (let ((dr (if (and (<= r1 mr) (<= mr r2))
                             0
                             (min (abs (- mr r1)) (abs (- mr r2)))))
                     (dc (if (and (<= c1 mc) (<= mc c2))
                             0
                             (min (abs (- mc c1)) (abs (- mc c2))))))
                 (+ dr dc))))
           (is-vertical (> h w))
           (shape-key
             (lambda (shape)
               (with-bbox shape (r1 c1 r2 c2)
                 (if is-vertical r1 c1))))
           (sorted-shapes
             (sort shapes (lambda (a b) (< (shape-key a) (shape-key b)))))
           (assigned-markers __ASSIGNED__)
           (shape-info
             (let loop ((ss sorted-shapes) (ms assigned-markers) (out (list)))
               (if (null? ss)
                   (reverse out)
                   (let* ((shape (car ss))
                          (marker (car ms))
                          (cells (obj-cells shape)))
                     (with-bbox shape (r1 c1 r2 c2)
                       (loop (cdr ss)
                             (cdr ms)
                             (cons (list cells r1 r2 c1 c2 (third marker)) out)))))))
           (n (length shape-info))
           (out-h (if is-vertical (* n 4) 4))
           (out-w (if is-vertical 4 (* n 4))))
      (build-grid out-h out-w (gr gc)
        (let* ((idx (if is-vertical (quotient gr 4) (quotient gc 4)))
               (base-r (if is-vertical (* idx 4) 0))
               (base-c (if is-vertical 0 (* idx 4)))
               (lr (- gr base-r))
               (lc (- gc base-c))
               (shape (list-ref shape-info idx))
               (cells (first shape))
               (sr1 (second shape))
               (sc1 (fourth shape))
               (color (sixth shape)))
          (let check ((cs cells))
            (cond ((null? cs) 0)
                  ((and (= (first (car cs)) (+ sr1 lr))
                        (= (second (car cs)) (+ sc1 lc))) color)
                  (else (check (cdr cs)))))))))))"""

_NEAREST = r"""(map
  (lambda (shape)
    (with-bbox shape (r1 c1 r2 c2)
      (let loop ((ms markers) (best #f) (best-dist 99999))
        (if (null? ms)
            best
            (let* ((m (car ms))
                   (d (dist-to-bbox (first m) (second m) r1 r2 c1 c2)))
              (if (< d best-dist)
                  (loop (cdr ms) m d)
                  (loop (cdr ms) best best-dist)))))))
  sorted-shapes)"""

_ASSIGNMENTS = {
    "greedy_unique": r"""(letrec
  ((remove-marker
     (lambda (target xs)
       (cond ((null? xs) (list))
             ((equal? (car xs) target) (cdr xs))
             (else (cons (car xs) (remove-marker target (cdr xs)))))))
   (nearest-marker
     (lambda (shape choices)
       (with-bbox shape (r1 c1 r2 c2)
         (let loop ((ms choices) (best #f) (best-dist 99999))
           (if (null? ms)
               best
               (let* ((m (car ms))
                      (d (dist-to-bbox (first m) (second m) r1 r2 c1 c2)))
                 (if (< d best-dist)
                     (loop (cdr ms) m d)
                     (loop (cdr ms) best best-dist))))))))
   (assign
     (lambda (ss choices out)
       (if (null? ss)
           (reverse out)
           (let ((chosen (nearest-marker (car ss) choices)))
             (assign (cdr ss)
                     (remove-marker chosen choices)
                     (cons chosen out)))))))
  (assign sorted-shapes markers (list)))""",
    "spatial_pairing": r"""(sort markers
  (lambda (a b)
    (let ((ka (if is-vertical (first a) (second a)))
          (kb (if is-vertical (first b) (second b))))
      (if (= ka kb)
          (if is-vertical
              (< (second a) (second b))
              (< (first a) (first b)))
          (< ka kb)))))""",
    "reverse_spatial_pairing": r"""(sort markers
  (lambda (a b)
    (let ((ka (if is-vertical (first a) (second a)))
          (kb (if is-vertical (first b) (second b))))
      (if (= ka kb)
          (if is-vertical
              (> (second a) (second b))
              (> (first a) (first b)))
          (> ka kb)))))""",
    "nearest_shape_cell": r"""(map
  (lambda (shape)
    (let ((cells (obj-cells shape)))
      (let loop ((ms markers) (best #f) (best-dist 99999))
        (if (null? ms)
            best
            (let* ((m (car ms))
                   (d (let cell-loop ((cs cells) (cell-best 99999))
                        (if (null? cs)
                            cell-best
                            (let ((cell (car cs)))
                              (cell-loop
                                (cdr cs)
                                (min cell-best
                                     (+ (abs (- (first m) (first cell)))
                                        (abs (- (second m) (second cell)))))))))))
              (if (< d best-dist)
                  (loop (cdr ms) m d)
                  (loop (cdr ms) best best-dist)))))))
  sorted-shapes)""",
    "independent_farthest": r"""(map
  (lambda (shape)
    (with-bbox shape (r1 c1 r2 c2)
      (let loop ((ms markers) (best #f) (best-dist -1))
        (if (null? ms)
            best
            (let* ((m (car ms))
                   (d (dist-to-bbox (first m) (second m) r1 r2 c1 c2)))
              (if (> d best-dist)
                  (loop (cdr ms) m d)
                  (loop (cdr ms) best best-dist)))))))
  sorted-shapes)""",
    "first_marker_all": r"""(map (lambda (shape) (first markers)) sorted-shapes)""",
    "color_order": r"""(sort markers (lambda (a b) (< (third a) (third b))))""",
    "center_nearest": r"""(map
  (lambda (shape)
    (with-bbox shape (r1 c1 r2 c2)
      (let ((cr (quotient (+ r1 r2) 2))
            (cc (quotient (+ c1 c2) 2)))
        (let loop ((ms markers) (best #f) (best-dist 99999))
          (if (null? ms)
              best
              (let* ((m (car ms))
                     (d (+ (abs (- (first m) cr))
                           (abs (- (second m) cc)))))
                (if (< d best-dist)
                    (loop (cdr ms) m d)
                    (loop (cdr ms) best best-dist))))))))
  sorted-shapes)""",
}


def programs() -> dict[str, str]:
    result = {
        name: _TEMPLATE.replace("__ASSIGNED__", expression)
        for name, expression in _ASSIGNMENTS.items()
    }
    if tuple(result) != NAMES or len(set(result.values())) != len(result):
        raise AssertionError("rival program inventory is incomplete or duplicated")
    return result


def assignment(prototype, grid, name: str) -> list[int]:
    if name not in NAMES:
        raise ValueError(f"unknown rival: {name}")
    _height, _width, vertical, shapes, markers = prototype._scene_parts(grid)
    matrix = prototype._distance_matrix(shapes, markers)
    count = len(shapes)
    if name == "greedy_unique":
        remaining = list(range(count))
        result = []
        for distances in matrix:
            offset = min(range(len(remaining)), key=lambda i: distances[remaining[i]])
            result.append(remaining.pop(offset))
        return result
    if name in ("spatial_pairing", "reverse_spatial_pairing"):
        result = sorted(
            range(count),
            key=lambda index: (
                markers[index][0] if vertical else markers[index][1],
                markers[index][1] if vertical else markers[index][0],
            ),
            reverse=name == "reverse_spatial_pairing",
        )
        return result
    if name == "nearest_shape_cell":
        result = []
        for shape in shapes:
            distances = [
                min(abs(marker[0] - row) + abs(marker[1] - col)
                    for row, col in shape["cells"])
                for marker in markers
            ]
            result.append(min(range(count), key=lambda index: distances[index]))
        return result
    if name == "independent_farthest":
        return [max(range(count), key=lambda index: distances[index])
                for distances in matrix]
    if name == "first_marker_all":
        return [0] * count
    if name == "color_order":
        return sorted(range(count), key=lambda index: markers[index][2])
    if name == "center_nearest":
        result = []
        for shape in shapes:
            top, left, bottom, right = shape["bbox"]
            center_row = (top + bottom) // 2
            center_col = (left + right) // 2
            distances = [abs(marker[0] - center_row) + abs(marker[1] - center_col)
                         for marker in markers]
            result.append(min(range(count), key=lambda index: distances[index]))
        return result
    raise AssertionError(name)  # pragma: no cover


def output(prototype, grid, name: str):
    _height, _width, vertical, shapes, markers = prototype._scene_parts(grid)
    assigned = assignment(prototype, grid, name)
    output_height = 4 * len(shapes) if vertical else 4
    output_width = 4 if vertical else 4 * len(shapes)
    result = [[0] * output_width for _ in range(output_height)]
    for slot, (shape, marker_index) in enumerate(zip(shapes, assigned, strict=True)):
        top, left, _bottom, _right = shape["bbox"]
        base_row = 4 * slot if vertical else 0
        base_col = 0 if vertical else 4 * slot
        color = markers[marker_index][2]
        for row, col in shape["cells"]:
            result[base_row + row - top][base_col + col - left] = color
    return result
