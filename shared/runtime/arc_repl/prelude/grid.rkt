;; LEGACY — Python-evaluator-only grid helpers.
;; The canonical Racket bridge uses `racket_prelude/arc-prelude.rkt`;
;; nothing here is callable from a grounded rule run in Racket mode.
;; Kept so the Python evaluator fallback still resolves these names.
;; Don't add to this file; new primitives go in arc-prelude.rkt.

;; Recolor: replace all cells of src with dst
(define (recolor* grid src dst)
  (map-grid grid (lambda (r c v) (if (= v src) dst v))))

;; Remove all cells of a color (set to 0)
(define (remove-color* grid color)
  (recolor* grid color 0))

;; Keep only one color, zero everything else
(define (keep-only* grid color)
  (map-grid grid (lambda (r c v) (if (= v color) v 0))))

;; Apply a color mapping dict
(define (recolor-map* grid mapping)
  (map-grid grid (lambda (r c v) (dict-get mapping v v))))

;; Swap two colors
(define (swap-colors* grid c1 c2)
  (map-grid grid (lambda (r c v)
    (cond ((= v c1) c2) ((= v c2) c1) (else v)))))

;; Invert colors (c → 9-c for non-zero)
(define (invert-colors* grid)
  (map-grid grid (lambda (r c v) (if (= v 0) 0 (- 9 v)))))

;; Fill enclosed regions with a color
(define (fill-enclosed* grid color)
  (set-cells grid (mask->cells (where-enclosed grid)) color))

;; Find all positions of a color
(define (find-color* grid color)
  (mask->cells (grid-where grid (lambda (v) (= v color)))))

;; Count cells of a color
(define (count-color* grid color)
  (length (find-color* grid color)))

;; Color filter: returns a predicate
(define (color-filter* c) (lambda (r col v) (= v c)))
(define (not-color-filter* c) (lambda (r col v) (!= v c)))

;; Const target: always returns the same value
(define (const-target* val) (lambda (r c v) val))

;; Apply filter+target composition
(define (apply-filtered* grid filter-fn target-fn)
  (map-grid grid (lambda (r c v)
    (if (filter-fn r c v) (target-fn r c v) v))))

;; Fill a rectangular region with a color
(define (fill-rect grid r1 c1 r2 c2 color)
  (map-grid grid (lambda (r c v)
    (if (and (>= r r1) (<= r r2) (>= c c1) (<= c c2)) color v))))

;; Fill a row/col with a color
(define (fill-row* grid row color)
  (map-grid grid (lambda (r c v) (if (= r row) color v))))
(define (fill-col* grid col color)
  (map-grid grid (lambda (r c v) (if (= c col) color v))))

;; Fill border with a color
(define (fill-border* grid color)
  (let ((h (rows grid)) (w (cols grid)))
    (map-grid grid (lambda (r c v)
      (if (or (= r 0) (= r (- h 1)) (= c 0) (= c (- w 1))) color v)))))

;; Is a cell isolated? (no same-color 8-connected neighbors)
(define (isolated? grid r c)
  (= 0 (neighbor-count-8 grid r c (cell-at grid r c))))

;; Remove all isolated pixels
(define (remove-isolated grid)
  (apply-filtered grid (make-isolated-filter grid 8) (const-target 0)))

;; Z-stack: overlay grids with later ones on top (non-zero overwrites)
;; (z-stack base (list layer1 layer2 ...)) — layer2 in front of layer1
(define (z-stack base layers)
  (reduce (lambda (acc layer) (grid+ acc layer)) base layers))

;; Paint a full row/col stripe onto a grid
(define (row-stripe grid row color)
  (grid-from-fn (rows grid) (cols grid)
    (lambda (r c) (if (= r row) color (cell-at grid r c)))))

(define (col-stripe grid col color)
  (grid-from-fn (rows grid) (cols grid)
    (lambda (r c) (if (= c col) color (cell-at grid r c)))))

;; Paint multiple row stripes at once: (row-stripes grid ((row1 color1) (row2 color2) ...))
(define (row-stripes grid pairs)
  (reduce (lambda (g pair) (row-stripe g (fst pair) (snd pair))) grid pairs))

(define (col-stripes grid pairs)
  (reduce (lambda (g pair) (col-stripe g (fst pair) (snd pair))) grid pairs))
