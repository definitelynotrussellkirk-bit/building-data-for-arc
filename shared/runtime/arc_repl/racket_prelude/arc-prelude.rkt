#lang racket
;; ARC-AGI-2 Grid Prelude for Racket
;; Provides all grid primitives used by grounded rules.
;; Grids are list-of-lists of integers.
(provide (all-defined-out))

;; ============================================================
;; Core aliases (compatibility with our S-expression subset)
;; ============================================================
;; Pair accessors — handle both proper lists and dotted pairs
(define (fst p) (car p))
(define (snd p) (if (and (pair? p) (not (list? p)))
                    (cdr p)    ;; dotted pair: (a . b) → b
                    (second p))) ;; proper list: (a b ...) → b
(define (third-elem p) (third p))
;; re-export 'third' as well for direct use
(define (nth lst i) (list-ref lst i))

;; Dict operations — our dicts are hash tables
(define (dict-get d k [default #f])
  (hash-ref d k (lambda () default)))
(define (dict-keys d) (hash-keys d))
(define (dict-values d) (hash-values d))

;; List utilities
(define (arc-null? x) (or (eq? x #f) (and (list? x) (empty? x)) (void? x)))

;; Safe range: treat #f as 0
(define (safe-range . args)
  (apply range (map (lambda (a) (if (eq? a #f) 0 (if (exact-integer? a) a (inexact->exact (floor a))))) args)))
(define (flatmap fn lst) (append* (map fn lst)))
(define (flat-map fn lst) (flatmap fn lst))
(define (count-where fn lst) (count fn lst))
(define (count-if fn lst) (count-where fn lst))
(define (min-list lst) (apply min lst))
(define (max-list lst) (apply max lst))
(define (sum-list lst) (apply + lst))
(define (mean-list lst) (if (empty? lst) 0 (/ (apply + lst) (length lst))))
(define (zip-lists . lsts) (apply map list lsts))
(define (enumerate-list lst)
  (for/list ([v (in-list lst)] [i (in-naturals)]) (list i v)))
(define (find-first fn lst)
  (for/first ([v (in-list lst)] #:when (fn v)) v))
(define (any? fn lst) (ormap fn lst))
(define (all? fn lst) (andmap fn lst))
(define (unique lst) (sort (set->list (list->set lst)) <))
(define (member? x lst) (and (member x lst) #t))

;; Pipe and compose
(define (pipe . fns)
  (lambda (x) (foldl (lambda (fn val) (fn val)) x fns)))
(define (compose . fns)
  (lambda (x) (foldr (lambda (fn val) (fn val)) x fns)))
(define (identity x) x)

;; cell< — lexicographic compare on (r c) cell pairs.
;; Frequency: 200+ corpus rules redefined this locally; promoted to
;; prelude after Phase 4 of the local-helper cleanup.
(define (cell< a b) (if (= (first a) (first b)) (< (second a) (second b)) (< (first a) (first b))))

;; ============================================================
;; Grid basics
;; ============================================================
(define (rows g) (length g))
(define (cols g) (if (empty? g) 0 (length (first g))))
(define (cell-at g r c) (list-ref (list-ref g r) c))
(define (grid-from-fn h w fn)
  (for/list ([r (in-range h)])
    (for/list ([c (in-range w)])
      (fn r c))))

(define (empty-grid h w [fill 0])
  (grid-from-fn h w (lambda (r c) fill)))

(define (set-cell g r c v)
  (for/list ([ri (in-range (rows g))])
    (for/list ([ci (in-range (cols g))])
      (if (and (= ri r) (= ci c)) v (cell-at g ri ci)))))

(define (map-grid g fn)
  (grid-from-fn (rows g) (cols g)
    (lambda (r c) (fn r c (cell-at g r c)))))

;; Grid colors (all distinct values, optionally excluding bg)
(define (grid-colors g [bg -999])
  (define vals (set->list
    (for*/set ([row (in-list g)] [v (in-list row)]
               #:when (not (= v bg)))
      v)))
  (sort vals <))

;; Color frequency
(define (color-frequency g)
  (define h (make-hash))
  (for* ([row (in-list g)] [v (in-list row)])
    (hash-update! h v add1 0))
  h)

;; Find all positions of a color
(define (find-color g color)
  (for*/list ([r (in-range (rows g))]
              [c (in-range (cols g))]
              #:when (= (cell-at g r c) color))
    (list r c)))

;; Mode (most common non-bg value)
(define (mode g [bg 0])
  (define freq (color-frequency g))
  (hash-remove! freq bg)
  (if (hash-empty? freq) bg
      (car (argmax cdr (hash->list freq)))))

;; Minority (least common non-bg value)
(define (minority g [bg 0])
  (define freq (color-frequency g))
  (hash-remove! freq bg)
  (if (hash-empty? freq) bg
      (car (argmin cdr (hash->list freq)))))

;; ============================================================
;; Subgrid / paste / overlay
;; ============================================================
(define (subgrid g r1 c1 r2 c2)
  (for/list ([r (in-range r1 (add1 r2))])
    (for/list ([c (in-range c1 (add1 c2))])
      (cell-at g r c))))

(define (paste g sub r0 c0)
  (define sh (rows sub))
  (define sw (cols sub))
  (grid-from-fn (rows g) (cols g)
    (lambda (r c)
      (if (and (>= r r0) (< r (+ r0 sh))
               (>= c c0) (< c (+ c0 sw)))
          (cell-at sub (- r r0) (- c c0))
          (cell-at g r c)))))

(define (overlay g1 g2 [bg 0])
  (grid-from-fn (rows g1) (cols g1)
    (lambda (r c)
      (define v2 (cell-at g2 r c))
      (if (= v2 bg) (cell-at g1 r c) v2))))

(define (overlay-all grids [bg 0])
  (foldl (lambda (g acc) (overlay acc g bg)) (first grids) (rest grids)))

;; ============================================================
;; Transforms
;; ============================================================
(define (flip-lr g)
  (map reverse g))

(define (flip-ud g)
  (reverse g))

(define (transpose g)
  (if (empty? g) '()
      (apply map list g)))

(define (rotate-cw g)
  (flip-lr (transpose g)))

(define (rotate-ccw g)
  (transpose (flip-lr g)))

(define (rotate-180 g)
  (flip-ud (flip-lr g)))

(define (crop-to-content g [bg 0])
  (define h (rows g))
  (define w (cols g))
  (define (has-content? r c) (not (= (cell-at g r c) bg)))
  (define r1 (for/first ([r (in-range h)] #:when (for/or ([c (in-range w)]) (has-content? r c))) r))
  (define r2 (for/last  ([r (in-range h)] #:when (for/or ([c (in-range w)]) (has-content? r c))) r))
  (define c1 (for/first ([c (in-range w)] #:when (for/or ([r (in-range h)]) (has-content? r c))) c))
  (define c2 (for/last  ([c (in-range w)] #:when (for/or ([r (in-range h)]) (has-content? r c))) c))
  (if (or (not r1) (not c1)) '(()) (subgrid g r1 c1 r2 c2)))

;; ============================================================
;; Recolor operations
;; ============================================================
(define (recolor g from to)
  (map-grid g (lambda (r c v) (if (= v from) to v))))

(define (recolor-map g mapping)
  ;; mapping is a hash
  (map-grid g (lambda (r c v) (hash-ref mapping v v))))

(define (swap-colors g c1 c2)
  (map-grid g (lambda (r c v)
    (cond [(= v c1) c2] [(= v c2) c1] [else v]))))

(define (remove-color g color [bg 0])
  (recolor g color bg))

(define (keep-only g color [bg 0])
  (map-grid g (lambda (r c v) (if (= v color) v bg))))

;; ============================================================
;; Object detection (connected components)
;; ============================================================

;; Internal: BFS connected components
(define (find-objects g bg connectivity)
  (define h (rows g))
  (define w (cols g))
  (define visited (make-hash))
  (define deltas
    (if (= connectivity 4)
        '((-1 0) (1 0) (0 -1) (0 1))
        '((-1 0) (1 0) (0 -1) (0 1) (-1 -1) (-1 1) (1 -1) (1 1))))
  (define objects '())

  (for* ([r (in-range h)] [c (in-range w)])
    (when (and (not (= (cell-at g r c) bg))
               (not (hash-has-key? visited (cons r c))))
      (define color (cell-at g r c))
      (define cells '())
      (define queue (list (cons r c)))
      (hash-set! visited (cons r c) #t)
      (let bfs ()
        (unless (empty? queue)
          (define curr (first queue))
          (set! queue (rest queue))
          (set! cells (cons (list (car curr) (cdr curr)) cells))
          (for ([d (in-list deltas)])
            (define nr (+ (car curr) (first d)))
            (define nc (+ (cdr curr) (second d)))
            (when (and (>= nr 0) (< nr h) (>= nc 0) (< nc w)
                       (= (cell-at g nr nc) color)
                       (not (hash-has-key? visited (cons nr nc))))
              (hash-set! visited (cons nr nc) #t)
              (set! queue (append queue (list (cons nr nc))))))
          (bfs)))
      ;; Build object
      (define rs (map first cells))
      (define cs (map second cells))
      (define obj (hasheq 'color color
                          'cells (reverse cells)
                          'bbox (list (apply min rs) (apply min cs)
                                      (apply max rs) (apply max cs))
                          'size (length cells)))
      (set! objects (cons obj objects))))
  (reverse objects))

(define (objects g [bg 0]) (find-objects g bg 4))
(define (objects-8 g [bg 0]) (find-objects g bg 8))

;; Object accessors
(define (obj-color obj) (hash-ref obj 'color))
(define (obj-cells obj) (hash-ref obj 'cells))
(define (obj-bbox obj) (hash-ref obj 'bbox))
(define (obj-size obj) (hash-ref obj 'size))

;; ============================================================
;; Flood fill
;; ============================================================
(define (flood-fill g r c new-color)
  (define h (rows g))
  (define w (cols g))
  (define old-color (cell-at g r c))
  (when (= old-color new-color) (error "flood-fill: old and new colors are the same"))
  (define result (list->vector (map list->vector g)))
  (define queue (list (cons r c)))
  (vector-set! (vector-ref result r) c new-color)
  (let bfs ()
    (unless (empty? queue)
      (define curr (first queue))
      (set! queue (rest queue))
      (for ([d '((-1 . 0) (1 . 0) (0 . -1) (0 . 1))])
        (define nr (+ (car curr) (car d)))
        (define nc (+ (cdr curr) (cdr d)))
        (when (and (>= nr 0) (< nr h) (>= nc 0) (< nc w)
                   (= (vector-ref (vector-ref result nr) nc) old-color))
          (vector-set! (vector-ref result nr) nc new-color)
          (set! queue (append queue (list (cons nr nc))))))
      (bfs)))
  (for/list ([row (in-vector result)])
    (vector->list row)))

;; Fill all enclosed bg regions (not reachable from border)
(define (fill-all-enclosed g color [bg 0])
  (define h (rows g))
  (define w (cols g))
  ;; BFS from all border bg cells
  (define reachable (make-hash))
  (define queue '())
  (for* ([r (in-range h)] [c (in-range w)]
         #:when (and (= (cell-at g r c) bg)
                     (or (= r 0) (= r (sub1 h)) (= c 0) (= c (sub1 w)))))
    (hash-set! reachable (cons r c) #t)
    (set! queue (append queue (list (cons r c)))))
  (let bfs ()
    (unless (empty? queue)
      (define curr (first queue))
      (set! queue (rest queue))
      (for ([d '((-1 . 0) (1 . 0) (0 . -1) (0 . 1))])
        (define nr (+ (car curr) (car d)))
        (define nc (+ (cdr curr) (cdr d)))
        (when (and (>= nr 0) (< nr h) (>= nc 0) (< nc w)
                   (= (cell-at g nr nc) bg)
                   (not (hash-has-key? reachable (cons nr nc))))
          (hash-set! reachable (cons nr nc) #t)
          (set! queue (append queue (list (cons nr nc))))))
      (bfs)))
  ;; Fill non-reachable bg cells
  (grid-from-fn h w (lambda (r c)
    (define v (cell-at g r c))
    (if (and (= v bg) (not (hash-has-key? reachable (cons r c))))
        color v))))

;; ============================================================
;; Gravity
;; ============================================================
(define (gravity g direction [bg 0])
  (define h (rows g))
  (define w (cols g))
  (define (gravity-col col-vals)
    ;; Move non-bg to end (gravity down)
    (define non-bg (filter (lambda (v) (not (= v bg))) col-vals))
    (define pad (- (length col-vals) (length non-bg)))
    (append (make-list pad bg) non-bg))
  (match direction
    ["down"
     (define cols-list (transpose g))
     (transpose (map gravity-col cols-list))]
    ["up"
     (define cols-list (transpose g))
     (transpose (map (lambda (col)
       (define non-bg (filter (lambda (v) (not (= v bg))) col))
       (define pad (- (length col) (length non-bg)))
       (append non-bg (make-list pad bg))) cols-list))]
    ["right"
     (map gravity-col g)]
    ["left"
     (map (lambda (row)
       (define non-bg (filter (lambda (v) (not (= v bg))) row))
       (define pad (- (length row) (length non-bg)))
       (append non-bg (make-list pad bg))) g)]))

;; ============================================================
;; Scaling
;; ============================================================
(define (upscale g factor)
  (for*/list ([r (in-range (rows g))]
              [_ (in-range factor)])
    (for*/list ([c (in-range (cols g))]
                [__ (in-range factor)])
      (cell-at g r c))))

(define (downscale g factor [fn #f])
  (grid-from-fn (quotient (rows g) factor) (quotient (cols g) factor)
    (lambda (r c)
      (if fn
          (fn (subgrid g (* r factor) (* c factor)
                        (sub1 (+ (* r factor) factor))
                        (sub1 (+ (* c factor) factor))))
          (cell-at g (* r factor) (* c factor))))))

;; ============================================================
;; Tiling
;; ============================================================
(define (tile g rows-n cols-n)
  (define h (rows g))
  (define w (cols g))
  (grid-from-fn (* h rows-n) (* w cols-n)
    (lambda (r c) (cell-at g (modulo r h) (modulo c w)))))

;; ============================================================
;; Analysis
;; ============================================================
(define (symmetric? g axis)
  (match axis
    ["lr" (equal? g (flip-lr g))]
    ["ud" (equal? g (flip-ud g))]
    ["180" (equal? g (rotate-180 g))]
    ["diag" (equal? g (transpose g))]))

(define (border-cells g)
  (define h (rows g))
  (define w (cols g))
  (for*/list ([r (in-range h)] [c (in-range w)]
              #:when (or (= r 0) (= r (sub1 h)) (= c 0) (= c (sub1 w))))
    (list r c)))

;; ============================================================
;; Filters and application
;; ============================================================
(define (color-filter color)
  (lambda (r c v) (= v color)))

(define (not-color-filter color)
  (lambda (r c v) (not (= v color))))

(define (const-target color)
  (lambda (r c v) color))

(define (apply-filtered g filter-fn target-fn)
  (map-grid g (lambda (r c v)
    (if (filter-fn r c v) (target-fn r c v) v))))

;; ============================================================
;; Sort helpers
;; ============================================================
(define (sort-by lst key-fn)
  (sort lst < #:key key-fn))

;; ============================================================
;; Additional utilities used by grounded rules
;; ============================================================

;; for/first returns the VALUE (not #t) — but "works correctly" was misleading
;; and taught the wrong rule. The real footgun: for/first stops at the FIRST
;; iteration whose BODY runs, so a body that returns #f for a non-match ends
;; the loop with #f even when a later element would have matched. ~15 rule
;; repairs came from exactly that.
;;   WRONG: (for/first ([v lst]) (if (> v 3) v #f))   ; stops on the first miss
;;   RIGHT: (for/first ([v lst] #:when (> v 3)) v)     ; #:when does the skipping
;;   RIGHT: (find-first (lambda (v) (> v 3)) lst)      ; canonical
;; Never write a bare-body #f; use #:when, or prefer find-first.

;; Print (for debugging)
(define (display-grid g)
  (for ([row (in-list g)])
    (displayln row)))

;; ============================================================
;; 3D Heightmap / Lattice operations
;; ============================================================
(require (file "heightmap.rkt"))
(require (file "layers.rkt"))

;; ============================================================
;; Missing builtins — ported from Python for grounded rule compat
;; ============================================================

;; --- Basics that Racket has but under different names ---
;; Overloaded = that handles non-numbers via equal?
(define (arc= a b)
  (if (and (number? a) (number? b))
      (= a b)
      (equal? a b)))
(define (arc!= a b) (not (arc= a b)))
(define (mod a b) (modulo a b))
;; and/or are syntax in Racket — (and a b), (or a b) work natively

;; Override / to do integer division for ints (like Python //)
(define (arc/ a b)
  (if (and (exact-integer? a) (exact-integer? b))
      (quotient a b)
      (/ a b)))
;; We need to shadow / in the eval namespace
;; This is done by redefining it

;; reduce = foldl with different arg order: (reduce fn init lst)
(define (reduce fn init lst)
  (foldl (lambda (v acc) (fn acc v)) init lst))

;; find = first element where pred is truthy, returns #f if not found
(define (find pred lst)
  (for/first ([v (in-list lst)] #:when (pred v)) v))

;; find-first is the SAFE form and should be preferred over for/first.
;; The old comment here described "(for/first (v lst) body) where body returns
;; #f for skip" as if that pattern worked — it does NOT. A #f body value does
;; not skip; it terminates the loop and becomes the result. Use #:when to skip,
;; or use find-first, which takes the predicate explicitly and cannot be
;; written that way by mistake.

;; grid constructor from list of rows
(define (grid . rows-or-single)
  (if (and (= (length rows-or-single) 1) (list? (first rows-or-single))
           (list? (first (first rows-or-single))))
      (first rows-or-single)
      rows-or-single))

;; --- Grid accessors ---
(define (row-at g r) (list-ref g r))
(define (grid->list g) g)  ;; grids are already lists
(define (grid-cells g)
  (for*/list ([r (in-range (rows g))] [c (in-range (cols g))])
    (list r c (cell-at g r c))))
(define (grid-equal? g1 g2) (equal? g1 g2))
(define (filter-cells g pred)
  (for*/list ([r (in-range (rows g))] [c (in-range (cols g))]
              #:when (pred r c (cell-at g r c)))
    (list r c)))

;; pos constructor
(define (pos r c) (list r c))

;; pairs — list of consecutive pairs
(define (pairs lst)
  (if (< (length lst) 2) '()
      (for/list ([i (in-range (sub1 (length lst)))])
        (list (list-ref lst i) (list-ref lst (add1 i))))))

;; --- Crop / Extract ---
(define (crop g r1 c1 r2 c2) (subgrid g r1 c1 r2 c2))

(define (crop-object g obj)
  (let ([bb (obj-bbox obj)])
    (subgrid g (first bb) (second bb) (third bb) (fourth bb))))

(define (extract-largest g [bg 0])
  (define objs (objects g bg))
  (if (empty? objs) g
      (let ([biggest (argmax obj-size objs)])
        (crop-object g biggest))))

(define (largest-object g [bg 0])
  (define objs (objects g bg))
  (if (empty? objs) #f (argmax obj-size objs)))

;; --- Fill operations ---
(define (fill-color g color)
  (grid-from-fn (rows g) (cols g) (lambda (r c) color)))

(define (fill-enclosed g [color #f] [bg 0])
  ;; Fill bg regions not reachable from border
  (fill-all-enclosed g (or color (mode g bg)) bg))

(define (enclosed? g r c [bg 0])
  ;; Is cell (r,c) enclosed (not border-reachable through bg)?
  (define h (rows g))
  (define w (cols g))
  (define visited (mutable-set))
  (define queue (list (cons r c)))
  (set-add! visited (cons r c))
  (let bfs ()
    (cond
      [(empty? queue) #t]  ;; never reached border → enclosed
      [else
       (define curr (first queue))
       (set! queue (rest queue))
       (define cr (car curr))
       (define cc (cdr curr))
       (if (or (= cr 0) (= cr (sub1 h)) (= cc 0) (= cc (sub1 w)))
           #f  ;; reached border → not enclosed
           (begin
             (for ([d '((-1 . 0) (1 . 0) (0 . -1) (0 . 1))])
               (define nr (+ cr (car d)))
               (define nc (+ cc (cdr d)))
               (when (and (>= nr 0) (< nr h) (>= nc 0) (< nc w)
                          (= (cell-at g nr nc) bg)
                          (not (set-member? visited (cons nr nc))))
                 (set-add! visited (cons nr nc))
                 (set! queue (append queue (list (cons nr nc))))))
             (bfs)))])))

;; --- Row/Column analysis ---
(define (full-rows g)
  (for/list ([r (in-range (rows g))]
             #:when (let ([vals (remove-duplicates (list-ref g r))])
                      (and (= (length vals) 1) (not (= (first vals) 0)))))
    (list r (first (list-ref g r)))))

(define (full-cols g)
  (define h (rows g))
  (define w (cols g))
  (for/list ([c (in-range w)]
             #:when (let ([vals (remove-duplicates
                                 (for/list ([r (in-range h)]) (cell-at g r c)))])
                      (and (= (length vals) 1) (not (= (first vals) 0)))))
    (list c (cell-at g 0 c))))

(define (gap-runs g row [val 0])
  ;; Contiguous runs of val in a row → list of (start length)
  (define w (cols g))
  (define result '())
  (define start #f)
  (for ([c (in-range (add1 w))])
    (define v (if (< c w) (cell-at g row c) -1))
    (cond
      [(= v val) (when (not start) (set! start c))]
      [else
       (when start
         (set! result (append result (list (list start (- c start)))))
         (set! start #f))]))
  result)

;; --- Objects: multicolor ---
(define (objects-multicolor g [bg 0])
  (define h (rows g))
  (define w (cols g))
  (define visited (make-hash))
  (define objects-list '())
  (for* ([r (in-range h)] [c (in-range w)])
    (when (and (not (= (cell-at g r c) bg))
               (not (hash-has-key? visited (cons r c))))
      (define cells '())
      (define queue (list (cons r c)))
      (hash-set! visited (cons r c) #t)
      (let bfs ()
        (unless (empty? queue)
          (define curr (first queue))
          (set! queue (rest queue))
          (set! cells (cons (list (car curr) (cdr curr)) cells))
          (for ([d '((-1 . 0) (1 . 0) (0 . -1) (0 . 1)
                     (-1 . -1) (-1 . 1) (1 . -1) (1 . 1))])
            (define nr (+ (car curr) (car d)))
            (define nc (+ (cdr curr) (cdr d)))
            (when (and (>= nr 0) (< nr h) (>= nc 0) (< nc w)
                       (not (= (cell-at g nr nc) bg))
                       (not (hash-has-key? visited (cons nr nc))))
              (hash-set! visited (cons nr nc) #t)
              (set! queue (append queue (list (cons nr nc))))))
          (bfs)))
      (define rs (map first cells))
      (define cs (map second cells))
      (define colors-seen (remove-duplicates (map (lambda (cell)
        (cell-at g (first cell) (second cell))) cells)))
      (set! objects-list (cons
        (hasheq 'color (first colors-seen)
                'cells (reverse cells)
                'bbox (list (apply min rs) (apply min cs)
                            (apply max rs) (apply max cs))
                'size (length cells))
        objects-list))))
  (reverse objects-list))

;; --- Complex builtins ---

(define (fill-frame-interiors g fill-color [wall-color #f])
  ;; Find rectangular frames and fill their interiors
  ;; Simplified: for each object, check if it's a rectangular frame
  (define h (rows g))
  (define w (cols g))
  (define wc (or wall-color (mode g)))
  (define objs (objects g 0))
  (foldl (lambda (obj acc)
    (define bb (obj-bbox obj))
    (define r1 (first bb)) (define c1 (second bb))
    (define r2 (third bb)) (define c2 (fourth bb))
    (define bh (add1 (- r2 r1))) (define bw (add1 (- c2 c1)))
    (if (and (>= bh 3) (>= bw 3) (= (obj-color obj) wc))
        ;; Check if it's a frame (border cells match, interior is different)
        (let ([is-frame
               (and (andmap (lambda (c) (= (cell-at acc r1 c) wc)) (range c1 (add1 c2)))
                    (andmap (lambda (c) (= (cell-at acc r2 c) wc)) (range c1 (add1 c2)))
                    (andmap (lambda (r) (= (cell-at acc r c1) wc)) (range r1 (add1 r2)))
                    (andmap (lambda (r) (= (cell-at acc r c2) wc)) (range r1 (add1 r2))))])
          (if is-frame
              (grid-from-fn h w (lambda (r c)
                (if (and (> r r1) (< r r2) (> c c1) (< c c2)
                         (= (cell-at acc r c) 0))
                    fill-color
                    (cell-at acc r c))))
              acc))
        acc))
    g objs))

(define (fill-object-bboxes-8 g color [bg 0])
  (define h (rows g))
  (define w (cols g))
  (define objs (objects-8 g bg))
  (foldl (lambda (obj acc)
    (define bb (obj-bbox obj))
    (grid-from-fn h w (lambda (r c)
      (if (and (>= r (first bb)) (<= r (third bb))
               (>= c (second bb)) (<= c (fourth bb))
               (= (cell-at acc r c) bg))
          color
          (cell-at acc r c)))))
    g objs))

(define (make-isolated-filter g connectivity)
  ;; Returns a filter function for cells with no same-color neighbors
  (define h (rows g))
  (define w (cols g))
  (define deltas (if (= connectivity 8)
    '((-1 -1) (-1 0) (-1 1) (0 -1) (0 1) (1 -1) (1 0) (1 1))
    '((-1 0) (1 0) (0 -1) (0 1))))
  (lambda (r c v)
    (and (not (= v 0))
         (not (for/or ([d (in-list deltas)])
           (define nr (+ r (first d)))
           (define nc (+ c (second d)))
           (and (>= nr 0) (< nr h) (>= nc 0) (< nc w)
                (= (cell-at g nr nc) v)))))))

(define (apply-filtered-in-shape g filter-fn target-fn shape)
  ;; Apply target-fn to cells matching filter-fn within shape mask
  (grid-from-fn (rows g) (cols g) (lambda (r c)
    (define v (cell-at g r c))
    (if (and (< r (rows shape)) (< c (cols shape))
             (not (= (cell-at shape r c) 0))
             (filter-fn r c v))
        (target-fn r c v)
        v))))

(define (rect-mask h w r1 c1 r2 c2)
  (grid-from-fn h w (lambda (r c)
    (if (and (>= r r1) (<= r r2) (>= c c1) (<= c c2)) 1 0))))

;; --- Shift ---
(define (shift g dr dc [bg 0])
  (grid-from-fn (rows g) (cols g) (lambda (r c)
    (define sr (- r dr))
    (define sc (- c dc))
    (if (and (>= sr 0) (< sr (rows g)) (>= sc 0) (< sc (cols g)))
        (cell-at g sr sc)
        bg))))

;; --- Sizing ---
(define (self-tile g [pred #f])
  (define h (rows g))
  (define w (cols g))
  (define check (or pred (lambda (v) (not (= v 0)))))
  (grid-from-fn (* h h) (* w w) (lambda (r c)
    (define br (quotient r h))
    (define bc (quotient c w))
    (define lr (modulo r h))
    (define lc (modulo c w))
    (if (check (cell-at g br bc))
        (cell-at g lr lc)
        0))))

(define (stamp-grid pattern stamp [bg 0] [pred #f])
  (define ph (rows pattern))
  (define pw (cols pattern))
  (define sh (rows stamp))
  (define sw (cols stamp))
  (define check (or pred (lambda (v) (not (= v bg)))))
  (grid-from-fn (* ph sh) (* pw sw) (lambda (r c)
    (define br (quotient r sh))
    (define bc (quotient c sw))
    (define lr (modulo r sh))
    (define lc (modulo c sw))
    (if (check (cell-at pattern br bc))
        (cell-at stamp lr lc)
        bg))))

(define (kaleidoscope g)
  (define h (rows g))
  (define w (cols g))
  (grid-from-fn (* 2 h) (* 2 w) (lambda (r c)
    (define lr (if (< r h) r (- (* 2 h) 1 r)))
    (define lc (if (< c w) c (- (* 2 w) 1 c)))
    (cell-at g lr lc))))

(define (scale-map g row-scales col-scales)
  (define row-offsets
    (let loop ([scales row-scales] [offset 0] [result '()])
      (if (empty? scales) (reverse result)
          (loop (rest scales) (+ offset (first scales))
                (cons offset result)))))
  (define col-offsets
    (let loop ([scales col-scales] [offset 0] [result '()])
      (if (empty? scales) (reverse result)
          (loop (rest scales) (+ offset (first scales))
                (cons offset result)))))
  (define new-h (apply + row-scales))
  (define new-w (apply + col-scales))
  (grid-from-fn new-h new-w (lambda (r c)
    ;; Find which source row/col this maps to
    (define src-r
      (for/last ([i (in-range (length row-offsets))]
                 #:when (<= (list-ref row-offsets i) r))
        i))
    (define src-c
      (for/last ([i (in-range (length col-offsets))]
                 #:when (<= (list-ref col-offsets i) c))
        i))
    (cell-at g src-r src-c))))

(define (count-blocks g color size)
  (define h (rows g))
  (define w (cols g))
  (for/sum ([r (in-range (add1 (- h size)))]
            [c (in-range (add1 (- w size)))])
    (if (for*/and ([dr (in-range size)] [dc (in-range size)])
          (= (cell-at g (+ r dr) (+ c dc)) color))
        1 0)))

(define (encode-bar count max-len on-color [bg 0])
  (list (for/list ([i (in-range max-len)])
    (if (< i count) on-color bg))))

(define (count-color g color)
  (for*/sum ([r (in-range (rows g))] [c (in-range (cols g))])
    (if (= (cell-at g r c) color) 1 0)))

;; --- Split at separator ---
(define (split-at-separator g [bg 0])
  ;; Split grid by full-span separator rows/columns of bg
  (define h (rows g))
  (define w (cols g))
  ;; Find separator rows (all bg)
  (define sep-rows
    (for/list ([r (in-range h)]
               #:when (andmap (lambda (v) (= v bg)) (list-ref g r)))
      r))
  (if (not (empty? sep-rows))
      ;; Split by rows
      (let loop ([remaining (range 0 h)] [seps sep-rows] [result '()] [current '()])
        (cond
          [(empty? remaining)
           (reverse (if (empty? current) result (cons (reverse current) result)))]
          [(and (not (empty? seps)) (= (first remaining) (first seps)))
           (loop (rest remaining) (rest seps)
                 (if (empty? current) result (cons (reverse current) result))
                 '())]
          [else
           (loop (rest remaining) seps result
                 (cons (list-ref g (first remaining)) current))]))
      ;; Try columns
      (let ()
        (define sep-cols
          (for/list ([c (in-range w)]
                     #:when (for/and ([r (in-range h)]) (= (cell-at g r c) bg)))
            c))
        (if (empty? sep-cols) (list g)
            ;; Split by cols (transpose, split by rows, transpose back)
            (map transpose (split-at-separator (transpose g) bg))))))

;; --- Zip halves ---
(define (zip-halves g fn [sep-color #f])
  (define parts (split-at-separator g (or sep-color 0)))
  (if (< (length parts) 2) g
      (let ([a (first parts)] [b (second parts)])
        (grid-from-fn (rows a) (cols a) (lambda (r c)
          (fn (cell-at a r c) (cell-at b r c)))))))

;; --- Recolor operations ---
(define (recolor-map* g mapping)
  ;; mapping is a hash table
  (map-grid g (lambda (r c v) (hash-ref mapping v v))))

(define (recolor-by-rank g [bg 0])
  ;; Recolor objects by size rank: largest=1, 2nd=2, etc.
  (define objs (sort (objects g bg) > #:key obj-size))
  (define h (rows g))
  (define w (cols g))
  (define cell-map (make-hash))
  (for ([obj (in-list objs)] [rank (in-naturals 1)])
    (for ([cell (in-list (obj-cells obj))])
      (hash-set! cell-map (cons (first cell) (second cell)) rank)))
  (grid-from-fn h w (lambda (r c)
    (hash-ref cell-map (cons r c) (cell-at g r c)))))

(define (recolor-enclosing-objects g color [bg 0])
  ;; Recolor objects whose bbox interior has bg cells (frame-like objects)
  (define h (rows g))
  (define w (cols g))
  (define objs (objects g bg))
  (define holey
    (filter (lambda (obj)
      (define bb (obj-bbox obj))
      (define r1 (first bb)) (define c1 (second bb))
      (define r2 (third bb)) (define c2 (fourth bb))
      (and (> (- r2 r1) 1) (> (- c2 c1) 1)
           (for*/or ([r (in-range (add1 r1) r2)]
                     [c (in-range (add1 c1) c2)])
             (= (cell-at g r c) bg))))
      objs))
  (foldl (lambda (obj acc)
    (define cell-set (list->set (map (lambda (cell) (cons (first cell) (second cell)))
                                     (obj-cells obj))))
    (grid-from-fn h w (lambda (r c)
      (if (set-member? cell-set (cons r c)) color (cell-at acc r c)))))
    g holey))

(define (recolor-by-nearest-marker g markers target-color [bg 0])
  ;; For each cell of target-color, recolor to nearest marker's color
  (define h (rows g))
  (define w (cols g))
  (grid-from-fn h w (lambda (r c)
    (define v (cell-at g r c))
    (if (= v target-color)
        (let ([nearest (argmin (lambda (m)
                (+ (abs (- r (first m))) (abs (- c (second m)))))
              markers)])
          (cell-at g (first nearest) (second nearest)))
        v))))

;; --- Holey / hollow objects ---
(define (holey-object-cells g [bg 0])
  (define objs (objects g bg))
  (apply append
    (map obj-cells
      (filter (lambda (obj)
        (define bb (obj-bbox obj))
        (for*/or ([r (in-range (add1 (first bb)) (third bb))]
                  [c (in-range (add1 (second bb)) (fourth bb))])
          (= (cell-at g r c) bg)))
        objs))))

(define (hollow-objects g [bg 0])
  (filter (lambda (obj)
    (define bb (obj-bbox obj))
    (for*/or ([r (in-range (add1 (first bb)) (third bb))]
              [c (in-range (add1 (second bb)) (fourth bb))])
      (= (cell-at g r c) bg)))
    (objects g bg)))

;; --- Find 0-regions ---
(define (find-0-regions g [bg 0])
  ;; Find connected components of bg
  (define h (rows g))
  (define w (cols g))
  (define visited (make-hash))
  (define regions '())
  (for* ([r (in-range h)] [c (in-range w)])
    (when (and (= (cell-at g r c) bg) (not (hash-has-key? visited (cons r c))))
      (define cells '())
      (define queue (list (cons r c)))
      (hash-set! visited (cons r c) #t)
      (let bfs ()
        (unless (empty? queue)
          (define curr (first queue))
          (set! queue (rest queue))
          (set! cells (cons (list (car curr) (cdr curr)) cells))
          (for ([d '((-1 . 0) (1 . 0) (0 . -1) (0 . 1))])
            (define nr (+ (car curr) (car d)))
            (define nc (+ (cdr curr) (cdr d)))
            (when (and (>= nr 0) (< nr h) (>= nc 0) (< nc w)
                       (= (cell-at g nr nc) bg)
                       (not (hash-has-key? visited (cons nr nc))))
              (hash-set! visited (cons nr nc) #t)
              (set! queue (append queue (list (cons nr nc))))))
          (bfs)))
      (set! regions (cons (reverse cells) regions))))
  (reverse regions))

;; --- Shortest path fill ---
(define (shortest-path-fill g r1 c1 r2 c2 color [walkable 0])
  (define h (rows g))
  (define w (cols g))
  ;; BFS from (r1,c1) to (r2,c2) through walkable cells
  (define parent (make-hash))
  (define visited (mutable-set))
  (set-add! visited (cons r1 c1))
  (define queue (list (cons r1 c1)))
  (define found #f)
  (let bfs ()
    (unless (or found (empty? queue))
      (define curr (first queue))
      (set! queue (rest queue))
      (when (and (= (car curr) r2) (= (cdr curr) c2))
        (set! found #t))
      (unless found
        (for ([d '((-1 . 0) (1 . 0) (0 . -1) (0 . 1))])
          (define nr (+ (car curr) (car d)))
          (define nc (+ (cdr curr) (cdr d)))
          (when (and (>= nr 0) (< nr h) (>= nc 0) (< nc w)
                     (not (set-member? visited (cons nr nc)))
                     (or (= (cell-at g nr nc) walkable)
                         (and (= nr r2) (= nc c2))))
            (set-add! visited (cons nr nc))
            (hash-set! parent (cons nr nc) curr)
            (set! queue (append queue (list (cons nr nc))))))
        (bfs))))
  ;; Trace path back
  (if (not found) g
      (let loop ([curr (cons r2 c2)] [acc g])
        (define next-acc (set-cell acc (car curr) (cdr curr) color))
        (if (and (= (car curr) r1) (= (cdr curr) c1))
            next-acc
            (loop (hash-ref parent curr) next-acc)))))

;; --- Stack objects ---
(define (stack-objects-right g [bg 0])
  (define objs (sort (objects g bg) < #:key (lambda (o) (second (obj-bbox o)))))
  (define h (rows g))
  (define w (cols g))
  (define result (empty-grid h w bg))
  ;; Thread the write cursor through the fold. It used to be a fixed
  ;; `(define cur-c 0)` that was never advanced, so EVERY object pasted at
  ;; column 0 and stacked on top of itself (`ow` was computed and discarded).
  ;; 0 corpus uses, so this repair cannot regress a gold rule.
  ;;
  ;; VOCAB-NEUTRAL ON PURPOSE: scripts/dsl_v2.prelude_callables() harvests
  ;; definition names by regex WITHOUT tracking nesting (or comments), so a
  ;; new inner binding name would enter the model's CLOSED VOCABULARY and
  ;; resize the embedding table — a first cut of this fix moved it
  ;; 4696 -> 4697, which sends the live 0.5B checkpoint down merge_vocab's
  ;; len-mismatch path. The accumulator is therefore destructured with `let`,
  ;; and the set of names bound here — bb, oh, ow, sub — is unchanged.
  (car (foldl (lambda (obj acc)
    (define bb (obj-bbox obj))
    (define oh (add1 (- (third bb) (first bb))))
    (define ow (add1 (- (fourth bb) (second bb))))
    (define sub (subgrid g (first bb) (second bb) (third bb) (fourth bb)))
    (let ([canvas (car acc)] [col (cdr acc)])
      (cons (paste canvas sub (first bb) col) (+ col ow))))
    (cons result 0) objs)))

;; --- Assemble at anchors ---
(define (assemble-at g anchor-color size)
  (define anchors (find-color g anchor-color))
  (define h (rows g))
  (define w (cols g))
  (define out-h size)
  (define out-w size)
  (define result (empty-grid out-h out-w 0))
  (foldl (lambda (anchor acc)
    (define ar (first anchor))
    (define ac (second anchor))
    ;; Gather cells around anchor within size radius
    (define half (quotient size 2))
    (grid-from-fn out-h out-w (lambda (r c)
      (define gr (+ ar (- r half)))
      (define gc (+ ac (- c half)))
      (define v (if (and (>= gr 0) (< gr h) (>= gc 0) (< gc w))
                    (cell-at g gr gc) 0))
      (define cur (cell-at acc r c))
      (if (and (not (= v 0)) (not (= v anchor-color))) v cur))))
    result anchors))

;; --- Denoise ---
(define (denoise-grid g [bg 0])
  ;; Remove isolated pixels (no same-color 4-connected neighbors)
  (map-grid g (lambda (r c v)
    (if (= v bg) bg
        (let ([has-neighbor
               (for/or ([d '((-1 0) (1 0) (0 -1) (0 1))])
                 (define nr (+ r (first d)))
                 (define nc (+ c (second d)))
                 (and (>= nr 0) (< nr (rows g)) (>= nc 0) (< nc (cols g))
                      (= (cell-at g nr nc) v)))])
          (if has-neighbor v bg))))))

;; --- Complex analysis builtins ---

(define (find-largest-frame g)
  ;; Find largest rectangular frame border in grid
  ;; Returns (list r1 c1 r2 c2 ih iw color) or #f
  (define h (rows g))
  (define w (cols g))
  (define best #f)
  (define best-area 0)
  (for ([color (in-range 1 10)])
    ;; Find horizontal runs of this color >= 4
    (define runs '())
    (for ([r (in-range h)])
      (define start #f)
      (for ([c (in-range (add1 w))])
        (define v (if (< c w) (cell-at g r c) -1))
        (cond
          [(= v color) (when (not start) (set! start c))]
          [else
           (when (and start (>= (- c start) 4))
             (set! runs (cons (list r start (sub1 c)) runs)))
           (set! start #f)])))
    ;; Match pairs
    (for* ([i (in-list runs)] [j (in-list runs)])
      (define r1 (first i)) (define c1 (second i)) (define c2 (third i))
      (define r2 (first j))
      (when (and (> r2 r1) (>= (- r2 r1) 3)
                 (= (second j) c1) (= (third j) c2))
        (when (and (andmap (lambda (r) (= (cell-at g r c1) color)) (range r1 (add1 r2)))
                   (andmap (lambda (r) (= (cell-at g r c2) color)) (range r1 (add1 r2))))
          (define area (* (sub1 (- r2 r1)) (sub1 (- c2 c1))))
          (when (> area best-area)
            (set! best (list r1 c1 r2 c2 (sub1 (- r2 r1)) (sub1 (- c2 c1)) color))
            (set! best-area area))))))
  best)

(define (line-z-order g [bg 7])
  ;; Overlapping lines: return colors sorted by z-order (bottom to top)
  ;; Sort by (obscured DESC, color DESC)
  (define h (rows g))
  (define w (cols g))
  (define color-info (make-hash))
  (for ([color (in-range 10)])
    (when (not (= color bg))
      (define positions
        (for*/list ([r (in-range h)] [c (in-range w)]
                    #:when (= (cell-at g r c) color))
          (cons r c)))
      (when (not (empty? positions))
        (define shown (length positions))
        ;; Count by row, col, diag, anti-diag
        (define row-c (make-hash))
        (define col-c (make-hash))
        (define diag-c (make-hash))
        (define adiag-c (make-hash))
        (for ([p (in-list positions)])
          (hash-update! row-c (car p) add1 0)
          (hash-update! col-c (cdr p) add1 0)
          (hash-update! diag-c (- (car p) (cdr p)) add1 0)
          (hash-update! adiag-c (+ (car p) (cdr p)) add1 0))
        (define max-r (apply max (hash-values row-c)))
        (define max-c (apply max (hash-values col-c)))
        (define max-d (apply max (hash-values diag-c)))
        (define max-a (apply max (hash-values adiag-c)))
        (define m (max max-r max-c max-d max-a))
        (define expected
          (cond
            [(= m max-r) w]
            [(= m max-c) h]
            [(= m max-d)
             (define best-d (argmax (lambda (k) (hash-ref diag-c k)) (hash-keys diag-c)))
             (max 0 (add1 (- (min (sub1 h) (+ (sub1 w) best-d))
                             (max 0 best-d))))]
            [else
             (define best-a (argmax (lambda (k) (hash-ref adiag-c k)) (hash-keys adiag-c)))
             (max 0 (add1 (- (min (sub1 h) best-a)
                             (max 0 (- best-a (sub1 w))))))]))
        (hash-set! color-info color (- expected shown)))))
  (sort (hash-keys color-info) >
    #:key (lambda (c) (+ (* 100 (hash-ref color-info c)) c))))

(define (tallest-rect g color [min-h 2])
  ;; Find largest rectangle of color with height >= min-h
  (define h (rows g))
  (define w (cols g))
  (define best #f)
  (define best-area 0)
  (for ([r1 (in-range h)])
    (define valid (make-vector w #t))
    (for ([r2 (in-range r1 h)])
      (for ([c (in-range w)])
        (when (not (= (cell-at g r2 c) color))
          (vector-set! valid c #f)))
      (define height (add1 (- r2 r1)))
      (when (>= height min-h)
        (define run-start #f)
        (for ([c (in-range (add1 w))])
          (cond
            [(and (< c w) (vector-ref valid c))
             (when (not run-start) (set! run-start c))]
            [else
             (when run-start
               (define run-len (- c run-start))
               (define area (* height run-len))
               (when (> area best-area)
                 (set! best (list r1 run-start r2 (sub1 c) area))
                 (set! best-area area)))
             (set! run-start #f)])))))
  best)

;; ============================================================
;; SYMMETRY DETECTION (BARC-inspired)
;; ============================================================
;; Returns the AXIS of symmetry, not just yes/no. Useful for
;; "complete the symmetric pattern" tasks where you need to know
;; HOW the grid is symmetric in order to fill the missing part.

(define (detect-mirror-symmetry g [ignore-colors '()])
  ;; Returns list of symmetry axes the grid has:
  ;;   'lr   — left-right (vertical axis)
  ;;   'ud   — up-down (horizontal axis)
  ;;   'diag — main diagonal (only if square)
  ;;   'anti — anti-diagonal (only if square)
  ;; Cells with colors in ignore-colors are treated as wildcards.
  ;; Empty list = no symmetry.
  (define h (length g))
  (define w (length (first g)))
  (define (cell-at-rc r c) (list-ref (list-ref g r) c))
  (define (matches? v1 v2)
    (or (= v1 v2)
        (and (not (null? ignore-colors))
             (or (member v1 ignore-colors) (member v2 ignore-colors)))))
  (define lr-sym
    (andmap (lambda (r)
      (andmap (lambda (c) (matches? (cell-at-rc r c) (cell-at-rc r (- w 1 c))))
              (range 0 w)))
      (range 0 h)))
  (define ud-sym
    (andmap (lambda (r)
      (andmap (lambda (c) (matches? (cell-at-rc r c) (cell-at-rc (- h 1 r) c)))
              (range 0 w)))
      (range 0 h)))
  (define diag-sym
    (and (= h w)
         (andmap (lambda (r)
           (andmap (lambda (c) (matches? (cell-at-rc r c) (cell-at-rc c r)))
                   (range 0 w)))
           (range 0 h))))
  (define anti-sym
    (and (= h w)
         (andmap (lambda (r)
           (andmap (lambda (c) (matches? (cell-at-rc r c) (cell-at-rc (- w 1 c) (- h 1 r))))
                   (range 0 w)))
           (range 0 h))))
  (filter (lambda (x) x)
          (list (and lr-sym 'lr) (and ud-sym 'ud)
                (and diag-sym 'diag) (and anti-sym 'anti))))

(define (detect-rotational-symmetry g [ignore-colors '()])
  ;; Returns 4 if 90° rotation symmetric, 2 if 180°, 1 if no rotational symmetry.
  ;; Only meaningful for square grids.
  (define h (length g))
  (define w (length (first g)))
  (cond
    [(not (= h w)) 1]
    [else
     (define (cell-at-rc r c) (list-ref (list-ref g r) c))
     (define (matches? v1 v2)
       (or (= v1 v2)
           (and (not (null? ignore-colors))
                (or (member v1 ignore-colors) (member v2 ignore-colors)))))
     (define rot90-ok
       (andmap (lambda (r)
         (andmap (lambda (c)
           (matches? (cell-at-rc r c) (cell-at-rc c (- w 1 r))))
           (range 0 w)))
         (range 0 h)))
     (define rot180-ok
       (andmap (lambda (r)
         (andmap (lambda (c)
           (matches? (cell-at-rc r c) (cell-at-rc (- h 1 r) (- w 1 c))))
           (range 0 w)))
         (range 0 h)))
     (cond [rot90-ok 4]
           [rot180-ok 2]
           [else 1])]))

;; ============================================================
;; TRANSLATIONAL PERIOD DETECTION
;; ============================================================
;; "Find the smallest (dr, dc) such that grid[r][c] == grid[r+dr][c+dc]
;;  whenever both are in bounds, treating ignore-colors as wildcards."
;; Useful for periodic-tile / occlusion tasks.

(define (detect-translational-period g [ignore-colors '()])
  ;; Returns (list dr dc) — smallest non-zero period — or #f if none.
  (define h (length g))
  (define w (length (first g)))
  (define (cell-at-rc r c) (list-ref (list-ref g r) c))
  (define (matches? v1 v2)
    (or (= v1 v2)
        (and (not (null? ignore-colors))
             (or (member v1 ignore-colors) (member v2 ignore-colors)))))
  (define (period-ok? dr dc)
    (andmap (lambda (r)
      (andmap (lambda (c)
        (or (>= (+ r dr) h)
            (>= (+ c dc) w)
            (matches? (cell-at-rc r c) (cell-at-rc (+ r dr) (+ c dc)))))
        (range 0 w)))
      (range 0 h)))
  ;; Try candidates in order of |dr|+|dc|, smallest first
  (define candidates
    (sort
      (for*/list ([dr (in-range 0 (+ 1 (quotient h 2)))]
                  [dc (in-range 0 (+ 1 (quotient w 2)))]
                  #:when (or (> dr 0) (> dc 0)))
        (list (+ dr dc) dr dc))
      (lambda (a b) (< (first a) (first b)))))
  (let loop ([cs candidates])
    (cond [(null? cs) #f]
          [(period-ok? (second (first cs)) (third (first cs)))
           (list (second (first cs)) (third (first cs)))]
          [else (loop (cdr cs))])))

;; ============================================================
;; OBJECT CONTACT / TOUCHING (BARC contact())
;; ============================================================

(define (obj-contact obj1 obj2)
  ;; Returns 'top, 'bottom, 'left, 'right indicating which side of obj1
  ;; is touching obj2 (4-connectivity). Returns #f if not touching.
  ;; If multiple sides touch, returns the first one found in (top bottom left right) order.
  (define cells1 (obj-cells obj1))
  (define cells2 (obj-cells obj2))
  (define cell-set2
    (for/set ([c (in-list cells2)]) (cons (first c) (second c))))
  (define (touches-side dir)
    (define delta (match dir
                    ['top (cons -1 0)]
                    ['bottom (cons 1 0)]
                    ['left (cons 0 -1)]
                    ['right (cons 0 1)]))
    (ormap (lambda (c)
      (set-member? cell-set2 (cons (+ (first c) (car delta))
                                   (+ (second c) (cdr delta)))))
      cells1))
  (cond
    [(touches-side 'top) 'top]
    [(touches-side 'bottom) 'bottom]
    [(touches-side 'left) 'left]
    [(touches-side 'right) 'right]
    [else #f]))

(define (objects-touching? obj1 obj2)
  ;; Boolean: do these two objects touch (4-connected)?
  (and (obj-contact obj1 obj2) #t))

;; ============================================================
;; SLIDE UNTIL CONTACT
;; ============================================================
;; Slide an object in a direction until it touches another object,
;; or hits a wall. More general than gravity (which slides ALL cells).

(define (slide-until-contact g moving-cells target-cells direction [bg 0])
  ;; moving-cells, target-cells: lists of (r c) lists
  ;; direction: 'up 'down 'left 'right
  ;; Returns new grid with moving object shifted to its contact position.
  (define h (length g))
  (define w (length (first g)))
  (define dlt (match direction
                ['up (cons -1 0)]
                ['down (cons 1 0)]
                ['left (cons 0 -1)]
                ['right (cons 0 1)]))
  (define dr (car dlt))
  (define dc (cdr dlt))
  (define target-set
    (for/set ([c (in-list target-cells)]) (cons (first c) (second c))))
  (define moving-set
    (for/set ([c (in-list moving-cells)]) (cons (first c) (second c))))
  ;; The color to draw with — take from the first moving cell
  (define color
    (let ([fc (first moving-cells)])
      (list-ref (list-ref g (first fc)) (second fc))))
  ;; Find max steps k such that shifting by k is still legal
  ;; (no cell goes out of bounds AND no cell would land on a target)
  (define (legal-at? k)
    (andmap (lambda (c)
      (define nr (+ (first c) (* k dr)))
      (define nc (+ (second c) (* k dc)))
      (and (>= nr 0) (< nr h) (>= nc 0) (< nc w)
           (not (set-member? target-set (cons nr nc)))))
      moving-cells))
  (define max-k
    (let loop ([k 0])
      (if (legal-at? (+ k 1)) (loop (+ k 1)) k)))
  ;; Clear original position, draw at new position
  (define cleared
    (for/list ([r (in-range h)])
      (for/list ([c (in-range w)])
        (if (set-member? moving-set (cons r c))
            bg
            (list-ref (list-ref g r) c)))))
  (for/fold ([acc cleared]) ([cell (in-list moving-cells)])
    (define nr (+ (first cell) (* max-k dr)))
    (define nc (+ (second cell) (* max-k dc)))
    (set-cell acc nr nc color)))

;; ============================================================
;; CUP / U-SHAPE OPENING DETECTION
;; ============================================================
;; A cup is an object whose bounding box border is mostly filled
;; except on one side where the "opening" is. Useful for tasks
;; involving C/U/horseshoe shapes.

(define (cup-opening obj)
  ;; Returns 'up 'down 'left 'right indicating the opening direction,
  ;; or #f if not cup-shaped (no clear opening or multiple openings).
  (define cells (obj-cells obj))
  (define bb (obj-bbox obj))
  (define r1 (first bb)) (define c1 (second bb))
  (define r2 (third bb)) (define c2 (fourth bb))
  (define cell-set
    (for/set ([cell (in-list cells)]) (cons (first cell) (second cell))))
  (define (border-side-cells dir)
    (match dir
      ['up    (for/list ([c (in-range c1 (+ 1 c2))]) (cons r1 c))]
      ['down  (for/list ([c (in-range c1 (+ 1 c2))]) (cons r2 c))]
      ['left  (for/list ([r (in-range r1 (+ 1 r2))]) (cons r c1))]
      ['right (for/list ([r (in-range r1 (+ 1 r2))]) (cons r c2))]))
  (define (missing-on dir)
    (count (lambda (c) (not (set-member? cell-set c))) (border-side-cells dir)))
  (define dirs '(up down left right))
  (define missings (map missing-on dirs))
  (define max-miss (apply max missings))
  ;; A cup has exactly ONE side with missing cells (the opening) and others mostly intact
  (define openings
    (filter values
      (map (lambda (d m) (if (= m max-miss) d #f)) dirs missings)))
  (cond
    [(= max-miss 0) #f]                ;; no opening — solid rectangle frame
    [(> (length openings) 1) #f]       ;; ambiguous (e.g. plus sign)
    [else (first openings)]))

;; ============================================================
;; OBJECT INTERIOR / BOUNDARY CELLS
;; ============================================================
;; The "interior" of an object = cells fully surrounded by other object cells.
;; The "boundary" = cells that have at least one non-object neighbor.

(define (obj-boundary-cells obj [connectivity 4])
  ;; Returns the cells of obj that touch a non-obj cell (i.e., the perimeter).
  (define cells (obj-cells obj))
  (define cell-set
    (for/set ([c (in-list cells)]) (cons (first c) (second c))))
  (define neighbors-of
    (if (= connectivity 8)
        '((-1 . -1) (-1 . 0) (-1 . 1) (0 . -1) (0 . 1) (1 . -1) (1 . 0) (1 . 1))
        '((-1 . 0) (1 . 0) (0 . -1) (0 . 1))))
  (filter (lambda (c)
    (define r (first c)) (define cc (second c))
    (ormap (lambda (d) (not (set-member? cell-set (cons (+ r (car d)) (+ cc (cdr d))))))
           neighbors-of))
    cells))

(define (obj-interior-cells obj [connectivity 4])
  ;; Returns cells fully surrounded by other obj cells (no neighbor outside).
  (define boundary (obj-boundary-cells obj connectivity))
  (define b-set
    (for/set ([c (in-list boundary)]) (cons (first c) (second c))))
  (filter (lambda (c) (not (set-member? b-set (cons (first c) (second c)))))
          (obj-cells obj)))

(define (obj-neighbor-cells obj [connectivity 4])
  ;; Returns cells immediately OUTSIDE the object (one step away from any obj cell).
  ;; These are the cells that would be filled if you "grew" the object by 1 step.
  (define cells (obj-cells obj))
  (define cell-set
    (for/set ([c (in-list cells)]) (cons (first c) (second c))))
  (define neighbors-of
    (if (= connectivity 8)
        '((-1 . -1) (-1 . 0) (-1 . 1) (0 . -1) (0 . 1) (1 . -1) (1 . 0) (1 . 1))
        '((-1 . 0) (1 . 0) (0 . -1) (0 . 1))))
  (define neighbor-set
    (for*/set ([c (in-list cells)]
               [d (in-list neighbors-of)])
      (cons (+ (first c) (car d)) (+ (second c) (cdr d)))))
  (for/list ([n (in-set neighbor-set)]
             #:unless (set-member? cell-set n))
    (list (car n) (cdr n))))

;; ============================================================
;; RE-ARC inspired primitives
;; ============================================================

(define (occurrences grid sub [ignore-colors '()])
  ;; Find all positions (r c) where `sub` matches in `grid`.
  ;; Returns list of (r c) — top-left corner of each match.
  ;; ignore-colors are wildcards in either grid or sub.
  (define gh (length grid))
  (define gw (length (first grid)))
  (define sh (length sub))
  (define sw (length (first sub)))
  (define (matches? a b)
    (or (= a b)
        (and (not (null? ignore-colors))
             (or (member a ignore-colors) (member b ignore-colors)))))
  (define (match-at? r c)
    (andmap (lambda (sr)
      (andmap (lambda (sc)
        (matches? (list-ref (list-ref grid (+ r sr)) (+ c sc))
                  (list-ref (list-ref sub sr) sc)))
        (range 0 sw)))
      (range 0 sh)))
  (filter values
    (for*/list ([r (in-range 0 (+ 1 (- gh sh)))]
                [c (in-range 0 (+ 1 (- gw sw)))])
      (if (match-at? r c) (list r c) #f))))

(define (center-of-mass obj)
  ;; Returns the (r c) center of an object as a list of two floats
  ;; (well — exact rationals, since we use racket's `/`).
  (define cells (obj-cells obj))
  (define n (length cells))
  (define sum-r (apply + (map first cells)))
  (define sum-c (apply + (map second cells)))
  (list (arc/ (+ 0.0 sum-r) n)
        (arc/ (+ 0.0 sum-c) n)))

(define (gravitate from-obj to-obj)
  ;; Returns 'up | 'down | 'left | 'right — the cardinal direction
  ;; from-obj would move to get closer to to-obj. Picks the dominant axis.
  (define c1 (center-of-mass from-obj))
  (define c2 (center-of-mass to-obj))
  (define dr (- (first c2) (first c1)))
  (define dc (- (second c2) (second c1)))
  (cond
    [(>= (abs dr) (abs dc))
     (if (> dr 0) 'down 'up)]
    [else
     (if (> dc 0) 'right 'left)]))

(define (obj-delta obj)
  ;; Returns the cells that are inside obj's bbox but NOT in the object.
  ;; The "negative space" / "holes" of the object's bbox.
  (define bb (obj-bbox obj))
  (define r1 (first bb)) (define c1 (second bb))
  (define r2 (third bb)) (define c2 (fourth bb))
  (define cell-set
    (for/set ([cell (in-list (obj-cells obj))]) (cons (first cell) (second cell))))
  (for*/list ([r (in-range r1 (+ 1 r2))]
              [c (in-range c1 (+ 1 c2))]
              #:unless (set-member? cell-set (cons r c)))
    (list r c)))

(define (frontiers grid [ignore-colors '()])
  ;; Find horizontal/vertical frontier lines: rows or columns whose entire
  ;; length is the same single (non-ignored) color.
  ;; Returns a list of tagged frontiers: (list 'row r color) or (list 'col c color)
  (define h (length grid))
  (define w (length (first grid)))
  (define (cell r c) (list-ref (list-ref grid r) c))
  (define (uniform? vals)
    (and (not (empty? vals))
         (let ([v (first vals)])
           (and (not (member v ignore-colors))
                (andmap (lambda (x) (= x v)) (rest vals))))))
  (define row-frontiers
    (filter values
      (for/list ([r (in-range h)])
        (define vals (for/list ([c (in-range w)]) (cell r c)))
        (if (uniform? vals) (list 'row r (first vals)) #f))))
  (define col-frontiers
    (filter values
      (for/list ([c (in-range w)])
        (define vals (for/list ([r (in-range h)]) (cell r c)))
        (if (uniform? vals) (list 'col c (first vals)) #f))))
  (append row-frontiers col-frontiers))

(define (compress-grid grid)
  ;; Drop consecutive duplicate rows AND consecutive duplicate columns.
  ;; Useful for normalizing periodic / striped grids to their unit cell.
  (define (dedup-consecutive lst)
    (cond [(empty? lst) '()]
          [(empty? (rest lst)) lst]
          [(equal? (first lst) (second lst))
           (dedup-consecutive (rest lst))]
          [else (cons (first lst) (dedup-consecutive (rest lst)))]))
  (define rows-dedup (dedup-consecutive grid))
  ;; Now dedup columns: transpose, dedup, transpose back
  (define transposed
    (apply map list rows-dedup))
  (define cols-dedup (dedup-consecutive transposed))
  (apply map list cols-dedup))

;; --- shape predicates ---
(define (square? obj)
  ;; Is this object a solid square (cells form a full N×N region)?
  (define bb (obj-bbox obj))
  (define h (+ 1 (- (third bb) (first bb))))
  (define w (+ 1 (- (fourth bb) (second bb))))
  (and (= h w) (= (obj-size obj) (* h w))))

(define (vline? obj)
  ;; 1-column-wide object?
  (define bb (obj-bbox obj))
  (= (second bb) (fourth bb)))

(define (hline? obj)
  ;; 1-row-tall object?
  (define bb (obj-bbox obj))
  (= (first bb) (third bb)))

(define (bordering? obj grid)
  ;; Does obj touch the grid's outer border?
  (define h (length grid))
  (define w (length (first grid)))
  (define bb (obj-bbox obj))
  (or (= (first bb) 0)
      (= (third bb) (- h 1))
      (= (second bb) 0)
      (= (fourth bb) (- w 1))))

(define (hmatching? o1 o2)
  ;; Do o1 and o2 share any row?
  (define b1 (obj-bbox o1))
  (define b2 (obj-bbox o2))
  (and (<= (first b1) (third b2))
       (<= (first b2) (third b1))))

(define (vmatching? o1 o2)
  ;; Do o1 and o2 share any column?
  (define b1 (obj-bbox o1))
  (define b2 (obj-bbox o2))
  (and (<= (second b1) (fourth b2))
       (<= (second b2) (fourth b1))))

;; ============================================================
;; More inspired primitives (icecuber + ConceptARC)
;; ============================================================

;; --- Spatial relationship predicates (ConceptARC categories) ---

(define (above-of? a b)
  ;; Is object a entirely above object b (no row overlap, a higher up)?
  (define ba (obj-bbox a))
  (define bb (obj-bbox b))
  (< (third ba) (first bb)))

(define (below-of? a b) (above-of? b a))

(define (left-of? a b)
  ;; Is object a entirely to the left of object b?
  (define ba (obj-bbox a))
  (define bb (obj-bbox b))
  (< (fourth ba) (second bb)))

(define (right-of? a b) (left-of? b a))

;; --- Shape & fill predicates ---

(define (filled? obj)
  ;; Is the object a SOLID shape (cells fully fill its bbox)?
  (define bb (obj-bbox obj))
  (define h (+ 1 (- (third bb) (first bb))))
  (define w (+ 1 (- (fourth bb) (second bb))))
  (= (obj-size obj) (* h w)))

(define (hollow? obj)
  ;; Object has at least one missing cell in its bbox (frame, C-shape, etc.)
  (not (filled? obj)))

(define (same-shape? a b)
  ;; Two objects have identical shape (modulo position and color).
  ;; Compares the normalized cell pattern.
  (define (normalize cells)
    (define rs (map first cells))
    (define cs (map second cells))
    (define rmin (apply min rs))
    (define cmin (apply min cs))
    (sort
      (map (lambda (c) (list (- (first c) rmin) (- (second c) cmin))) cells)
      (lambda (p q)
        (or (< (first p) (first q))
            (and (= (first p) (first q)) (< (second p) (second q)))))))
  (equal? (normalize (obj-cells a)) (normalize (obj-cells b))))

;; --- Object movement to walls (ConceptARC: MoveToBoundary) ---

(define (move-to-wall g obj-cells direction [bg 0])
  ;; Slide an object until it hits a wall (no other-object obstacles).
  ;; direction: 'up | 'down | 'left | 'right
  (define h (length g))
  (define w (length (first g)))
  (define dlt (match direction
                ['up (cons -1 0)]
                ['down (cons 1 0)]
                ['left (cons 0 -1)]
                ['right (cons 0 1)]))
  (define dr (car dlt))
  (define dc (cdr dlt))
  (define moving-set
    (for/set ([c (in-list obj-cells)]) (cons (first c) (second c))))
  (define color
    (let ([fc (first obj-cells)])
      (list-ref (list-ref g (first fc)) (second fc))))
  (define (legal-at? k)
    (andmap (lambda (c)
      (define nr (+ (first c) (* k dr)))
      (define nc (+ (second c) (* k dc)))
      (and (>= nr 0) (< nr h) (>= nc 0) (< nc w)))
      obj-cells))
  (define max-k
    (let loop ([k 0])
      (if (legal-at? (+ k 1)) (loop (+ k 1)) k)))
  (define cleared
    (for/list ([r (in-range h)])
      (for/list ([c (in-range w)])
        (if (set-member? moving-set (cons r c)) bg
            (list-ref (list-ref g r) c)))))
  (for/fold ([acc cleared]) ([cell (in-list obj-cells)])
    (define nr (+ (first cell) (* max-k dr)))
    (define nc (+ (second cell) (* max-k dc)))
    (set-cell acc nr nc color)))

;; --- Smear / propagate (icecuber smear) ---

(define (smear-color g color direction [bg 0])
  ;; For every cell of `color`, propagate it in `direction` until hitting a wall
  ;; or a non-bg cell. Returns new grid.
  ;; direction: 'up | 'down | 'left | 'right
  (define h (length g))
  (define w (length (first g)))
  (define dlt (match direction
                ['up (cons -1 0)]
                ['down (cons 1 0)]
                ['left (cons 0 -1)]
                ['right (cons 0 1)]))
  (define dr (car dlt))
  (define dc (cdr dlt))
  (define source-cells (find-color g color))
  (for/fold ([acc g]) ([sc (in-list source-cells)])
    (let loop ([acc acc] [r (+ (first sc) dr)] [c (+ (second sc) dc)])
      (cond
        [(or (< r 0) (>= r h) (< c 0) (>= c w)) acc]
        [(not (= (cell-at acc r c) bg)) acc]
        [else (loop (set-cell acc r c color) (+ r dr) (+ c dc))]))))

;; --- pickMax / pickUnique (icecuber) ---

(define (pick-max objs key-fn)
  ;; Returns the object that maximizes key-fn (first one if ties).
  (if (empty? objs) #f
      (first (sort objs (lambda (a b) (> (key-fn a) (key-fn b)))))))

(define (pick-min objs key-fn)
  (if (empty? objs) #f
      (first (sort objs (lambda (a b) (< (key-fn a) (key-fn b)))))))

(define (pick-unique objs equiv-fn)
  ;; Find the one object that is "different" from all others under equiv-fn.
  ;; Groups objects by equivalence; returns the singleton group's element.
  (cond
    [(< (length objs) 2) #f]
    [else
     (define (find-equiv-class o)
       (filter (lambda (o2) (equiv-fn o o2)) objs))
     (define singletons
       (filter (lambda (o) (= 1 (length (find-equiv-class o)))) objs))
     (if (empty? singletons) #f (first singletons))]))

;; --- Functional combinators (RE-ARC) ---

(define (power f n)
  ;; Apply f n times: (power f 3) ≡ (lambda (x) (f (f (f x))))
  (lambda (x)
    (let loop ([k n] [v x])
      (if (= k 0) v (loop (- k 1) (f v))))))

(define (fork f g h)
  ;; (fork f g h)(x) = (f (g x) (h x))
  (lambda (x) (f (g x) (h x))))

;; --- Halves (RE-ARC) ---

(define (top-half g)
  (define h (length g))
  (subgrid g 0 0 (- (quotient h 2) 1) (- (length (first g)) 1)))

(define (bottom-half g)
  (define h (length g))
  (define w (length (first g)))
  (subgrid g (quotient (+ h 1) 2) 0 (- h 1) (- w 1)))

(define (left-half g)
  (define w (length (first g)))
  (subgrid g 0 0 (- (length g) 1) (- (quotient w 2) 1)))

(define (right-half g)
  (define w (length (first g)))
  (subgrid g 0 (quotient (+ w 1) 2) (- (length g) 1) (- w 1)))

;; --- Cellwise combine (RE-ARC) ---

(define (cellwise g1 g2 fallback)
  ;; Combine two grids cell-by-cell: if cells equal, keep value, else use fallback
  (define h (length g1))
  (define w (length (first g1)))
  (grid-from-fn h w (lambda (r c)
    (define a (cell-at g1 r c))
    (define b (cell-at g2 r c))
    (if (= a b) a fallback))))

;; ============================================================
;; ERGONOMIC SHORTCUTS — extracted from mining grounded_rules.py
;; ============================================================
;; (cell-at g r c) appears 977 times across 785 rules. These shortcuts
;; collapse the most common boilerplate.

;; --- Short cell access ---
(define (at g r c) (list-ref (list-ref g r) c))   ;; alias for cell-at, 4 chars
(define cell at)                                   ;; another alias
(define (row g r) (list-ref g r))                 ;; nth row
(define (col g c)                                 ;; nth col as a list
  (for/list ([r (in-list g)]) (list-ref r c)))

;; --- Semantic positional accessors ---
;; Cells:
(define (top-left g)     (at g 0 0))
(define (top-right g)    (at g 0 (sub1 (length (first g)))))
(define (bottom-left g)  (at g (sub1 (length g)) 0))
(define (bottom-right g) (at g (sub1 (length g)) (sub1 (length (first g)))))
(define (center-cell g)
  (at g (quotient (length g) 2) (quotient (length (first g)) 2)))

;; Positions (returns (list r c)):
(define (top-left-pos g)     (list 0 0))
(define (top-right-pos g)    (list 0 (sub1 (length (first g)))))
(define (bottom-left-pos g)  (list (sub1 (length g)) 0))
(define (bottom-right-pos g) (list (sub1 (length g)) (sub1 (length (first g)))))
(define (center-pos g)
  (list (quotient (length g) 2) (quotient (length (first g)) 2)))

;; Lines (whole rows/cols):
(define (top-row g)    (first g))
(define (bottom-row g) (last g))
(define (left-col g)   (col g 0))
(define (right-col g)  (col g (sub1 (length (first g)))))

;; All four corners as values / as positions
(define (corners g)
  (list (top-left g) (top-right g) (bottom-left g) (bottom-right g)))
(define (corner-positions g)
  (list (top-left-pos g) (top-right-pos g)
        (bottom-left-pos g) (bottom-right-pos g)))

;; --- Neighbor cell access (with optional out-of-bounds value) ---
(define (cell-up g r c [oob #f])
  (if (> r 0) (at g (- r 1) c) oob))
(define (cell-down g r c [oob #f])
  (if (< r (sub1 (length g))) (at g (+ r 1) c) oob))
(define (cell-left g r c [oob #f])
  (if (> c 0) (at g r (- c 1)) oob))
(define (cell-right g r c [oob #f])
  (if (< c (sub1 (length (first g)))) (at g r (+ c 1)) oob))

(define (neighbors-4 g r c [oob #f])
  ;; Returns 4 cardinal neighbor values (up down left right). oob fills missing.
  (list (cell-up g r c oob) (cell-down g r c oob)
        (cell-left g r c oob) (cell-right g r c oob)))

(define (neighbors-8 g r c [oob #f])
  ;; All 8 neighbors in (TL T TR L R BL B BR) order.
  (define h (length g))
  (define w (length (first g)))
  (define (safe r c) (if (and (>= r 0) (< r h) (>= c 0) (< c w)) (at g r c) oob))
  (list (safe (- r 1) (- c 1)) (safe (- r 1) c) (safe (- r 1) (+ c 1))
        (safe r (- c 1))                          (safe r (+ c 1))
        (safe (+ r 1) (- c 1)) (safe (+ r 1) c) (safe (+ r 1) (+ c 1))))

;; --- Bounds & deltas (saves the in-bounds check we write 6+ times) ---
(define (in-bounds? r c h w)
  (and (>= r 0) (< r h) (>= c 0) (< c w)))

(define cardinal-deltas '((-1 0) (1 0) (0 -1) (0 1)))
(define diagonal-deltas '((-1 -1) (-1 1) (1 -1) (1 1)))
(define all-8-deltas
  '((-1 -1) (-1 0) (-1 1) (0 -1) (0 1) (1 -1) (1 0) (1 1)))

;; --- Position enumeration (saves the verbose flatmap pattern) ---
(define (grid-positions g)
  ;; All (r c) lists in row-major order.
  (define h (length g))
  (define w (length (first g)))
  (for*/list ([r (in-range h)] [c (in-range w)]) (list r c)))

(define (grid-positions-pairs g)
  ;; Same but as cons pairs.
  (define h (length g))
  (define w (length (first g)))
  (for*/list ([r (in-range h)] [c (in-range w)]) (cons r c)))

(define (positions-of g pred)
  ;; All (r c) where (pred (cell-at g r c)) is true. pred takes one arg (the value).
  (filter (lambda (p) (pred (at g (first p) (second p))))
          (grid-positions g)))

;; Inclusive rectangle positions, in row-major order.
(define (positions-in-rect r1 c1 r2 c2)
  (for*/list ([r (in-range r1 (add1 r2))]
              [c (in-range c1 (add1 c2))])
    (list r c)))

(define (bbox-of-cells cells)
  ;; Bounding box of (r c) cells: (r1 c1 r2 c2), or #f for empty input.
  (if (empty? cells)
      #f
      (let ([rs (map fst cells)]
            [cs (map snd cells)])
        (list (apply min rs) (apply min cs) (apply max rs) (apply max cs)))))

;; --- Folding over the whole grid ---
(define (for-each-cell g fn)
  ;; (fn r c v) called for each cell. Returns (void).
  (define h (length g))
  (define w (length (first g)))
  (for* ([r (in-range h)] [c (in-range w)]) (fn r c (at g r c))))

(define (fold-cells g init fn)
  ;; (fn acc r c v) for each cell. Returns final acc.
  (for*/fold ([acc init])
             ([r (in-range (length g))]
              [c (in-range (length (first g)))])
    (fn acc r c (at g r c))))

;; --- Common list/cell painting helpers ---
(define (mode-list vals [ignore #f])
  ;; Most frequent value in a list. If ignore is supplied, skip matching values.
  (define freq (make-hash))
  (for ([v (in-list vals)])
    (unless (and (not (eq? ignore #f)) (equal? v ignore))
      (hash-update! freq v add1 0)))
  (if (hash-empty? freq)
      #f
      (car (first (sort (hash->list freq) (lambda (a b) (> (cdr a) (cdr b))))))))

(define (paint-cells g cells [color #f])
  ;; Paint (r c) or (r c value) cells. Explicit color overrides per-cell value.
  (foldl (lambda (cell acc)
           (let* ([r (fst cell)]
                  [c (snd cell)]
                  [v (if (eq? color #f)
                         (if (and (list? cell) (>= (length cell) 3))
                             (third cell)
                             (at acc r c))
                         color)])
             (if (in-bounds? r c (rows acc) (cols acc))
                 (set-cell acc r c v)
                 acc)))
         g cells))

(define (erase-cells g cells [bg 0])
  (paint-cells g cells bg))

;; --- Object coordinate accessors (extracted: 5+ occurrences each) ---
(define (obj-rs obj)
  ;; List of row coordinates of obj's cells.
  (map first (obj-cells obj)))
(define (obj-cs obj)
  ;; List of col coordinates of obj's cells.
  (map second (obj-cells obj)))
(define (obj-row-range obj)
  ;; (rmin rmax)
  (define rs (obj-rs obj))
  (list (apply min rs) (apply max rs)))
(define (obj-col-range obj)
  (define cs (obj-cs obj))
  (list (apply min cs) (apply max cs)))
(define (obj-r1 obj) (first (obj-bbox obj)))
(define (obj-c1 obj) (second (obj-bbox obj)))
(define (obj-r2 obj) (third (obj-bbox obj)))
(define (obj-c2 obj) (fourth (obj-bbox obj)))
(define (obj-h obj)  (+ 1 (- (obj-r2 obj) (obj-r1 obj))))
(define (obj-w obj)  (+ 1 (- (obj-c2 obj) (obj-c1 obj))))

;; --- Grid edge positions (for "border" tasks) ---
(define (border-positions g)
  ;; All (r c) on the outer border of the grid.
  (define h (length g))
  (define w (length (first g)))
  (define top    (for/list ([c (in-range w)]) (list 0 c)))
  (define bot    (for/list ([c (in-range w)]) (list (- h 1) c)))
  (define lft    (for/list ([r (in-range 1 (- h 1))]) (list r 0)))
  (define rgt    (for/list ([r (in-range 1 (- h 1))]) (list r (- w 1))))
  (append top bot lft rgt))

(define (interior-positions g)
  ;; All (r c) NOT on the outer border.
  (define h (length g))
  (define w (length (first g)))
  (for*/list ([r (in-range 1 (- h 1))] [c (in-range 1 (- w 1))]) (list r c)))

;; ============================================================
;; BASIC MATRIX / GRID OPERATIONS
;; ============================================================

;; --- Cell-wise binary combine ---
(define (zip-grids g1 g2 fn)
  ;; Combine two same-sized grids cell by cell. fn takes (a b) → c.
  (define h (length g1))
  (define w (length (first g1)))
  (grid-from-fn h w (lambda (r c) (fn (at g1 r c) (at g2 r c)))))

(define (grid-and g1 g2 [bg 0])
  ;; Both cells non-bg → keep g1's value, else bg.
  (zip-grids g1 g2 (lambda (a b) (if (and (not (= a bg)) (not (= b bg))) a bg))))

(define (grid-or g1 g2 [bg 0])
  ;; Either cell non-bg → that value (g1 wins ties), else bg.
  (zip-grids g1 g2 (lambda (a b) (cond [(not (= a bg)) a]
                                        [(not (= b bg)) b]
                                        [else bg]))))

(define (grid-xor g1 g2 [bg 0] [on 1])
  ;; Exactly one cell non-bg → on, else bg.
  (zip-grids g1 g2 (lambda (a b)
    (let ([na (not (= a bg))] [nb (not (= b bg))])
      (if (or (and na (not nb)) (and (not na) nb)) on bg)))))

(define (grid-diff g1 g2 [same-color 0] [diff-color 1])
  ;; Cells where g1 and g2 differ → diff-color, same → same-color.
  (zip-grids g1 g2 (lambda (a b) (if (= a b) same-color diff-color))))

(define (grid-overlay-on g1 g2 [bg 0])
  ;; g2 cells override g1 wherever g2 is non-bg.
  (zip-grids g1 g2 (lambda (a b) (if (= b bg) a b))))

;; --- Concatenation ---
(define (hconcat g1 g2)
  ;; Side-by-side. Heights must match.
  (for/list ([r1 (in-list g1)] [r2 (in-list g2)]) (append r1 r2)))

(define (vconcat g1 g2)
  ;; Top-on-bottom. Widths must match.
  (append g1 g2))

(define (stack-grids dir grids)
  ;; dir: 'horizontal | 'vertical. Stacks all grids in the list.
  (cond
    [(empty? grids) '()]
    [(empty? (rest grids)) (first grids)]
    [(eq? dir 'horizontal) (foldl (lambda (g acc) (hconcat acc g)) (first grids) (rest grids))]
    [(eq? dir 'vertical)   (foldl (lambda (g acc) (vconcat acc g)) (first grids) (rest grids))]
    [else (error 'stack-grids "dir must be 'horizontal or 'vertical")]))

;; --- Diagonals ---
(define (diagonal g)
  ;; Main diagonal as a list of values (top-left to bottom-right).
  (define n (min (length g) (length (first g))))
  (for/list ([i (in-range n)]) (at g i i)))

(define (anti-diagonal g)
  ;; Anti-diagonal (top-right to bottom-left).
  (define h (length g))
  (define w (length (first g)))
  (define n (min h w))
  (for/list ([i (in-range n)]) (at g i (- w 1 i))))

;; --- Padding ---
(define (pad-grid g n [color 0])
  ;; Add an n-wide border of `color` around the grid.
  (define h (length g))
  (define w (length (first g)))
  (define new-h (+ h (* 2 n)))
  (define new-w (+ w (* 2 n)))
  (grid-from-fn new-h new-w (lambda (r c)
    (let ([gr (- r n)] [gc (- c n)])
      (if (and (>= gr 0) (< gr h) (>= gc 0) (< gc w))
          (at g gr gc)
          color)))))

(define (pad-grid-asym g top bottom left right [color 0])
  ;; Asymmetric padding.
  (define h (length g))
  (define w (length (first g)))
  (grid-from-fn (+ h top bottom) (+ w left right) (lambda (r c)
    (let ([gr (- r top)] [gc (- c left)])
      (if (and (>= gr 0) (< gr h) (>= gc 0) (< gc w))
          (at g gr gc)
          color)))))

;; --- Row/column reductions ---
(define (row-uniform? g r)
  ;; Are all cells in row r the same value?
  (define vals (row g r))
  (andmap (lambda (v) (= v (first vals))) (rest vals)))

(define (col-uniform? g c)
  (define vals (col g c))
  (andmap (lambda (v) (= v (first vals))) (rest vals)))

(define (row-count g r v)
  ;; How many cells in row r equal v.
  (length (filter (lambda (x) (= x v)) (row g r))))

(define (col-count g c v)
  (length (filter (lambda (x) (= x v)) (col g c))))

(define (row-mode g r [bg #f])
  ;; Most common value in row r. If bg given, exclude it.
  (define vals (row g r))
  (define filtered (if bg (filter (lambda (v) (not (= v bg))) vals) vals))
  (if (empty? filtered) bg
      (let ([freq (map (lambda (v) (cons v (length (filter (lambda (x) (= x v)) filtered))))
                       (remove-duplicates filtered))])
        (car (first (sort freq (lambda (a b) (> (cdr a) (cdr b)))))))))

(define (col-mode g c [bg #f])
  (define vals (col g c))
  (define filtered (if bg (filter (lambda (v) (not (= v bg))) vals) vals))
  (if (empty? filtered) bg
      (let ([freq (map (lambda (v) (cons v (length (filter (lambda (x) (= x v)) filtered))))
                       (remove-duplicates filtered))])
        (car (first (sort freq (lambda (a b) (> (cdr a) (cdr b)))))))))

;; --- Distinct rows / cols ---
(define (unique-rows g)
  ;; Removes duplicate rows (keeps first occurrence).
  (remove-duplicates g))

(define (unique-cols g)
  ;; Removes duplicate columns.
  (define cols-list (apply map list g))
  (define dedup (remove-duplicates cols-list))
  (apply map list dedup))

;; ============================================================
;; WISHLIST ADDITIONS — high-value primitives from API design
;; ============================================================

;; --- Coordinate (position) arithmetic ---
;; Positions are still (list r c) — just helpers, no new types.
(define (pos-r p) (first p))
(define (pos-c p) (second p))
(define (pos+ p1 p2) (list (+ (first p1) (first p2)) (+ (second p1) (second p2))))
(define (pos- p1 p2) (list (- (first p1) (first p2)) (- (second p1) (second p2))))
(define (pos* p k)   (list (* (first p) k) (* (second p) k)))
(define (pos-eq? p1 p2) (and (= (first p1) (first p2)) (= (second p1) (second p2))))
(define (pos-manhattan p1 p2)
  (+ (abs (- (first p1) (first p2))) (abs (- (second p1) (second p2)))))
(define (pos-chebyshev p1 p2)
  (max (abs (- (first p1) (first p2))) (abs (- (second p1) (second p2)))))
(define (pos-in-bounds? p h w)
  (in-bounds? (first p) (second p) h w))

;; --- Pixel & color operations ---
(define (pixel-swap g r1 c1 r2 c2)
  ;; Swap the values at two positions.
  (let ([v1 (at g r1 c1)] [v2 (at g r2 c2)])
    (set-cell (set-cell g r1 c1 v2) r2 c2 v1)))

(define (color-shift g k [bg 0])
  ;; Add k to every non-bg color, modulo 10. Useful for "color rotate" puzzles.
  (define h (length g))
  (define w (length (first g)))
  (grid-from-fn h w (lambda (r c)
    (let ([v (at g r c)])
      (if (= v bg) bg
          (let ([nv (modulo (+ v k) 10)])
            (if (= nv 0) 1 nv)))))))   ; never produce bg from non-bg

(define (color-majority g [bg 0])
  ;; Color covering >50% of non-bg cells, or #f if no majority.
  (define vals (filter (lambda (v) (not (= v bg)))
                       (apply append g)))
  (define total (length vals))
  (cond
    [(= total 0) #f]
    [else
     (define freqs (map (lambda (c) (cons c (length (filter (lambda (v) (= v c)) vals))))
                        (remove-duplicates vals)))
     (define winner (first (sort freqs (lambda (a b) (> (cdr a) (cdr b))))))
     (if (> (cdr winner) (quotient total 2)) (car winner) #f)]))

;; --- "Color majority IN a shape" family ---
;; Pattern that recurs ~50+ times across grounded rules: collect the
;; values of `g` at a list of (r c) cells, then take the mode/majority.
;;
;; mode-in            argmax of cell values in `cells` (ignores bg by default).
;;                    Ties → first-seen wins (mode-list semantics).
;; majority-color-in  same, but #f unless one color holds strict >50%.
;; obj-mode-color     convenience: mode-in over (obj-cells obj).
;; obj-majority-color convenience: majority-color-in over (obj-cells obj).
;;
;; All four take an optional `bg` (default 0). Pass `#f` for bg to count
;; every value, including 0.
(define (_cell-vals-of cells g)
  (map (lambda (p) (cell-at g (first p) (second p))) cells))

(define (mode-in cells g [bg 0])
  ;; Most common color among cells of `g` listed in `cells`. Excludes bg
  ;; unless bg is #f. Returns #f if every cell is bg / cells is empty.
  (define vals (if (eq? bg #f)
                   (_cell-vals-of cells g)
                   (filter (lambda (v) (not (= v bg)))
                           (_cell-vals-of cells g))))
  (mode-list vals))

(define (majority-color-in cells g [bg 0])
  ;; Color holding >50% of non-bg cells in `cells`, or #f if no clear majority.
  (define vals (if (eq? bg #f)
                   (_cell-vals-of cells g)
                   (filter (lambda (v) (not (= v bg)))
                           (_cell-vals-of cells g))))
  (define total (length vals))
  (cond
    [(= total 0) #f]
    [else
     (define freqs (map (lambda (c)
                          (cons c (length (filter (lambda (v) (= v c)) vals))))
                        (remove-duplicates vals)))
     (define winner (first (sort freqs (lambda (a b) (> (cdr a) (cdr b))))))
     (if (> (cdr winner) (quotient total 2)) (car winner) #f)]))

(define (obj-mode-color obj g [bg 0])
  (mode-in (obj-cells obj) g bg))

(define (obj-majority-color obj g [bg 0])
  (majority-color-in (obj-cells obj) g bg))

;; --- Object: translate / paint / erase / merge / intersect ---
(define (object-translate g obj dr dc)
  ;; Move obj on g by (dr, dc). Erases original cells, paints at new positions.
  (define color (obj-color obj))
  (define cells (obj-cells obj))
  (define cleared (erase-cells g cells 0))
  (define moved
    (filter (lambda (cell) (in-bounds? (first cell) (second cell) (rows g) (cols g)))
            (map (lambda (cell) (list (+ (first cell) dr) (+ (second cell) dc))) cells)))
  (paint-cells cleared moved color))

(define (object-paint g obj [color #f])
  ;; Paint obj onto g (using obj's color, or override).
  (paint-cells g (obj-cells obj) (or color (obj-color obj))))

(define (object-erase g obj [bg 0])
  ;; Replace obj's cells on g with bg.
  (erase-cells g (obj-cells obj) bg))

(define (object-cells-set obj)
  (for/set ([c (in-list (obj-cells obj))]) (cons (first c) (second c))))

(define (object-intersect obj1 obj2)
  ;; List of cells in BOTH objects.
  (define s2 (object-cells-set obj2))
  (filter (lambda (c) (set-member? s2 (cons (first c) (second c))))
          (obj-cells obj1)))

;; --- Object growth/shrink ---
(define (object-grow obj [connectivity 4])
  ;; Add a 1-pixel layer around the object. Returns list of NEW cells added.
  (obj-neighbor-cells obj connectivity))

(define (object-shrink obj [connectivity 4])
  ;; Remove the 1-pixel boundary. Returns interior cells.
  (obj-interior-cells obj connectivity))

;; --- Topology ---
(define (topo-count-holes g obj [bg 0])
  ;; Number of bg-color enclosed regions inside obj's bbox.
  ;; Counts 4-connected bg components inside the obj's bbox that are
  ;; NOT connected to the bbox border (those that the object encloses).
  (define bb (obj-bbox obj))
  (define r1 (first bb)) (define c1 (second bb))
  (define r2 (third bb)) (define c2 (fourth bb))
  (define sub (subgrid g r1 c1 r2 c2))
  (define h (length sub))
  (define w (length (first sub))) 
  ;; Find bg objects in the sub-bbox NOT touching the border
  (define bg-objs
    (filter
      (lambda (o)
        (let ([cells (obj-cells o)])
          (andmap (lambda (cell)
            (and (> (first cell) 0)
                 (< (first cell) (- h 1))
                 (> (second cell) 0)
                 (< (second cell) (- w 1))))
            cells)))
      (objects sub (obj-color obj))))
  (length bg-objs))

(define (topo-rectangle? obj)
  ;; Is the object a perfect solid rectangle (cells fill its bbox completely)?
  (filled? obj))

(define (topo-corners obj)
  ;; The 4 corner cells of the object's bbox (only those that are in the object).
  (define bb (obj-bbox obj))
  (define cs (object-cells-set obj))
  (filter (lambda (p) (set-member? cs (cons (first p) (second p))))
          (list (list (first bb)  (second bb))
                (list (first bb)  (fourth bb))
                (list (third bb)  (second bb))
                (list (third bb)  (fourth bb)))))

;; --- Physics: raycasting, line-of-sight, billiards ---
(define (phys-raycast g start-r start-c dr dc [bg 0])
  ;; Cast a ray from (start-r, start-c) in direction (dr, dc).
  ;; Returns the (r c) of the first non-bg cell hit, or #f if hit the edge.
  (define h (length g))
  (define w (length (first g)))
  (let loop ([r (+ start-r dr)] [c (+ start-c dc)])
    (cond
      [(or (< r 0) (>= r h) (< c 0) (>= c w)) #f]
      [(not (= (at g r c) bg)) (list r c)]
      [else (loop (+ r dr) (+ c dc))])))

(define (phys-distance g start-r start-c dr dc [bg 0])
  ;; Number of bg cells in direction (dr, dc) before hitting non-bg or edge.
  (define h (length g))
  (define w (length (first g)))
  (let loop ([r (+ start-r dr)] [c (+ start-c dc)] [k 0])
    (cond
      [(or (< r 0) (>= r h) (< c 0) (>= c w)) k]
      [(not (= (at g r c) bg)) k]
      [else (loop (+ r dr) (+ c dc) (+ k 1))])))

(define (phys-has-los? g r1 c1 r2 c2 [bg 0])
  ;; Line of sight: is the straight line between (r1,c1) and (r2,c2) all bg?
  ;; Only checks horizontal, vertical, or 45° diagonals (returns #f otherwise).
  (define dr (- r2 r1))
  (define dc (- c2 c1))
  (cond
    [(and (= dr 0) (= dc 0)) #t]
    [(and (= dr 0)) (andmap (lambda (c) (= (at g r1 c) bg))
                            (range (+ (min c1 c2) 1) (max c1 c2)))]
    [(and (= dc 0)) (andmap (lambda (r) (= (at g r c1) bg))
                            (range (+ (min r1 r2) 1) (max r1 r2)))]
    [(= (abs dr) (abs dc))
     (let* ([sdr (if (> dr 0) 1 -1)]
            [sdc (if (> dc 0) 1 -1)]
            [n (abs dr)])
       (andmap (lambda (k) (= (at g (+ r1 (* k sdr)) (+ c1 (* k sdc))) bg))
               (range 1 n)))]
    [else #f]))

(define (phys-bounce-ray g start-r start-c dr dc color max-bounces [bg 0])
  ;; Draw a ray from (start-r, start-c) in direction (dr, dc), bouncing
  ;; off non-bg cells. Returns the modified grid with `color` painted along
  ;; the ray's path. Stops after `max-bounces` reflections.
  (define h (length g))
  (define w (length (first g)))
  (let loop ([acc g] [r start-r] [c start-c] [dr dr] [dc dc] [bounces 0])
    (cond
      [(> bounces max-bounces) acc]
      [(or (< r 0) (>= r h) (< c 0) (>= c w)) acc]
      [else
       (let* ([nr (+ r dr)] [nc (+ c dc)]
              [hit-r? (or (< nr 0) (>= nr h))]
              [hit-c? (or (< nc 0) (>= nc w))]
              [hit-cell? (and (not hit-r?) (not hit-c?) (not (= (at acc nr nc) bg)))]
              [acc2 (set-cell acc r c color)])
         (cond
           [(or hit-r? hit-c? hit-cell?)
            ;; Bounce: invert appropriate component
            (let ([new-dr (if (or hit-r? (and hit-cell? #t)) (- dr) dr)]
                  [new-dc (if (or hit-c? (and hit-cell? #t)) (- dc) dc)])
              ;; If only an edge, flip just that axis. Otherwise flip both.
              (cond
                [hit-r? (loop acc2 r c (- dr) dc (+ bounces 1))]
                [hit-c? (loop acc2 r c dr (- dc) (+ bounces 1))]
                [else (loop acc2 r c (- dr) (- dc) (+ bounces 1))]))]
           [else (loop acc2 nr nc dr dc bounces)]))])))

;; --- Object clustering ---
(define (cluster-by key-fn objs)
  ;; Group objs into a list of lists, by key-fn value.
  (define groups (make-hash))
  (for ([o (in-list objs)])
    (define k (key-fn o))
    (hash-update! groups k (lambda (lst) (cons o lst)) '()))
  (hash-values groups))

(define (cluster-by-color objs)
  (cluster-by obj-color objs))
(define (cluster-by-size objs)
  (cluster-by obj-size objs))

(define (cluster-aligned-row objs)
  ;; Group objs whose bbox top edge is on the same row.
  (cluster-by (lambda (o) (first (obj-bbox o))) objs))

(define (cluster-aligned-col objs)
  (cluster-by (lambda (o) (second (obj-bbox o))) objs))

;; --- Image processing filters ---
(define (filter-noise-remove g min-size [bg 0])
  ;; Remove all objects (4-connected) with cells < min-size.
  (define small-objs (filter (lambda (o) (< (obj-size o) min-size))
                              (objects-multicolor g bg)))
  (foldl (lambda (o acc) (object-erase acc o bg)) g small-objs))

(define (filter-erode-color g color [bg 0])
  ;; Erode: any cell of `color` that has a non-color neighbor (4-conn) becomes bg.
  (define h (length g))
  (define w (length (first g)))
  (grid-from-fn h w (lambda (r c)
    (cond
      [(not (= (at g r c) color)) (at g r c)]
      [(or (and (> r 0)        (not (= (at g (- r 1) c) color)))
           (and (< r (- h 1))  (not (= (at g (+ r 1) c) color)))
           (and (> c 0)        (not (= (at g r (- c 1)) color)))
           (and (< c (- w 1))  (not (= (at g r (+ c 1)) color)))
           (= r 0) (= r (- h 1)) (= c 0) (= c (- w 1)))
       bg]
      [else color]))))

(define (filter-dilate-color g color [bg 0])
  ;; Dilate: any bg cell with a 4-neighbor of `color` becomes `color`.
  (define h (length g))
  (define w (length (first g)))
  (grid-from-fn h w (lambda (r c)
    (cond
      [(not (= (at g r c) bg)) (at g r c)]
      [(or (and (> r 0)        (= (at g (- r 1) c) color))
           (and (< r (- h 1))  (= (at g (+ r 1) c) color))
           (and (> c 0)        (= (at g r (- c 1)) color))
           (and (< c (- w 1))  (= (at g r (+ c 1)) color)))
       color]
      [else (at g r c)]))))

;; --- Drawing helpers ---
(define (draw-rect-filled g r1 c1 r2 c2 color)
  ;; Fill rectangle (r1,c1)-(r2,c2) inclusive with color.
  (define h (length g))
  (define w (length (first g)))
  (grid-from-fn h w (lambda (r c)
    (if (and (>= r r1) (<= r r2) (>= c c1) (<= c c2))
        color
        (at g r c)))))

(define (draw-rect-outline g r1 c1 r2 c2 color)
  ;; Draw only the rectangle's border.
  (define h (length g))
  (define w (length (first g)))
  (grid-from-fn h w (lambda (r c)
    (if (and (>= r r1) (<= r r2) (>= c c1) (<= c c2)
             (or (= r r1) (= r r2) (= c c1) (= c c2)))
        color
        (at g r c)))))

(define (draw-cross g r c color)
  (define h (length g))
  (define w (length (first g)))
  (grid-from-fn h w (lambda (rr cc)
    (if (or (= rr r) (= cc c)) color (at g rr cc)))))

(define (draw-x-shape g r c color)
  ;; Two diagonals intersecting at (r,c).
  (define h (length g))
  (define w (length (first g)))
  (grid-from-fn h w (lambda (rr cc)
    (if (or (= (- rr r) (- cc c))
            (= (- rr r) (- (- cc c))))
        color
        (at g rr cc)))))

(define (draw-border g color)
  ;; Paint the outer border of the grid with color.
  (define h (length g))
  (define w (length (first g)))
  (grid-from-fn h w (lambda (r c)
    (if (or (= r 0) (= r (- h 1)) (= c 0) (= c (- w 1)))
        color
        (at g r c)))))

;; --- Grid hashing (for memoization) ---
(define (grid-hash g)
  (equal-hash-code g))

(define (shape-hash obj)
  ;; Hash based on object shape ignoring color & translation.
  (define cells (obj-cells obj))
  (define rs (map first cells))
  (define cs (map second cells))
  (define rmin (apply min rs))
  (define cmin (apply min cs))
  (define normalized
    (sort (map (lambda (c) (list (- (first c) rmin) (- (second c) cmin))) cells)
          (lambda (a b)
            (or (< (first a) (first b))
                (and (= (first a) (first b)) (< (second a) (second b)))))))
  (equal-hash-code normalized))

;; --- Example diff helpers (for analogy reasoning) ---
(define (diff-positions g1 g2)
  ;; Return list of (r c) where g1 and g2 differ.
  (define h (length g1))
  (define w (length (first g1)))
  (filter values
    (for*/list ([r (in-range h)] [c (in-range w)])
      (if (= (at g1 r c) (at g2 r c)) #f (list r c)))))

(define (diff-recolor-map g1 g2)
  ;; If g1 and g2 differ ONLY by recoloring (same shape), return a list of
  ;; (list old new) pairs. Otherwise #f.
  (define h (length g1))
  (define w (length (first g1)))
  (cond
    [(or (not (= h (length g2))) (not (= w (length (first g2))))) #f]
    [else
     (define mapping (make-hash))
     (define ok
       (for*/and ([r (in-range h)] [c (in-range w)])
         (let ([a (at g1 r c)] [b (at g2 r c)])
           (cond
             [(hash-has-key? mapping a) (= (hash-ref mapping a) b)]
             [else (hash-set! mapping a b) #t]))))
     (if ok
         (for/list ([k (in-list (sort (hash-keys mapping) <))])
           (list k (hash-ref mapping k)))
         #f)]))

(define (diff-translation g1 g2 [bg 0])
  ;; If g2 is g1 shifted by (dr, dc), return (list dr dc). Otherwise #f.
  (define h (length g1))
  (define w (length (first g1)))
  (cond
    [(or (not (= h (length g2))) (not (= w (length (first g2))))) #f]
    [else
     ;; Find a non-bg cell in g1, find the corresponding cell in g2
     (define c1 (find (lambda (p) (not (= (at g1 (first p) (second p)) bg)))
                      (grid-positions g1)))
     (define c2 (find (lambda (p) (not (= (at g2 (first p) (second p)) bg)))
                      (grid-positions g2)))
     (cond
       [(or (not c1) (not c2)) #f]
       [else
        (define dr (- (first c2) (first c1)))
        (define dc (- (second c2) (second c1)))
        ;; Verify all non-bg cells of g1 shift cleanly to g2
        (define ok
          (andmap (lambda (p)
            (let ([v (at g1 (first p) (second p))])
              (or (= v bg)
                  (let ([nr (+ (first p) dr)] [nc (+ (second p) dc)])
                    (and (in-bounds? nr nc h w) (= (at g2 nr nc) v))))))
            (grid-positions g1)))
        (if ok (list dr dc) #f)])]))

;; ============================================================
;; NEW PRIMITIVES — added 2026-04-12
;; ============================================================

;; safe-at: bounds-checked cell access, returns default if out of bounds
(define (safe-at g r c [default 0])
  (if (in-bounds? r c (rows g) (cols g))
      (cell-at g r c)
      default))

;; local-signature: row-major square neighborhood around a cell.
(define (local-signature g r c radius [default -1])
  (for*/list ([dr (range (- radius) (+ radius 1))]
              [dc (range (- radius) (+ radius 1))])
    (safe-at g (+ r dr) (+ c dc) default)))

;; apply-local-rewrite: exact context table of (new-color signature) entries.
(define (apply-local-rewrite g radius patterns [default -1])
  (map-grid g
    (lambda (r c v)
      (let* ([sig (local-signature g r c radius default)]
             [hit (find-first (lambda (p) (equal? sig (second p))) patterns)])
        (if hit (first hit) v)))))

;; normalize-cells: shift (r c) cell list so min-r = min-c = 0
(define (normalize-cells cells)
  (if (empty? cells) '()
      (let ([bb (bbox-of-cells cells)])
        (map (lambda (c) (list (- (first c) (first bb))
                                (- (second c) (second bb))))
             cells))))

;; recolor-cells: paint a list of (r c) positions to a single color (simpler than paint-cells)
(define (recolor-cells g cells color)
  ;; Cells may be proper lists (r c …) OR cons pairs (r . c). Use fst/snd
  ;; so both forms work; find-color returns cons pairs and is the most
  ;; common source of cells in the corpus.
  (foldl (lambda (cell acc)
    (let ([r (fst cell)] [c (snd cell)])
      (if (in-bounds? r c (rows acc) (cols acc))
          (set-cell acc r c color)
          acc)))
    g cells))

;; connected-region: BFS from a seed cell, expanding via a predicate
;; pred? takes (r c val) and returns #t if the cell should be included.
;; Returns a list of (r c) positions in the connected region.
(define (connected-region g start-r start-c pred? [connectivity 4])
  (define h (rows g)) (define w (cols g))
  (define visited (make-hash))
  (define deltas (if (= connectivity 8) all-8-deltas cardinal-deltas))
  (define result '())
  (let bfs ([queue (list (list start-r start-c))])
    (unless (empty? queue)
      (let* ([cur (first queue)]
             [r (first cur)] [c (second cur)]
             [rest (cdr queue)])
        (cond
          [(hash-has-key? visited cur) (bfs rest)]
          [(not (in-bounds? r c h w)) (bfs rest)]
          [(not (pred? r c (cell-at g r c))) (bfs rest)]
          [else
           (hash-set! visited cur #t)
           (set! result (cons cur result))
           (bfs (append rest
                  (map (lambda (d) (list (+ r (first d)) (+ c (second d)))) deltas)))]))))
  (reverse result))

;; draw-line: Bresenham line from (r1,c1) to (r2,c2), returns list of (r c) positions
(define (line-cells r1 c1 r2 c2)
  (define dr (abs (- r2 r1)))
  (define dc (abs (- c2 c1)))
  (define sr (if (< r1 r2) 1 -1))
  (define sc (if (< c1 c2) 1 -1))
  (let loop ([r r1] [c c1] [err (- dr dc)] [acc '()])
    (define acc2 (cons (list r c) acc))
    (if (and (= r r2) (= c c2))
        (reverse acc2)
        (let* ([e2 (* 2 err)]
               [nr (if (> e2 (- dc)) (+ r sr) r)]
               [nc (if (< e2 dr) (+ c sc) c)]
               [ne (+ err
                      (if (> e2 (- dc)) (- dc) 0)
                      (if (< e2 dr) dr 0))])
          (loop nr nc ne acc2)))))

;; draw-line: paint a line onto a grid
(define (draw-line g r1 c1 r2 c2 color)
  (recolor-cells g (line-cells r1 c1 r2 c2) color))

;; obj-center: integer center of an object's bounding box
(define (obj-center obj)
  (list (quotient (+ (obj-r1 obj) (obj-r2 obj)) 2)
        (quotient (+ (obj-c1 obj) (obj-c2 obj)) 2)))

;; --- Shape transform matching ---

;; rotate-cells-cw: rotate (r c) list 90° clockwise around origin
(define (rotate-cells-cw cells)
  (map (lambda (p) (list (second p) (- (first p)))) cells))

;; flip-cells-lr: flip (r c) list left-right
(define (flip-cells-lr cells)
  (map (lambda (p) (list (first p) (- (second p)))) cells))

;; all-transforms: return all 8 orientations of a cell list (normalized)
(define (all-transforms cells)
  (define (norm cs) (sort (normalize-cells cs)
    (lambda (a b) (if (= (first a) (first b)) (< (second a) (second b)) (< (first a) (first b))))))
  (define r0 cells)
  (define r1 (rotate-cells-cw r0))
  (define r2 (rotate-cells-cw r1))
  (define r3 (rotate-cells-cw r2))
  (define f0 (flip-cells-lr r0))
  (define f1 (rotate-cells-cw f0))
  (define f2 (rotate-cells-cw f1))
  (define f3 (rotate-cells-cw f2))
  (list (norm r0) (norm r1) (norm r2) (norm r3)
        (norm f0) (norm f1) (norm f2) (norm f3)))

;; match-transform: check if cells-b matches any rotation/flip of cells-a
;; Returns the index (0-7) of the matching transform, or #f
;; 0=identity, 1=cw90, 2=180, 3=ccw90, 4=flip-lr, 5=flip+cw90, 6=flip+180, 7=flip+ccw90
(define (match-transform cells-a cells-b)
  (define transforms (all-transforms cells-a))
  (define target (sort (normalize-cells cells-b)
    (lambda (a b) (if (= (first a) (first b)) (< (second a) (second b)) (< (first a) (first b))))))
  (let loop ([i 0])
    (cond
      [(>= i 8) #f]
      [(equal? (list-ref transforms i) target) i]
      [else (loop (+ i 1))])))

;; --- Convex hull ---

;; convex-hull: Graham scan on (r c) points, returns hull vertices in order
(define (convex-hull points)
  (define pts (sort (remove-duplicates points)
    (lambda (a b) (if (= (first a) (first b)) (< (second a) (second b)) (< (first a) (first b))))))
  (if (<= (length pts) 1) pts
    (let ()
      (define (cross o a b)
        (- (* (- (first a) (first o)) (- (second b) (second o)))
           (* (- (second a) (second o)) (- (first b) (first o)))))
      (define (build-half ps)
        (foldl (lambda (p hull)
          (let trim ([h hull])
            (if (and (>= (length h) 2) (<= (cross (second h) (first h) p) 0))
                (trim (cdr h))
                (cons p h))))
          '() ps))
      (define lower (reverse (build-half pts)))
      (define upper (reverse (build-half (reverse pts))))
      (append (drop-right lower 1) (drop-right upper 1)))))

;; point-in-hull?: ray-casting test for point inside convex polygon
(define (point-in-hull? pr pc hull)
  (define n (length hull))
  (let loop ([i 0] [j (- n 1)] [inside #f])
    (if (>= i n) inside
      (let* ([ri (first (list-ref hull i))] [ci (second (list-ref hull i))]
             [rj (first (list-ref hull j))] [cj (second (list-ref hull j))]
             [ci-above (> ci pc)]
             [cj-above (> cj pc)]
             [cross? (and (not (equal? ci-above cj-above))
                          (< (+ 0.0 pr) (+ ri (/ (* (- rj ri) (- pc ci)) (- cj ci)))))])
        (loop (+ i 1) i (if cross? (not inside) inside))))))

;; convex-hull-fill: fill the convex hull of points on a grid with color
;; Expands each point to pixel corners so boundary cells are included
(define (convex-hull-fill g points color)
  (if (< (length points) 3) g
    (let* ([expanded (apply append
            (map (lambda (p)
              (let ([r (first p)] [c (second p)])
                (list (list (- r 0.5) (- c 0.5)) (list (- r 0.5) (+ c 0.5))
                      (list (+ r 0.5) (- c 0.5)) (list (+ r 0.5) (+ c 0.5)))))
              points))]
           [hull (convex-hull expanded)]
           [bb (bbox-of-cells points)]
           [r1 (first bb)] [c1 (second bb)] [r2 (third bb)] [c2 (fourth bb)])
      (foldl (lambda (pos acc)
        (let ([r (first pos)] [c (second pos)])
          (if (point-in-hull? r c hull)
              (set-cell acc r c color)
              acc)))
        g (positions-in-rect r1 c1 r2 c2)))))

;; --- Spiral generation ---

;; spiral-cells: generate a clockwise spiral path from (sr,sc) within an h×w grid
;; Returns list of (r c) in spiral order
(define (spiral-cells h w [sr 0] [sc 0])
  (define visited (make-hash))
  ;; Directions: right, down, left, up (clockwise)
  (define dirs '((0 1) (1 0) (0 -1) (-1 0)))
  (let loop ([r sr] [c sc] [di 0] [acc '()] [count 0])
    (if (>= count (* h w)) (reverse acc)
      (let* ([new-acc (cons (list r c) acc)]
             [dummy (hash-set! visited (list r c) #t)]
             [cur-dir (list-ref dirs di)]
             [dr (first cur-dir)] [dc (second cur-dir)]
             [nr (+ r dr)] [nc (+ c dc)])
        (if (and (in-bounds? nr nc h w) (not (hash-has-key? visited (list nr nc))))
            (loop nr nc di new-acc (+ count 1))
            ;; Try turning right
            (let* ([ndi (modulo (+ di 1) 4)]
                   [next-dir (list-ref dirs ndi)]
                   [dr2 (first next-dir)] [dc2 (second next-dir)]
                   [nr2 (+ r dr2)] [nc2 (+ c dc2)])
              (if (and (in-bounds? nr2 nc2 h w) (not (hash-has-key? visited (list nr2 nc2))))
                  (loop nr2 nc2 ndi new-acc (+ count 1))
                  (reverse new-acc))))))))

;; spiral-fill: fill a grid in spiral order with a repeating color pattern
(define (spiral-fill g colors [sr 0] [sc 0])
  (define h (rows g)) (define w (cols g))
  (define path (spiral-cells h w sr sc))
  (define nc (length colors))
  (let loop ([remaining path] [i 0] [acc g])
    (if (empty? remaining) acc
      (let* ([pos (first remaining)]
             [color (list-ref colors (modulo i nc))])
        (loop (cdr remaining) (+ i 1)
              (set-cell acc (first pos) (second pos) color))))))

;; ============================================================
;; NEW PRIMITIVES — added 2026-04-12 (batch 2)
;; ============================================================

;; stamp-normalized-cells: place a normalized (r c) or (r c value) cell list
;; onto grid at target top-left (tr, tc). If color is given, overrides per-cell values.
;; Out-of-bounds placements are silently ignored.
(define (stamp-normalized-cells g cells tr tc [color #f])
  (foldl (lambda (cell acc)
    (let* ([r (+ tr (first cell))]
           [c (+ tc (second cell))]
           [v (if (not (eq? color #f))
                  color
                  (if (and (list? cell) (>= (length cell) 3))
                      (third cell)
                      (safe-at acc r c 0)))])
      (if (in-bounds? r c (rows acc) (cols acc))
          (set-cell acc r c v)
          acc)))
    g cells))

;; shift-row-cells: shift all non-bg cells in row r by dc columns.
;; Old positions become bg; shifted cells that leave the grid are dropped.
(define (shift-row-cells g r dc [bg 0])
  (define w (cols g))
  (define row-vals (for/list ([c (in-range w)]) (cell-at g r c)))
  (define new-row (make-list w bg))
  (foldl (lambda (c acc)
    (let ([v (list-ref row-vals c)]
          [nc (+ c dc)])
      (if (and (not (= v bg)) (>= nc 0) (< nc w))
          (list-set acc nc v)
          acc)))
    new-row (range 0 w))
  ;; Build the result grid
  (grid-from-fn (rows g) w
    (lambda (gr gc)
      (if (= gr r)
          (let ([v (list-ref row-vals gc)]
                [nc (+ gc dc)])
            ;; New row: shift non-bg cells
            (let ([shifted-from
                   ;; Is there a non-bg cell that shifts INTO gc?
                   (let ([src (- gc dc)])
                     (if (and (>= src 0) (< src w) (not (= (list-ref row-vals src) bg)))
                         (list-ref row-vals src)
                         bg))])
              shifted-from))
          (cell-at g gr gc)))))

;; bbox-interior-cells: interior positions of a bbox (r1 c1 r2 c2), excluding the 1-cell border.
;; Returns empty for boxes smaller than 3×3. Accepts either raw bbox or an object.
(define (bbox-interior-cells arg)
  (define bb (if (and (list? arg) (= (length arg) 4) (number? (first arg)))
                 arg  ;; raw bbox (r1 c1 r2 c2)
                 (obj-bbox arg)))  ;; object
  (define r1 (first bb)) (define c1 (second bb))
  (define r2 (third bb)) (define c2 (fourth bb))
  (if (or (< (- r2 r1) 2) (< (- c2 c1) 2))
      '()
      (positions-in-rect (+ r1 1) (+ c1 1) (- r2 1) (- c2 1))))

;; select-object-by: pick one object by scoring function.
;; mode is 'max or 'min. Tie-breaks by row-major bbox position.
;; Returns #f for empty input.
(define (select-object-by objs score-fn [mode 'max])
  (if (empty? objs) #f
    (let* ([scored (map (lambda (o) (list (score-fn o) o)) objs)]
           [cmp (if (equal? mode 'max) > <)]
           [sorted (sort scored
             (lambda (a b)
               (if (not (= (first a) (first b)))
                   (cmp (first a) (first b))
                   ;; Tie-break: row-major bbox
                   (let ([ba (obj-bbox (second a))] [bb (obj-bbox (second b))])
                     (cond
                       [(< (first ba) (first bb)) #t]
                       [(> (first ba) (first bb)) #f]
                       [else (< (second ba) (second bb))])))))])
      (second (first sorted)))))

;; fill-object-interior: fill an object's bbox interior where cells equal bg.
;; Does not overwrite non-bg interior cells (preserves the frame).
(define (fill-object-interior g obj color [bg 0])
  (define interior (bbox-interior-cells obj))
  (foldl (lambda (pos acc)
    (let ([r (first pos)] [c (second pos)])
      (if (= (cell-at acc r c) bg)
          (set-cell acc r c color)
          acc)))
    g interior))

;; straight-runs: extract maximal same-value runs along given directions.
;; pred? takes a cell value and returns #t to include. dirs is a list of (dr dc) deltas.
;; Returns list of (list cells direction) where cells is a list of (r c) and direction is (dr dc).
;; Each run has length >= 2. Deterministic order: by starting position row-major, then direction.
(define (straight-runs g pred? dirs)
  (define h (rows g)) (define w (cols g))
  (define visited (make-hash))  ;; (r c dr dc) → #t
  (define result '())
  (for* ([r (in-range h)] [c (in-range w)])
    (when (pred? (cell-at g r c))
      (for ([d (in-list dirs)])
        (let ([dr (first d)] [dc (second d)])
          (unless (hash-has-key? visited (list r c dr dc))
            ;; Trace run from (r,c) in direction (dr,dc)
            (let loop ([cr r] [cc c] [cells '()])
              (if (and (in-bounds? cr cc h w) (pred? (cell-at g cr cc)))
                  (begin
                    (hash-set! visited (list cr cc dr dc) #t)
                    (loop (+ cr dr) (+ cc dc) (cons (list cr cc) cells)))
                  ;; End of run
                  (when (>= (length cells) 2)
                    (set! result (cons (list (reverse cells) d) result))))))))))
  (reverse result))

;; apply-row-shift-cycle: apply a repeating shift pattern to nonempty rows.
;; shifts is a list of column deltas, e.g. '(-1 0 1 0).
;; Cycles through shifts for each successive nonempty row starting from start-row
;; (default: first nonempty row).
(define (apply-row-shift-cycle g shifts [bg 0] [start-row #f])
  (define h (rows g)) (define w (cols g))
  (define n (length shifts))
  ;; Find nonempty rows
  (define nonempty-rows
    (filter (lambda (r) (ormap (lambda (c) (not (= (cell-at g r c) bg))) (range 0 w)))
            (range 0 h)))
  (define first-ne (if (and start-row (>= start-row 0)) start-row
                       (if (empty? nonempty-rows) 0 (first nonempty-rows))))
  ;; Apply shifts
  (foldl (lambda (r-info acc)
    (let* ([r (first r-info)] [i (second r-info)]
           [dc (list-ref shifts (modulo i n))])
      (if (= dc 0) acc (shift-row-cells acc r dc bg))))
    g
    (filter (lambda (ri) (member (first ri) nonempty-rows))
      (map (lambda (r) (list r (- r first-ne))) (range 0 h)))))

;; cells-equal?: check if two normalized cell sets are identical shapes
(define (cells-equal? a b)
  (let ([na (sort (normalize-cells a) (lambda (x y) (if (= (first x) (first y)) (< (second x) (second y)) (< (first x) (first y)))))]
        [nb (sort (normalize-cells b) (lambda (x y) (if (= (first x) (first y)) (< (second x) (second y)) (< (first x) (first y)))))])
    (equal? na nb)))

;; ============================================================
;; (Compatibility aliases removed 2026-04-25.)
;; The previous deprecated set (get-cell, num-rows, num-cols, width,
;; height, colors-of, new-grid, flood) was confirmed unused in
;; grounded_rules.py — every apparent call was a local let-binding
;; whose name happened to match. Canonical names: cell-at, rows,
;; cols, grid-colors, empty-grid, gravity. See docs/RACKET_DSL.md.
;; ============================================================

;; ============================================================
;; High-frequency convenience helpers
;; Added based on corpus analysis: grid-colors+filter (69 rules),
;; objects+reduce (93 rules)
;; ============================================================

;; non-bg-colors: get all colors except background (0)
(define (non-bg-colors g [bg 0])
  (filter (lambda (c) (not (= c bg))) (grid-colors g)))

;; other-color: in a two-color-plus-bg grid, find the "other" color
;; given one known color. Common pattern: find fg vs marker.
(define (other-color g known [bg 0])
  (let ((others (filter (lambda (c) (and (not (= c bg)) (not (= c known))))
                  (grid-colors g))))
    (if (null? others) bg (car others))))

;; fg-color: the single foreground color (most common non-bg)
(define (fg-color g [bg 0])
  (mode g bg))

;; map-objects: apply fn to each object, accumulate into grid
;; fn takes (grid, obj) -> grid
(define (map-objects g bg fn)
  (foldl (lambda (obj acc) (fn acc obj)) g (objects g bg)))

;; filter-objects: keep only objects matching predicate
(define (filter-objects g bg pred)
  (filter pred (objects g bg)))

;; smallest-object: return the single smallest object
(define (smallest-object g [bg 0])
  (pick-min (objects g bg) obj-size))

;; ============================================================
;; New helpers from reviewer feedback (2026-04-14)
;; ============================================================

;; hole-count: count zero-connected-components inside an object's bbox
(define (hole-count obj grid)
  (let* ((r1 (obj-r1 obj)) (c1 (obj-c1 obj))
         (r2 (obj-r2 obj)) (c2 (obj-c2 obj))
         (bbox-grid (subgrid grid r1 c1 r2 c2))
         ;; Build binary grid: 1 where bbox has 0, 0 elsewhere
         (zero-grid (grid-from-fn (rows bbox-grid) (cols bbox-grid)
                      (lambda (r c) (if (= (cell-at bbox-grid r c) 0) 1 0)))))
    ;; Count connected components of 1s (the zero-regions)
    (length (objects zero-grid 0))))

;; diagonal-between: cells strictly between two diagonal points
(define (diagonal-between start end)
  (let* ((r1 (first start)) (c1 (second start))
         (r2 (first end)) (c2 (second end))
         (row-diff (abs (- r2 r1)))
         (col-diff (abs (- c2 c1))))
    (if (not (= row-diff col-diff)) '()
        (let ((row-step (if (> r2 r1) 1 -1))
              (col-step (if (> c2 c1) 1 -1)))
          (for/list ([i (in-range 1 row-diff)])
            (list (+ r1 (* i row-step))
                  (+ c1 (* i col-step))))))))

;; stamp-object: translate an object's cells to new anchor and paint
(define (stamp-object grid obj top left [color #f])
  (let ((paint-color (or color (obj-color obj)))
        (translated (map (lambda (cell)
                           (list (+ top (- (first cell) (obj-r1 obj)))
                                 (+ left (- (second cell) (obj-c1 obj)))))
                         (obj-cells obj))))
    (recolor-cells grid translated paint-color)))

;; translate-cells: shift a list of (r c) positions by (dr, dc)
(define (translate-cells cells dr dc)
  (map (lambda (cell)
         (list (+ (first cell) dr) (+ (second cell) dc)))
       cells))

;; grids-equal?: compare two grids for identical content
(define (grids-equal? g1 g2)
  (and (= (rows g1) (rows g2))
       (= (cols g1) (cols g2))
       (for*/and ([r (in-range (rows g1))]
                  [c (in-range (cols g1))])
         (= (cell-at g1 r c) (cell-at g2 r c)))))

;; grid-matches-rotation?: check if g2 matches g1 under any of 4 rotations
(define (grid-matches-rotation? g1 g2)
  (or (grids-equal? g1 g2)
      (grids-equal? g1 (rotate-cw g2))
      (grids-equal? g1 (rotate-180 g2))
      (grids-equal? g1 (rotate-ccw g2))))

;; touches-border?: does an object's bbox touch the grid edge?
(define (touches-border? obj height width)
  (or (= (obj-r1 obj) 0)
      (= (obj-c1 obj) 0)
      (= (obj-r2 obj) (- height 1))
      (= (obj-c2 obj) (- width 1))))

;; all-equal?: are all values in a list the same?
(define (all-equal? lst)
  (or (empty? lst) (andmap (lambda (v) (= v (first lst))) (rest lst))))

;; ============================================================
;; Round 7 additions: tile-consensus, pack-objects, separator helpers,
;; reachable-from-seeds, normalize-shape
;; ============================================================

;; tile-consensus: compress a repeated-tile grid to its base tile.
;; Uses full-rows/full-cols of a separator color to find tile boundaries.
;; Disagreements across copies get marked with conflict-color.
(define (tile-consensus g [conflict-color 1])
  (define sep-rows-info (full-rows g))
  (define sep-cols-info (full-cols g))
  (define sep-rows (map first sep-rows-info))
  (define sep-cols (map first sep-cols-info))
  (define tile-h (if (empty? sep-rows) (rows g) (first sep-rows)))
  (define tile-w (if (empty? sep-cols) (cols g) (first sep-cols)))
  (define row-starts (cons 0 (map (lambda (r) (+ r 1)) sep-rows)))
  (define col-starts (cons 0 (map (lambda (c) (+ c 1)) sep-cols)))
  (grid-from-fn tile-h tile-w
    (lambda (row col)
      (let ((values
              (flatmap (lambda (tr)
                        (map (lambda (tc) (cell-at g (+ tr row) (+ tc col))) col-starts))
                       row-starts)))
        (if (all-equal? values)
          (first values)
          conflict-color)))))

;; split-panels: split a grid by a separator (color or detected).
;; Returns a list of sub-grids. Works for both row and col separators.
(define (split-panels-by-row g sep-row)
  (list (subgrid g 0 0 (- sep-row 1) (- (cols g) 1))
        (subgrid g (+ sep-row 1) 0 (- (rows g) 1) (- (cols g) 1))))

(define (split-panels-by-col g sep-col)
  (list (subgrid g 0 0 (- (rows g) 1) (- sep-col 1))
        (subgrid g 0 (+ sep-col 1) (- (rows g) 1) (- (cols g) 1))))

;; split-panels-with-info: auto-detect separator, return (panels separator-info)
;; separator-info is '(row index color) or '(col index color)
(define (split-panels-with-info g)
  (let ((frow (full-rows g))
        (fcol (full-cols g)))
    (cond
      [(not (empty? frow))
       (let* ((sep (first frow))
              (sep-idx (first sep))
              (sep-color (second sep)))
         (list (split-panels-by-row g sep-idx) (list 'row sep-idx sep-color)))]
      [(not (empty? fcol))
       (let* ((sep (first fcol))
              (sep-idx (first sep))
              (sep-color (second sep)))
         (list (split-panels-by-col g sep-idx) (list 'col sep-idx sep-color)))]
      [else (list (list g) (list 'none 0 0))])))

;; pack-objects-vertical: stack a list of objects vertically in a clean canvas.
;; Each object's bbox gets placed bottom-up in left-aligned column bands.
(define (pack-objects-vertical height width objs color)
  (let loop ((acc (empty-grid height width 0))
             (remaining objs)
             (current-top height))
    (if (empty? remaining) acc
        (let* ((obj (first remaining))
               (obj-h (obj-h obj))
               (new-top (- current-top obj-h)))
          (loop (stamp-object acc obj new-top 0 color)
                (rest remaining)
                (- new-top 1))))))

;; reachable-from-seeds: multi-seed BFS with a walkable predicate.
;; seeds is a list of (r c), pred? takes (row col val) -> bool.
(define (reachable-from-seeds g seeds pred? [connectivity 4])
  (let loop ((visited (list))
             (queue seeds))
    (if (empty? queue) visited
        (let* ((current (first queue))
               (rest-queue (rest queue)))
          (if (member current visited)
            (loop visited rest-queue)
            (let* ((new-visited (cons current visited))
                   (row (first current))
                   (col (second current))
                   (deltas (if (= connectivity 8)
                             '((-1 -1) (-1 0) (-1 1) (0 -1) (0 1) (1 -1) (1 0) (1 1))
                             '((-1 0) (1 0) (0 -1) (0 1))))
                   (new-neighbors
                     (filter (lambda (n)
                               (let ((nr (first n)) (nc (second n)))
                                 (and (>= nr 0) (< nr (rows g))
                                      (>= nc 0) (< nc (cols g))
                                      (pred? nr nc (cell-at g nr nc))
                                      (not (member n new-visited))
                                      (not (member n rest-queue)))))
                             (map (lambda (d)
                                    (list (+ row (first d)) (+ col (second d))))
                                  deltas))))
              (loop new-visited (append rest-queue new-neighbors))))))))

;; normalize-shape: canonical binary shape grid of an object.
;; Crops to bbox, keeps only the object's color, recolors to 1.
(define (normalize-shape obj g)
  (let* ((bbox-grid (subgrid g (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj)))
         (kept (keep-only bbox-grid (obj-color obj)))
         (canonical (recolor kept (obj-color obj) 1)))
    (crop-to-content canonical)))

;; neighbor-count-4: count cardinal neighbors with a specific color
(define (neighbor-count-4 g r c color)
  (for/sum ([d (in-list cardinal-deltas)])
    (let ((nr (+ r (first d))) (nc (+ c (second d))))
      (if (and (>= nr 0) (< nr (rows g))
               (>= nc 0) (< nc (cols g))
               (= (cell-at g nr nc) color))
          1 0))))

;; detect-lines: full-span rows and columns as a flat list of
;;   (list 'row index color) and (list 'col index color) entries.
(define (detect-lines g)
  (append
    (map (lambda (info) (list 'row (first info) (second info))) (full-rows g))
    (map (lambda (info) (list 'col (first info) (second info))) (full-cols g))))

;; internal-separators: full-span rows/cols that are NOT on the grid border.
;; Same return shape as detect-lines, but excludes the edges.
(define (internal-separators g)
  (let ((h (rows g)) (w (cols g)))
    (filter (lambda (info)
              (let ((kind (first info)) (idx (second info)))
                (cond
                  [(eq? kind 'row) (and (> idx 0) (< idx (- h 1)))]
                  [(eq? kind 'col) (and (> idx 0) (< idx (- w 1)))]
                  [else #f])))
            (detect-lines g))))


;; ============================================================================
;; SHAPE — first-class rectangular-region descriptor.
;;
;; Rationale: many operations (crop, paint, tile, mask, …) want the same
;; argument shape: "a rectangular region of the grid." Today each operation
;; takes its own positional args; rules end up repeating r1/c1/r2/c2
;; computations everywhere. A `shape` is a tagged hasheq describing such a
;; region. Field-named hashes (not structs) so the model can edit a single
;; field for off-by-one fixes — e.g. `(hash-set s 'h 4)` to grow by one.
;;
;; A shape always exposes r, c, h, w (top-left + height + width).
;; Specific kinds carry extra fields for introspection / re-rendering.
;; ============================================================================

(define (shape? s) (and (hash? s) (hash-has-key? s 'kind)))

;; Constructors -----

(define (rect r c h w)
  ;; Explicit top-left + height + width.
  (hasheq 'kind 'rect 'r r 'c c 'h h 'w w))

(define (rect-rc r1 c1 r2 c2)
  ;; Inclusive corner-pair form (matches existing crop calling convention).
  (rect r1 c1 (+ 1 (- r2 r1)) (+ 1 (- c2 c1))))

(define (corner g cnr h w)
  ;; cnr ∈ '(tl tr bl br). Anchors the rect at the chosen corner of g.
  (let ([gh (rows g)] [gw (cols g)])
    (case cnr
      [(tl) (rect 0 0 h w)]
      [(tr) (rect 0 (- gw w) h w)]
      [(bl) (rect (- gh h) 0 h w)]
      [(br) (rect (- gh h) (- gw w) h w)]
      [else (error 'corner "bad corner: ~a (want 'tl 'tr 'bl 'br)" cnr)])))

(define (content-shape g [bg 0])
  ;; Bbox of non-bg cells. Empty grid → (rect 0 0 0 0).
  (let ([cells (filter (lambda (p) (not (= (cell-at g (first p) (second p)) bg)))
                       (grid-positions g))])
    (cond
      [(null? cells) (rect 0 0 0 0)]
      [else
       (let ([rs (map first cells)] [cs (map second cells)])
         (rect (apply min rs) (apply min cs)
               (+ 1 (- (apply max rs) (apply min rs)))
               (+ 1 (- (apply max cs) (apply min cs)))))])))

(define (color-bbox g color)
  ;; Bbox of all cells of `color`.
  (let ([cells (find-color g color)])
    (cond
      [(null? cells) (rect 0 0 0 0)]
      [else
       (let ([rs (map first cells)] [cs (map second cells)])
         (rect (apply min rs) (apply min cs)
               (+ 1 (- (apply max rs) (apply min rs)))
               (+ 1 (- (apply max cs) (apply min cs)))))])))

(define (cells-bbox cells)
  ;; Bbox of an arbitrary cell list.
  (cond
    [(null? cells) (rect 0 0 0 0)]
    [else
     (let ([rs (map first cells)] [cs (map second cells)])
       (rect (apply min rs) (apply min cs)
             (+ 1 (- (apply max rs) (apply min rs)))
             (+ 1 (- (apply max cs) (apply min cs)))))]))

(define (object-shape obj)
  ;; Shape from the bbox of an object (uses obj-bbox).
  (let ([bb (obj-bbox obj)])
    (rect-rc (first bb) (second bb) (third bb) (fourth bb))))

;; Accessors -----

(define (shape-r s) (hash-ref s 'r))
(define (shape-c s) (hash-ref s 'c))
(define (shape-h s) (hash-ref s 'h))
(define (shape-w s) (hash-ref s 'w))
(define (shape-r2 s) (- (+ (shape-r s) (shape-h s)) 1))
(define (shape-c2 s) (- (+ (shape-c s) (shape-w s)) 1))

(define (shape-cells s)
  ;; List of (r c) cells covered by the shape, row-major.
  (let ([r (shape-r s)] [c (shape-c s)]
        [h (shape-h s)] [w (shape-w s)])
    (for*/list ([dr (in-range h)] [dc (in-range w)])
      (list (+ r dr) (+ c dc)))))

(define (shape-frame s)
  ;; Outline (perimeter) cells of the shape.
  (let ([r (shape-r s)] [c (shape-c s)]
        [h (shape-h s)] [w (shape-w s)])
    (cond
      [(or (<= h 0) (<= w 0)) '()]
      [(or (= h 1) (= w 1)) (shape-cells s)]
      [else
       (append
         (for/list ([dc (in-range w)]) (list r (+ c dc)))                         ; top
         (for/list ([dc (in-range w)]) (list (+ r h -1) (+ c dc)))                ; bottom
         (for/list ([dr (in-range 1 (- h 1))]) (list (+ r dr) c))                 ; left
         (for/list ([dr (in-range 1 (- h 1))]) (list (+ r dr) (+ c w -1))))])))   ; right

(define (shape-interior s)
  ;; Cells strictly inside the shape (excludes the perimeter).
  (let ([r (shape-r s)] [c (shape-c s)]
        [h (shape-h s)] [w (shape-w s)])
    (cond
      [(or (<= h 2) (<= w 2)) '()]
      [else
       (for*/list ([dr (in-range 1 (- h 1))] [dc (in-range 1 (- w 1))])
         (list (+ r dr) (+ c dc)))])))

;; Consumers -----

(define (crop-shape g s)
  ;; Crop a grid to a shape's region.
  (subgrid g (shape-r s) (shape-c s) (shape-r2 s) (shape-c2 s)))

(define (paint-shape g s color)
  ;; Paint the shape's cells with color. Returns new grid.
  (paint-cells g (shape-cells s) color))

(define (paint-frame g s color)
  ;; Paint just the outline of the shape.
  (paint-cells g (shape-frame s) color))

(define (paint-interior g s color)
  ;; Paint just the interior of the shape.
  (paint-cells g (shape-interior s) color))


;; ============================================================================
;; Fold/iterate combinators — capture the dominant authoring patterns.
;; ============================================================================

(define (for-each-object g objs fn)
  ;; fn takes (acc-grid obj) → new grid. Used to transform g once per object.
  (foldl (lambda (obj acc) (fn acc obj)) g objs))

(define (underfill g cells color [bg 0])
  ;; Paint cells with `color`, but only where the current cell value == bg.
  (foldl (lambda (cell acc)
           (let* ([r (fst cell)] [c (snd cell)])
             (if (and (in-bounds? r c (rows acc) (cols acc))
                      (= (at acc r c) bg))
                 (set-cell acc r c color)
                 acc)))
         g cells))


;; ============================================================================
;; CORE VOCAB — high-leverage forms for the dominant authoring patterns.
;;
;; All of these target rule families that appear many times in the
;; grounded corpus. Each is meant to map cleanly onto a "big step" in
;; the 4-step pipeline framing (identify / derive / transform / compose).
;; ============================================================================

;; ----- cellmap: per-cell transform with explicit (r c v) binders -----
;; Replaces the dominant idiom:
;;   (grid-from-fn h w (lambda (r c) (let ((v (cell-at g r c))) BODY)))
;; (~700 of 900 rules use this shape).
(define-syntax-rule (cellmap g (r c v) body ...)
  (let ([__cm_g g])
    (grid-from-fn (rows __cm_g) (cols __cm_g)
      (lambda (r c)
        (let ([v (cell-at __cm_g r c)])
          body ...)))))

;; ----- casev: dispatch a cell value through a recolor table -----
;; Replaces the (cond ((= v X) Y) ((= v Z) W) (else default)) pattern.
;; (~500 rules use this shape). `table` is a dict literal {OLD NEW OLD NEW ...}.
(define (casev v table [default #f])
  (let ([d (if (eq? default #f) v default)])
    (hash-ref table v d)))

;; ----- with-shape: destructure a shape into r/c/h/w/r2/c2 -----
(define-syntax-rule (with-shape s (r c h w) body ...)
  (let ([__ws_s s])
    (let ([r (shape-r __ws_s)] [c (shape-c __ws_s)]
          [h (shape-h __ws_s)] [w (shape-w __ws_s)])
      body ...)))


;; ============================================================================
;; SELECTORS — cells-where, objects-where, objects-of-color
;; ============================================================================

(define (cells-where g pred)
  ;; Return list of (r c) where (pred g r c v) is truthy. v = cell value.
  (filter (lambda (p) (pred g (first p) (second p) (cell-at g (first p) (second p))))
          (grid-positions g)))

(define (objects-where objs pred)
  ;; Filter a list of objects by predicate.
  (filter pred objs))

(define (objects-of-color objs color)
  ;; Filter objects to those whose dominant color is `color`.
  (filter (lambda (o) (= (obj-color o) color)) objs))


;; ============================================================================
;; IDENTIFICATION primitives — common "find the unique X" patterns.
;; ============================================================================

(define (find-anchor g color)
  ;; Returns the (r c) of the unique cell of `color`, or #f if not unique.
  (let ([cells (find-color g color)])
    (cond
      [(= (length cells) 1) (first cells)]
      [else #f])))

(define (find-singletons g [bg 0])
  ;; Returns list of (color (r c)) for each color that appears exactly once.
  (let ([colors (filter (lambda (c) (not (= c bg))) (grid-colors g))])
    (filter (lambda (entry) entry)
      (map (lambda (c)
             (let ([cells (find-color g c)])
               (if (= (length cells) 1) (list c (first cells)) #f)))
           colors))))

(define (largest-solid-rect g [bg 0])
  ;; Find the largest solid (single-color) rectangle of any non-bg color.
  ;; Returns a hasheq with keys: 'color, 'shape (a rect shape), or #f if none.
  (let* ([h (rows g)] [w (cols g)]
         [best #f]
         [best-area 0])
    (for* ([r1 (in-range h)] [c1 (in-range w)])
      (let ([clr (cell-at g r1 c1)])
        (when (not (= clr bg))
          (for* ([r2 (in-range r1 h)] [c2 (in-range c1 w)])
            (let ([area (* (+ 1 (- r2 r1)) (+ 1 (- c2 c1)))])
              (when (> area best-area)
                (let ([solid (for*/and ([rr (in-range r1 (+ r2 1))]
                                         [cc (in-range c1 (+ c2 1))])
                              (= (cell-at g rr cc) clr))])
                  (when solid
                    (set! best (hasheq 'color clr 'shape (rect-rc r1 c1 r2 c2)))
                    (set! best-area area)))))))))
    best))

(define (find-divider g [bg 0])
  ;; Find the first uniform full-row or full-col (excluding bg). Returns
  ;; (list 'row r color) or (list 'col c color), or #f.
  (let* ([h (rows g)] [w (cols g)]
         [row-result
           (for/first ([r (in-range h)]
                       #:when (let ([v (cell-at g r 0)])
                                (and (not (= v bg))
                                     (for/and ([c (in-range 1 w)])
                                       (= (cell-at g r c) v)))))
             (list 'row r (cell-at g r 0)))])
    (cond
      [row-result row-result]
      [else
       (for/first ([c (in-range w)]
                   #:when (let ([v (cell-at g 0 c)])
                            (and (not (= v bg))
                                 (for/and ([r (in-range 1 h)])
                                   (= (cell-at g r c) v)))))
         (list 'col c (cell-at g 0 c)))])))


;; ============================================================================
;; STAMP primitives — capture the "find a template, paint it elsewhere" family.
;;
;; A stamp is a list of (dr dc value) triples relative to an anchor cell
;; (typically the bbox top-left).
;; ============================================================================

(define (stamp-from-cells cells g)
  ;; Extract a stamp from cells in grid g, anchored at the cell-set's
  ;; bbox top-left.
  (cond
    [(null? cells) '()]
    [else
     (let ([r0 (apply min (map first cells))]
           [c0 (apply min (map second cells))])
       (map (lambda (cell)
              (list (- (first cell) r0)
                    (- (second cell) c0)
                    (cell-at g (first cell) (second cell))))
            cells))]))

(define (stamp-from-object obj g)
  ;; Extract a stamp from an object, anchored at obj's bbox top-left.
  (stamp-from-cells (obj-cells obj) g))

(define (stamp-from-shape g s)
  ;; Extract a stamp covering the entire shape's region (full rect).
  (stamp-from-cells (shape-cells s) g))

(define (paint-stamp-at g stamp anchor)
  ;; Paint `stamp` at anchor (r c). Out-of-bounds triples are skipped.
  (let ([or (first anchor)] [oc (second anchor)])
    (paint-cells g
      (map (lambda (t) (list (+ or (first t)) (+ oc (second t)) (third t)))
           stamp))))

(define (paint-stamp-at-each g stamp positions)
  ;; Paint stamp at multiple anchor positions.
  (foldl (lambda (pos acc) (paint-stamp-at acc stamp pos)) g positions))

(define (paint-stamp-at-marker g stamp marker-color [bg 0])
  ;; "Paint stamp at key location": find each cell of `marker-color` in g,
  ;; paint the stamp anchored at the marker. The marker cell becomes the
  ;; stamp's (0,0) cell.
  (let ([positions (find-color g marker-color)])
    (paint-stamp-at-each g stamp positions)))


;; ============================================================================
;; "FIND FULL + RECOVER PARTIALS" pattern: complete-shape-by-largest.
;;
;; Finds the largest non-bg object as the "template" (full version), then
;; for each smaller object of the same color, paints the template's cells
;; at the partial's bbox top-left (completing the missing cells).
;; ============================================================================

(define (complete-shape-by-largest g [bg 0])
  ;; Conservative implementation: requires 1 "full" (largest) and N≥1
  ;; smaller objects of the same color.
  (let* ([objs (objects g bg)]
         [non-empty (filter (lambda (o) (> (obj-size o) 0)) objs)])
    (cond
      [(< (length non-empty) 2) g]
      [else
       (let* ([full (pick-max non-empty obj-size)]
              [color (obj-color full)]
              [partials (filter (lambda (o)
                                  (and (= (obj-color o) color)
                                       (not (= (obj-size o) (obj-size full)))))
                                non-empty)]
              [stamp (stamp-from-object full g)])
         (foldl (lambda (p acc)
                  (let ([anchor (list (obj-r1 p) (obj-c1 p))])
                    (paint-stamp-at acc stamp anchor)))
                g partials))])))


;; ============================================================================
;; "FIND KEY+ATTACHMENT, MATCH KEYHOLES" pattern: transport-attachments.
;;
;; Pattern: one cluster has a "key" cell of `key-color` plus other-color cells
;; "attached" to it (any non-bg, non-key cells in the same connected region
;; or within a bounding box of the key). Other clusters are bare keys
;; (just key-color cells, no attachment).
;;
;; The rule: paint the attachment relative to each bare key.
;; ============================================================================

(define (transport-attachments g key-color [bg 0])
  ;; Find all key-color cells; the cluster with the most adjacent non-bg,
  ;; non-key cells is the "full key". Its attachment is those adjacent cells.
  ;; Paint the attachment at every other key cluster's anchor.
  (let* ([key-cells (find-color g key-color)])
    (cond
      [(null? key-cells) g]
      [else
       ;; For each key cell, count "attached" cells (non-bg, non-key in 8-nbhd).
       (let* ([key-with-attached
               (map (lambda (kp)
                      (let* ([kr (first kp)] [kc (second kp)]
                             [nbrs (for*/list ([dr (in-list '(-1 0 1))]
                                                [dc (in-list '(-1 0 1))]
                                                #:when (not (and (= dr 0) (= dc 0))))
                                     (list (+ kr dr) (+ kc dc)))]
                             [attached
                              (filter (lambda (n)
                                        (and (in-bounds? (first n) (second n) (rows g) (cols g))
                                             (let ([v (cell-at g (first n) (second n))])
                                               (and (not (= v bg)) (not (= v key-color))))))
                                      nbrs)])
                        (list kp attached)))
                    key-cells)]
              [full-entry (pick-max key-with-attached
                                    (lambda (e) (length (second e))))]
              [full-key (first full-entry)]
              [attached-cells (second full-entry)])
         (cond
           [(null? attached-cells) g]  ; no attachment found
           [else
            ;; Stamp = attached cells relative to the full key
            (let ([stamp (map (lambda (a)
                                (list (- (first a) (first full-key))
                                      (- (second a) (second full-key))
                                      (cell-at g (first a) (second a))))
                              attached-cells)])
              (paint-stamp-at-each g stamp
                (filter (lambda (kp) (not (equal? kp full-key))) key-cells)))]))])))


;; ============================================================================
;; COMPLETION combinators — given a partial pattern, fill in to satisfy the
;; constraint. Common in ARC puzzles where the input is a deliberately-broken
;; symmetric / periodic grid and the task is to restore it.
;; ============================================================================

(define (complete-symmetry g axis [bg 0])
  ;; axis ∈ '(lr ud 180 diag anti). For each cell pair (a, mirror(a)),
  ;; if a is bg and mirror(a) is non-bg, copy mirror's value to a (and vice
  ;; versa). The result is a symmetric grid wherever the partial input was
  ;; consistent.
  (let* ([h (rows g)] [w (cols g)])
    (define (mirror-pos r c)
      (case axis
        [(lr) (list r (- (- w 1) c))]
        [(ud) (list (- (- h 1) r) c)]
        [(180) (list (- (- h 1) r) (- (- w 1) c))]
        [(diag) (list c r)]                           ; only valid for square
        [(anti) (list (- (- w 1) c) (- (- h 1) r))]
        [else (error 'complete-symmetry "bad axis: ~a" axis)]))
    (cellmap g (r c v)
      (let* ([m (mirror-pos r c)]
             [mr (first m)] [mc (second m)])
        (cond
          [(not (in-bounds? mr mc h w)) v]
          [(= v bg) (cell-at g mr mc)]
          [else v])))))

(define (fill-by-period g pr pc [bg 0])
  ;; Given assumed period (pr, pc), fill bg cells from any cell at the same
  ;; (r mod pr, c mod pc) phase. If multiple non-bg cells exist at the same
  ;; phase, the first found wins.
  (let* ([h (rows g)] [w (cols g)]
         [phase-table (make-hash)])
    (for* ([r (in-range h)] [c (in-range w)])
      (let ([v (cell-at g r c)])
        (when (not (= v bg))
          (let ([k (list (modulo r pr) (modulo c pc))])
            (when (not (hash-has-key? phase-table k))
              (hash-set! phase-table k v))))))
    (cellmap g (r c v)
      (cond
        [(not (= v bg)) v]
        [else (hash-ref phase-table (list (modulo r pr) (modulo c pc)) bg)]))))

(define (count-occurrences g sub)
  ;; Count how many times the sub-grid `sub` appears as a top-left-anchored
  ;; sub-block of `g`.
  (let* ([gh (rows g)] [gw (cols g)]
         [sh (rows sub)] [sw (cols sub)])
    (for*/sum ([r (in-range (+ 1 (- gh sh)))]
                [c (in-range (+ 1 (- gw sw)))]
                #:when (for*/and ([dr (in-range sh)] [dc (in-range sw)])
                         (= (cell-at g (+ r dr) (+ c dc))
                            (cell-at sub dr dc))))
      1)))


;; ============================================================================
;; Round-2 review feedback: contract fixes + build-grid + typed selectors +
;; region abstraction + shape edits + panel/line/ray primitives.
;; ============================================================================

;; --- with-shape extended to bind r2 c2 ---
(define-syntax-rule (with-shape* s (r c h w r2 c2) body ...)
  (let ([__ws_s s])
    (let ([r (shape-r __ws_s)] [c (shape-c __ws_s)]
          [h (shape-h __ws_s)] [w (shape-w __ws_s)]
          [r2 (shape-r2 __ws_s)] [c2 (shape-c2 __ws_s)])
      body ...)))

;; --- casev with proper sentinel (non-#f default fix) ---
(define __casev-sentinel (gensym 'casev-default-sentinel))
(define (casev* v table . default-args)
  ;; Drop-in replacement for casev that supports (casev v table) → default=v,
  ;; (casev v table d) → default=d (including #f, '(), or any value).
  (cond
    [(null? default-args) (hash-ref table v v)]
    [else (hash-ref table v (first default-args))]))

;; --- stamp-from-shape with :ignore-bg option ---
(define (stamp-from-shape-no-bg g s [bg 0])
  ;; Like stamp-from-shape but excludes cells whose value == bg.
  (let* ([r (shape-r s)] [c (shape-c s)]
         [h (shape-h s)] [w (shape-w s)])
    (filter (lambda (t) (not (= (third t) bg)))
      (for*/list ([dr (in-range h)] [dc (in-range w)])
        (list dr dc (cell-at g (+ r dr) (+ c dc)))))))

;; --- paint-stamp-at-marker with bg as underfill control ---
(define (paint-stamp-at-marker-under g stamp marker-color [bg 0])
  ;; Like paint-stamp-at-marker but only paints cells currently == bg
  ;; (preserves existing non-bg content). Useful when stamps shouldn't
  ;; clobber other markers.
  (let ([positions (find-color g marker-color)])
    (foldl (lambda (pos acc)
             (let ([or (first pos)] [oc (second pos)])
               (foldl (lambda (t a)
                        (let ([nr (+ or (first t))] [nc (+ oc (second t))])
                          (if (and (in-bounds? nr nc (rows a) (cols a))
                                   (= (at a nr nc) bg))
                              (set-cell a nr nc (third t))
                              a)))
                      acc stamp)))
           g positions)))

;; --- typed accessors for largest-solid-rect output ---
(define (solid-rect-shape r) (hash-ref r 'shape))
(define (solid-rect-color r) (hash-ref r 'color))


;; ============================================================================
;; build-grid — companion to cellmap for non-same-size output.
;; ============================================================================

(define-syntax-rule (build-grid h w (r c) body ...)
  ;; Construct a fresh h × w grid; r, c bound to row/col indices.
  (grid-from-fn h w (lambda (r c) body ...)))

(define-syntax-rule (build-like g (r c v) body ...)
  ;; Same size as g, with r/c/v auto-bound (alias for cellmap, kept for naming).
  (let ([__bl_g g])
    (grid-from-fn (rows __bl_g) (cols __bl_g)
      (lambda (r c)
        (let ([v (cell-at __bl_g r c)])
          body ...)))))

(define-syntax-rule (build-shape s (r c) body ...)
  ;; Build a grid of the shape's dimensions, with r/c local to the shape.
  (let ([__bs_s s])
    (grid-from-fn (shape-h __bs_s) (shape-w __bs_s)
      (lambda (r c) body ...))))


;; ============================================================================
;; Shape edits (typed, replacing raw hash-set).
;; ============================================================================

(define (shape-set-r s v) (hash-set s 'r v))
(define (shape-set-c s v) (hash-set s 'c v))
(define (shape-set-h s v) (hash-set s 'h v))
(define (shape-set-w s v) (hash-set s 'w v))

(define (shape-shift s dr dc)
  ;; Translate the shape's origin by (dr, dc).
  (rect (+ (shape-r s) dr) (+ (shape-c s) dc) (shape-h s) (shape-w s)))

(define (shape-grow s top right bottom left)
  ;; Expand each side outward by the given amount (negative shrinks).
  (rect (- (shape-r s) top)
        (- (shape-c s) left)
        (+ (shape-h s) top bottom)
        (+ (shape-w s) left right)))

(define (shape-pad s n) (shape-grow s n n n n))
(define (shape-inset s n) (shape-grow s (- n) (- n) (- n) (- n)))


;; ============================================================================
;; Region abstraction — irregular cell-sets above the rectangular shape.
;; A region is a `set` (Racket hash-set) of (r c) cells.
;; ============================================================================

(define (region-of-color g color)
  ;; All (r c) cells of `color`.
  (list->set (find-color g color)))

(define (region-of-object obj)
  ;; A region from an object's actual occupied cells.
  (list->set (obj-cells obj)))

(define (region-where g pred)
  ;; Cells where pred(g, r, c, v) is truthy. pred is a Racket function.
  (list->set
    (filter (lambda (p) (pred g (first p) (second p) (cell-at g (first p) (second p))))
            (grid-positions g))))

(define (region-bbox region)
  ;; Bounding box shape of a region.
  (cells-bbox (set->list region)))

(define (region-union a b) (set-union a b))
(define (region-intersect a b) (set-intersect a b))
(define (region-diff a b) (set-subtract a b))

(define (region-translate region dr dc)
  (for/set ([p (in-set region)])
    (list (+ (first p) dr) (+ (second p) dc))))

(define (region-normalize region)
  ;; Translate so the bbox top-left is at (0, 0).
  (let* ([cells (set->list region)])
    (cond
      [(null? cells) region]
      [else
       (let ([rs (map first cells)] [cs (map second cells)])
         (region-translate region (- (apply min rs)) (- (apply min cs))))])))

(define (paint-region g region color)
  ;; Paint all cells of region with color.
  (paint-cells g (set->list region) color))

(define (underfill-region g region color [bg 0])
  ;; Paint region cells with color only where current value == bg.
  (underfill g (set->list region) color bg))


;; ============================================================================
;; Typed cell selectors — replace lambda-only cells-where for safer/compact use.
;; Each returns a list of (r c) cells.
;; ============================================================================

(define (cells-of-color g color)
  (find-color g color))

(define (cells-bg g [bg 0])
  (filter (lambda (p) (= (cell-at g (first p) (second p)) bg))
          (grid-positions g)))

(define (cells-non-bg g [bg 0])
  (filter (lambda (p) (not (= (cell-at g (first p) (second p)) bg)))
          (grid-positions g)))

(define (cells-on-row g r)
  (for/list ([c (in-range (cols g))]) (list r c)))

(define (cells-on-col g c)
  (for/list ([r (in-range (rows g))]) (list r c)))

(define (cells-in-shape s)
  (shape-cells s))

(define (cells-on-frame s)
  (shape-frame s))

(define (cells-with-neighbor-color g color [conn 4])
  ;; Cells that have at least one neighbor of `color` (4 or 8 conn).
  (let ([nbr (if (= conn 8) neighbors-8 neighbors-4)])
    (filter (lambda (p)
              (let* ([r (first p)] [c (second p)]
                     [nbrs (nbr g r c #f)])
                (memv color nbrs)))
            (grid-positions g))))


;; ============================================================================
;; Typed object selectors — replace lambda-only objects-where for compact use.
;; ============================================================================

(define (objects-touching-border objs g)
  (let ([h (rows g)] [w (cols g)])
    (filter (lambda (o)
              (let ([bb (obj-bbox o)])
                (or (= (first bb) 0)
                    (= (second bb) 0)
                    (= (third bb) (- h 1))
                    (= (fourth bb) (- w 1)))))
            objs)))

(define (objects-not-touching-border objs g)
  (let ([on (objects-touching-border objs g)])
    (filter (lambda (o) (not (member o on))) objs)))

(define (objects-solid-rect objs)
  ;; Objects whose cells exactly fill their bbox.
  (filter (lambda (o)
            (let* ([bb (obj-bbox o)]
                   [bh (+ 1 (- (third bb) (first bb)))]
                   [bw (+ 1 (- (fourth bb) (second bb)))])
              (= (obj-size o) (* bh bw))))
          objs))

(define (objects-hollow-frame objs)
  ;; Objects that are perimeter-only (cells exactly = box outline of bbox).
  (filter (lambda (o)
            (let* ([bb (obj-bbox o)]
                   [s (rect-rc (first bb) (second bb) (third bb) (fourth bb))]
                   [frame (list->set (shape-frame s))]
                   [cells (list->set (obj-cells o))])
              (and (>= (shape-h s) 3) (>= (shape-w s) 3)
                   (set=? cells frame))))
          objs))

(define (objects-by-color objs)
  ;; Group objects by color → hash from color to list of objects.
  (let ([h (make-hasheq)])
    (for ([o (in-list objs)])
      (hash-update! h (obj-color o) (lambda (xs) (cons o xs)) '()))
    h))

(define (select-object objs criterion)
  ;; criterion ∈ '(largest smallest topmost bottommost leftmost rightmost).
  (cond
    [(null? objs) #f]
    [else
     (case criterion
       [(largest)    (pick-max objs obj-size)]
       [(smallest)   (pick-min objs obj-size)]
       [(topmost)    (pick-min objs obj-r1)]
       [(bottommost) (pick-max objs (lambda (o) (third (obj-bbox o))))]
       [(leftmost)   (pick-min objs obj-c1)]
       [(rightmost)  (pick-max objs (lambda (o) (fourth (obj-bbox o))))]
       [else (error 'select-object "bad criterion: ~a" criterion)])]))


;; ============================================================================
;; Panel / divider primitives.
;; ============================================================================

(define (divider-rows g [bg 0])
  ;; Rows whose cells are all the same color != bg.
  (filter (lambda (r)
            (let ([v (cell-at g r 0)])
              (and (not (= v bg))
                   (for/and ([c (in-range 1 (cols g))])
                     (= (cell-at g r c) v)))))
          (range 0 (rows g))))

(define (divider-cols g [bg 0])
  (filter (lambda (c)
            (let ([v (cell-at g 0 c)])
              (and (not (= v bg))
                   (for/and ([r (in-range 1 (rows g))])
                     (= (cell-at g r c) v)))))
          (range 0 (cols g))))

(define (split-by-dividers g [bg 0])
  ;; Split g into rectangular panels separated by uniform full rows/cols.
  ;; Returns a 2D list of subgrids: out[i][j] = panel at row-band i, col-band j.
  (let* ([drs (divider-rows g bg)]
         [dcs (divider-cols g bg)]
         [h (rows g)] [w (cols g)]
         [row-bands
           (let loop ([prev -1] [rest drs] [acc '()])
             (cond
               [(null? rest) (reverse (if (< (+ prev 1) h)
                                           (cons (list (+ prev 1) (- h 1)) acc)
                                           acc))]
               [else (loop (car rest) (cdr rest)
                            (if (< (+ prev 1) (car rest))
                                (cons (list (+ prev 1) (- (car rest) 1)) acc)
                                acc))]))]
         [col-bands
           (let loop ([prev -1] [rest dcs] [acc '()])
             (cond
               [(null? rest) (reverse (if (< (+ prev 1) w)
                                           (cons (list (+ prev 1) (- w 1)) acc)
                                           acc))]
               [else (loop (car rest) (cdr rest)
                            (if (< (+ prev 1) (car rest))
                                (cons (list (+ prev 1) (- (car rest) 1)) acc)
                                acc))]))])
    (for/list ([rb (in-list row-bands)])
      (for/list ([cb (in-list col-bands)])
        (subgrid g (first rb) (first cb) (second rb) (second cb))))))

(define (panel-at panels i j)
  (list-ref (list-ref panels i) j))

(define (panel-map panels fn)
  ;; Apply fn to each panel. fn takes (panel i j) → new panel.
  (for/list ([row (in-list panels)] [i (in-naturals)])
    (for/list ([p (in-list row)] [j (in-naturals)])
      (fn p i j))))


;; ============================================================================
;; Line / ray / connect primitives.
;; ============================================================================

(define (line-points p1 p2)
  ;; Bresenham line cells from p1 to p2 as point pairs.
  ;; Wraps the existing positional `line-cells` with a point-pair API.
  (line-cells (first p1) (second p1) (first p2) (second p2)))

(define (paint-line g p1 p2 color)
  (paint-cells g (line-points p1 p2) color))

(define (ray-cells g start dir #:until [stop-pred (lambda (g r c v) #f)])
  ;; Cells from start stepping by dir; halts when stop-pred returns truthy
  ;; OR cell goes out of bounds. Includes start; excludes the stopping cell.
  (let* ([dr (first dir)] [dc (second dir)] [h (rows g)] [w (cols g)])
    (let loop ([r (first start)] [c (second start)] [acc '()])
      (cond
        [(not (in-bounds? r c h w)) (reverse acc)]
        [(stop-pred g r c (cell-at g r c)) (reverse acc)]
        [else (loop (+ r dr) (+ c dc) (cons (list r c) acc))]))))

(define (paint-ray g start dir color #:until [stop-pred (lambda (g r c v) #f)])
  (paint-cells g (ray-cells g start dir #:until stop-pred) color))

(define (connect-points g points color)
  ;; Pairwise: connect every two consecutive points with a line.
  (cond
    [(< (length points) 2) g]
    [else
     (foldl (lambda (pair acc)
              (paint-line acc (first pair) (second pair) color))
            g
            (for/list ([i (in-range (- (length points) 1))])
              (list (list-ref points i) (list-ref points (+ i 1)))))]))

(define (connect-pair-cells g p1 p2 color)
  ;; Convenience: paint a Bresenham line between two point pairs.
  (paint-line g p1 p2 color))

(define (connect-same-color-pairs g [bg 0])
  ;; For each non-bg color with exactly 2 cells, draw a line between them.
  (let ([colors (filter (lambda (c) (not (= c bg))) (grid-colors g))])
    (foldl (lambda (color acc)
             (let ([cells (find-color acc color)])
               (cond
                 [(= (length cells) 2)
                  (paint-line acc (first cells) (second cells) color)]
                 [else acc])))
           g colors)))


;; ============================================================================
;; Hole / frame predicates and operations.
;; ============================================================================

(define (hollow-frame? obj)
  ;; Object's cells exactly match its bbox perimeter.
  (let* ([bb (obj-bbox obj)]
         [s (rect-rc (first bb) (second bb) (third bb) (fourth bb))]
         [frame (list->set (shape-frame s))]
         [cells (list->set (obj-cells obj))])
    (and (>= (shape-h s) 3) (>= (shape-w s) 3)
         (set=? cells frame))))

(define (solid-rect? obj)
  ;; Object's cells exactly fill its bbox.
  (let* ([bb (obj-bbox obj)]
         [bh (+ 1 (- (third bb) (first bb)))]
         [bw (+ 1 (- (fourth bb) (second bb)))])
    (= (obj-size obj) (* bh bw))))

(define (holes-of-object g obj [bg 0])
  ;; Cells inside the object's bbox that are bg-colored.
  (let* ([bb (obj-bbox obj)]
         [r1 (first bb)] [c1 (second bb)]
         [r2 (third bb)] [c2 (fourth bb)])
    (filter (lambda (p)
              (= (cell-at g (first p) (second p)) bg))
            (for*/list ([r (in-range r1 (+ r2 1))]
                        [c (in-range c1 (+ c2 1))])
              (list r c)))))

(define (fill-holes g obj color [bg 0])
  ;; Paint the object's holes with `color`.
  (paint-cells g (holes-of-object g obj bg) color))


;; ============================================================================
;; Dihedral / transform primitives for stamp matching.
;; ============================================================================

(define (transform-cells cells op)
  ;; op ∈ '(identity rot90 rot180 rot270 flip-lr flip-ud transpose anti-trans).
  ;; Returns transformed (and re-normalized) cell list.
  (let ([transformed
         (case op
           [(identity)   cells]
           [(rot90)      (map (lambda (p) (list (second p) (- 0 (first p)))) cells)]
           [(rot180)     (map (lambda (p) (list (- 0 (first p)) (- 0 (second p)))) cells)]
           [(rot270)     (map (lambda (p) (list (- 0 (second p)) (first p))) cells)]
           [(flip-lr)    (map (lambda (p) (list (first p) (- 0 (second p)))) cells)]
           [(flip-ud)    (map (lambda (p) (list (- 0 (first p)) (second p))) cells)]
           [(transpose)  (map (lambda (p) (list (second p) (first p))) cells)]
           [(anti-trans) (map (lambda (p) (list (- 0 (second p)) (- 0 (first p)))) cells)]
           [else (error 'transform-cells "bad op: ~a" op)])])
    (let ([rs (map first transformed)] [cs (map second transformed)])
      (cond
        [(null? rs) '()]
        [else
         (let ([rmin (apply min rs)] [cmin (apply min cs)])
           (map (lambda (p) (list (- (first p) rmin) (- (second p) cmin)))
                transformed))]))))

(define dihedral-ops
  '(identity rot90 rot180 rot270 flip-lr flip-ud transpose anti-trans))


;; ============================================================================
;; Local-window rewrite primitive — for pattern-table p95+ rules.
;; ============================================================================

(define (window-rewrite g radius table [default-mode 'same] [pad-value -1])
  ;; For each cell, compute a local-window signature (cells in [-radius, radius]
  ;; around the cell) as a tuple; look up in `table`. If found, output the
  ;; mapped value; else default-mode = 'same → keep current cell, or any int.
  (let* ([h (rows g)] [w (cols g)])
    (cellmap g (r c v)
      (let ([sig
              (for*/list ([dr (in-range (- radius) (+ radius 1))]
                          [dc (in-range (- radius) (+ radius 1))])
                (let ([nr (+ r dr)] [nc (+ c dc)])
                  (if (in-bounds? nr nc h w)
                      (cell-at g nr nc)
                      pad-value)))])
        (let ([m (hash-ref table sig (if (eq? default-mode 'same) v default-mode))])
          m)))))

;; ============================================================================
;; OBJECT-LEVEL paint primitives — collapse the dominant "for each object,
;; paint its cells with a computed color" idiom (~30 corpus rules).
;; ============================================================================

(define (paint-objects-by g objs color-fn)
  ;; For each obj in objs, paint obj's cells in g with (color-fn obj).
  ;; If color-fn returns #f, leave the object untouched — this lets the
  ;; "conditional skip" idiom (if PRED acc (recolor-cells …)) collapse to
  ;; (paint-objects-by g objs (lambda (obj) (if PRED COLOR #f))).
  (foldl (lambda (obj acc)
           (let ([c (color-fn obj)])
             (if (eq? c #f)
                 acc
                 (recolor-cells acc (obj-cells obj) c))))
         g objs))

(define (paint-objects g objs color)
  ;; Constant-color variant: paint every object's cells with the same color.
  (paint-objects-by g objs (lambda (_) color)))

;; min-of / max-of: minimum/maximum of (map fn lst). Replaces the
;; (min-list (map FN LST)) idiom (286 corpus occurrences for min,
;; 226 for max). Returns the EXTREMAL VALUE — not the element.
(define (min-of fn lst) (apply min (map fn lst)))
(define (max-of fn lst) (apply max (map fn lst)))

;; with-bbox: destructure (obj-bbox obj) into r1/c1/r2/c2 binders.
;; The (let ((bb (obj-bbox o)) (r1 (first bb)) (c1 (second bb)) ...)) pattern
;; appears in ~30 corpus rules — this macro takes that 5-line preamble down
;; to one line.
(define-syntax-rule (with-bbox obj (r1 c1 r2 c2) body ...)
  (let ([__wb_o obj])
    (let ([r1 (obj-r1 __wb_o)] [c1 (obj-c1 __wb_o)]
          [r2 (obj-r2 __wb_o)] [c2 (obj-c2 __wb_o)])
      body ...)))

;; ============================================================================
;; Reverse-genetics object genes — concise executable targets in two dialects.
;;
;; The unprefixed names are ordinary prelude vocabulary and the rg-* names are
;; compatibility aliases. Both spellings have exactly the same semantics and
;; normalize to the same typed gene in qwen9b/reverse_genetics.py. Keeping each
;; sampled gene as one short call makes synthesis supervision identify the gene
;; itself without walling the learned name off from general ARC synthesis.
;; ============================================================================

(define (keep-largest g)
  (let ([obj (largest-object g)])
    (if obj
        (paint-cells
          (grid-from-fn (rows g) (cols g) (lambda (r c) 0))
          (obj-cells obj) (obj-color obj))
        g)))

(define (remove-smallest g)
  (let ([obj (smallest-object g)])
    (if obj (object-erase g obj) g)))

(define (recolor-largest g color)
  (let ([obj (largest-object g)])
    (if obj (paint-cells g (obj-cells obj) color) g)))

(define (translate-largest g dr dc)
  (let ([obj (largest-object g)])
    (if obj (object-translate g obj dr dc) g)))

(define (move-largest g direction)
  (let ([obj (largest-object g)])
    (if obj (move-to-wall g (obj-cells obj) direction) g)))

(define (move-largest-up g) (move-largest g 'up))
(define (move-largest-down g) (move-largest g 'down))
(define (move-largest-left g) (move-largest g 'left))
(define (move-largest-right g) (move-largest g 'right))

(define (largest-bbox-cells obj outline-only?)
  (let* ([bb (obj-bbox obj)]
         [cells (positions-in-rect
                  (first bb) (second bb) (third bb) (fourth bb))])
    (if outline-only?
        (filter (lambda (p)
                  (or (= (first p) (first bb))
                      (= (first p) (third bb))
                      (= (second p) (second bb))
                      (= (second p) (fourth bb))))
                cells)
        cells)))

(define (fill-largest-bbox g color)
  (let ([obj (largest-object g)])
    (if obj (paint-cells g (largest-bbox-cells obj #f) color) g)))

(define (outline-largest-bbox g color)
  (let ([obj (largest-object g)])
    (if obj (paint-cells g (largest-bbox-cells obj #t) color) g)))

;; Compatibility aliases for v1/v2 rows already present in durable ledgers.
(define (rg-extract-largest g) (extract-largest g))
(define (rg-keep-largest g) (keep-largest g))
(define (rg-remove-smallest g) (remove-smallest g))
(define (rg-recolor-largest g color) (recolor-largest g color))
(define (rg-translate-largest g dr dc) (translate-largest g dr dc))
(define (rg-move-largest g direction) (move-largest g direction))
(define (rg-move-largest-up g) (move-largest-up g))
(define (rg-move-largest-down g) (move-largest-down g))
(define (rg-move-largest-left g) (move-largest-left g))
(define (rg-move-largest-right g) (move-largest-right g))
(define (rg-fill-enclosed g color) (fill-enclosed g color 0))
(define (rg-fill-largest-bbox g color) (fill-largest-bbox g color))
(define (rg-outline-largest-bbox g color) (outline-largest-bbox g color))
