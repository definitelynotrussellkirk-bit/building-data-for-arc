#lang racket
;; Layer operations for ARC grids
;;
;; A "layer" = all cells of one color. The grid is a stack of 10 layers (colors 0-9).
;; Operations: extract, rotate, shift, swap, overlay, and per-layer transforms.
;; Also: automated invariance analysis — which decomposition makes the rule simplest?

(provide (all-defined-out))

;; ============================================================
;; Layer extraction and recombination
;; ============================================================

(define (layer-extract g color)
  ;; Binary mask: 1 where grid has this color, 0 elsewhere
  (for/list ([row (in-list g)])
    (for/list ([v (in-list row)])
      (if (= v color) 1 0))))

(define (layer-cells g color)
  ;; List of (r c) positions where grid == color
  (define h (length g))
  (define w (length (first g)))
  (for*/list ([r (in-range h)] [c (in-range w)]
              #:when (= (list-ref (list-ref g r) c) color))
    (list r c)))

(define (layer-set g color cells)
  ;; Place color at given positions, bg elsewhere for those positions
  (define h (length g))
  (define w (length (first g)))
  (define cell-set (list->set (map (lambda (p) (cons (first p) (second p))) cells)))
  (for/list ([r (in-range h)])
    (for/list ([c (in-range w)])
      (if (set-member? cell-set (cons r c))
          color
          (list-ref (list-ref g r) c)))))

(define (layer-remove g color [bg 0])
  ;; Remove all cells of this color (replace with bg)
  (for/list ([row (in-list g)])
    (for/list ([v (in-list row)])
      (if (= v color) bg v))))

(define (layer-swap g c1 c2)
  ;; Swap two colors spatially
  (for/list ([row (in-list g)])
    (for/list ([v (in-list row)])
      (cond [(= v c1) c2] [(= v c2) c1] [else v]))))

;; ============================================================
;; Per-layer transforms
;; ============================================================

(define (layer-bbox g color)
  ;; Bounding box of a color layer: (r1 c1 r2 c2) or #f if empty
  (define cells (layer-cells g color))
  (if (empty? cells) #f
      (let ([rs (map first cells)] [cs (map second cells)])
        (list (apply min rs) (apply min cs) (apply max rs) (apply max cs)))))

(define (layer-rotate g color direction [bg 0])
  ;; Rotate just the cells of this color within their bbox
  ;; direction: 'cw 'ccw '180
  (define bb (layer-bbox g color))
  (if (not bb) g
      (let* ([r1 (first bb)] [c1 (second bb)]
             [r2 (third bb)] [c2 (fourth bb)]
             [bh (add1 (- r2 r1))] [bw (add1 (- c2 c1))]
             ;; Extract sub-grid, keep only this color
             [sub (for/list ([r (in-range r1 (add1 r2))])
                    (for/list ([c (in-range c1 (add1 c2))])
                      (let ([v (list-ref (list-ref g r) c)])
                        (if (= v color) color bg))))]
             ;; Rotate the sub-grid
             [rotated (match direction
                        ['cw (let ([t (apply map list sub)]) ;; transpose
                               (map reverse t))]
                        ['ccw (let ([t (apply map list sub)])
                                (reverse t))]
                        ['180 (map reverse (reverse sub))])]
             ;; Compute new bbox dimensions
             [nh (length rotated)]
             [nw (length (first rotated))]
             ;; Center the rotated sub in the original bbox center
             [cr (+ r1 (quotient (- bh nh) 2))]
             [cc (+ c1 (quotient (- bw nw) 2))])
        ;; Remove old layer, paste rotated
        (define h (length g))
        (define w (length (first g)))
        (define cleared (layer-remove g color bg))
        (for/list ([r (in-range h)])
          (for/list ([c (in-range w)])
            (let ([lr (- r cr)] [lc (- c cc)])
              (if (and (>= lr 0) (< lr nh) (>= lc 0) (< lc nw))
                  (let ([rv (list-ref (list-ref rotated lr) lc)])
                    (if (= rv color) color (list-ref (list-ref cleared r) c)))
                  (list-ref (list-ref cleared r) c))))))))

(define (layer-shift g color dr dc [bg 0])
  ;; Shift all cells of this color by (dr, dc)
  (define h (length g))
  (define w (length (first g)))
  (define cells (layer-cells g color))
  (define cleared (layer-remove g color bg))
  (define new-cells
    (filter (lambda (p) (and (>= (first p) 0) (< (first p) h)
                             (>= (second p) 0) (< (second p) w)))
            (map (lambda (p) (list (+ (first p) dr) (+ (second p) dc))) cells)))
  (layer-set cleared color new-cells))

(define (layer-flip g color axis [bg 0])
  ;; Flip a layer within its bbox. axis: 'lr or 'ud
  (define bb (layer-bbox g color))
  (if (not bb) g
      (let* ([r1 (first bb)] [c1 (second bb)]
             [r2 (third bb)] [c2 (fourth bb)]
             [cells (layer-cells g color)]
             [flipped (map (lambda (p)
               (match axis
                 ['lr (list (first p) (- (+ c1 c2) (second p)))]
                 ['ud (list (- (+ r1 r2) (first p)) (second p))])) cells)]
             [cleared (layer-remove g color bg)])
        (layer-set cleared color flipped))))

(define (for-each-layer g fn [bg 0])
  ;; Apply fn to each non-bg color's cells independently.
  ;; fn takes (grid color) → grid
  (define colors (remove-duplicates
    (filter (lambda (v) (not (= v bg)))
            (append* g))))
  (foldl (lambda (color acc) (fn acc color)) g colors))

;; ============================================================
;; Invariance analysis — which layers changed?
;; ============================================================

(define (layer-diff g1 g2 color)
  ;; How many cells of this color differ between g1 and g2?
  ;; Returns (changed-count total-in-g1 total-in-g2)
  (define h (length g1))
  (define w (length (first g1)))
  (define mask1 (layer-extract g1 color))
  (define mask2 (layer-extract g2 color))
  (define changed 0)
  (define total1 0)
  (define total2 0)
  (for* ([r (in-range h)] [c (in-range w)])
    (define v1 (list-ref (list-ref mask1 r) c))
    (define v2 (list-ref (list-ref mask2 r) c))
    (when (= v1 1) (set! total1 (add1 total1)))
    (when (= v2 1) (set! total2 (add1 total2)))
    (when (not (= v1 v2)) (set! changed (add1 changed))))
  (list changed total1 total2))

(define (invariance-report g1 g2 [bg-hint #f])
  ;; For each color, report: how much changed between g1 and g2?
  ;; Returns list of (color changed total1 total2 status)
  ;; status: 'invariant 'modified 'added 'removed
  (define all-colors (sort (remove-duplicates
    (append (append* g1) (append* g2))) <))
  (for/list ([color (in-list all-colors)])
    (define diff (layer-diff g1 g2 color))
    (define changed (first diff))
    (define t1 (second diff))
    (define t2 (third diff))
    (define status
      (cond
        [(= changed 0) 'invariant]
        [(= t1 0) 'added]
        [(= t2 0) 'removed]
        [else 'modified]))
    (list color changed t1 t2 status)))

(define (invariant-layers g1 g2)
  ;; Which colors didn't change at all?
  (define report (invariance-report g1 g2))
  (filter-map (lambda (entry)
    (if (eq? (fifth entry) 'invariant) (first entry) #f))
    report))

(define (modified-layers g1 g2)
  ;; Which colors changed?
  (define report (invariance-report g1 g2))
  (filter-map (lambda (entry)
    (if (not (eq? (fifth entry) 'invariant)) (first entry) #f))
    report))

(define (simplest-decomposition g1 g2)
  ;; Find the decomposition with the fewest changes.
  ;; Tests: raw layers, heightmap layers, color-lattice layers.
  ;; Returns (method invariant-count modified-count details)
  (define report (invariance-report g1 g2))
  (define n-invariant (count (lambda (e) (eq? (fifth e) 'invariant)) report))
  (define n-modified (count (lambda (e) (not (eq? (fifth e) 'invariant))) report))
  (define total-changed (apply + (map second report)))

  (list 'per-color n-invariant n-modified total-changed
        (filter (lambda (e) (not (eq? (fifth e) 'invariant))) report)))

(define (analyze-task-layers pairs)
  ;; For a list of (input . output) pairs, find consistent invariants
  ;; Returns: colors that are invariant across ALL pairs
  (if (empty? pairs) '()
      (let* ([first-inv (invariant-layers (car (first pairs)) (cdr (first pairs)))]
             [consistent (foldl (lambda (pair acc)
               (define inv (list->set (invariant-layers (car pair) (cdr pair))))
               (filter (lambda (c) (set-member? inv c)) acc))
               first-inv (rest pairs))])
        consistent)))
