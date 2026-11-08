# 04 · Idiom cookbook

Named, reusable multi-line patterns. Each appears in many landed rules —
recognize the task shape, reach for the idiom. All snippets are in final
house form and can be pasted into a rule body.

---

## mask + objects — components under ANY definition

`objects` only finds same-color components. To get components of an
arbitrary cell set (multicolor blobs, "everything that isn't a wall",
custom predicates), paint a 0/1 mask and run `objects` on it:

```scheme
;; 4-connected components of all nonzero cells (multicolor, 4-conn):
(define blobs
  (map obj-cells
       (objects (cellmap g (r c v) (if (zero? v) 0 1)) 0)))

;; rooms = components of non-wall cells:
(define rooms
  (objects (grid-from-fn h w (lambda (r c)
                               (if (wall? (at g r c)) 0 1)))
           0))

;; components of an explicit cell list:
(define pieces
  (map obj-cells (objects (paint-cells (empty-grid h w 0) cells 1) 0)))
```

Use `objects-8` on the mask for 8-connectivity. This replaces every
hand-written BFS over "cells like X".

---

## frame? — the hollow-rectangle detector

```scheme
(define (frame? o)  ;; hollow rectangle outline, at least 3x3
  (and (>= (obj-h o) 3) (>= (obj-w o) 3)
       (= (obj-size o) (- (* 2 (+ (obj-h o) (obj-w o))) 4))
       (all? (lambda (p) (or (= (first p) (obj-r1 o))
                             (= (first p) (obj-r2 o))
                             (= (second p) (obj-c1 o))
                             (= (second p) (obj-c2 o))))
             (obj-cells o))))
```

Size equals perimeter + every cell on the bbox border ⟺ a complete hollow
outline. Add `(= (obj-color o) 5)` etc. for color-specific frames. The rim
cells are then just `(obj-cells frame)`; the interior crop is
`(subgrid g (+ r1 1) (+ c1 1) (- r2 1) (- c2 1))`.

⚠ Some legacy rules use a brute-force scan over all rects with a uniform
border. That variant also matches **solid** rectangles and rects embedded
in larger shapes — it is NOT interchangeable with `frame?`. When
beautifying, verify on generated inputs before swapping.

---

## rim — border positions of a box

```scheme
(define (rim r0 c0 r1 c1)
  (remove-duplicates
   (append (for/list ((c (in-range c0 (+ c1 1)))) (list r0 c))
           (for/list ((c (in-range c0 (+ c1 1)))) (list r1 c))
           (for/list ((r (in-range r0 (+ r1 1)))) (list r c0))
           (for/list ((r (in-range r0 (+ r1 1)))) (list r c1)))))
```
(`remove-duplicates`, NOT `unique` — these are cell lists.)
Equivalent filter form: `(filter on-border? (positions-in-rect ...))`.

---

## mask-of / shape stamping

Render an object's shape as a standalone grid, or stamp it elsewhere:

```scheme
(define (norm-cells obj)
  (map (lambda (p) (list (- (first p) (obj-r1 obj))
                         (- (second p) (obj-c1 obj))))
       (obj-cells obj)))

(define (mask-of obj color)          ;; the shape on its own canvas
  (paint-cells (empty-grid (obj-h obj) (obj-w obj) 0)
               (norm-cells obj) color))

;; stamp a pattern grid onto out at (top,left), skipping 0s, clipped:
(define (stamp out pat top left)
  (for*/fold ((acc out)) ((r (range 0 (rows pat)))
                          (c (range 0 (cols pat))))
    (let ((v (at pat r c)))
      (if (and (> v 0) (in-bounds? (+ top r) (+ left c) h w))
          (set-cell acc (+ top r) (+ left c) v)
          acc))))

;; centered placement inside a frame's interior:
(define top (+ (obj-r1 fr) 1 (quotient (- (obj-h fr) 2 (rows pat)) 2)))
(define left (+ (obj-c1 fr) 1 (quotient (- (obj-w fr) 2 (cols pat)) 2)))
```

---

## transpose / flip projection — collapse mirrored branches

When a rule has 2 or 4 branches that are exact mirror images (open-side
left/right/top/bottom, horizontal/vertical bar...), implement ONE
orientation and project:

```scheme
(define (solve gg) ...)          ;; handles the canonical orientation only

(cond ((facing-left? g)  (solve g))
      ((facing-right? g) (flip-lr (solve (flip-lr g))))
      ((facing-up? g)    (transpose (solve (transpose g))))
      (else              (transpose (flip-lr (solve (flip-lr (transpose g)))))))
```

Inverses: `flip-lr`/`flip-ud`/`transpose`/`rotate-180` are their own
inverses; `(flip-lr (transpose ·))` inverts as `(transpose (flip-lr ·))`.

⚠ Verify the branches really ARE mirrors before collapsing — legacy rules
sometimes encode deliberately asymmetric behavior per side. Cell-check each
branch's formulas under the mapping; when in doubt, keep the branches.

---

## the dihedral spin table

For per-cell control over the 8 orientations (when `all-transforms` isn't
enough because you must transform *other* data by the same index):

```scheme
(define (spin p idx)  ;; the 8 dihedral images of a cell
  (let ((r (first p)) (c (second p)))
    (cond ((zero? idx) (list r c))
          ((= idx 1) (list c (- r)))
          ((= idx 2) (list (- r) (- c)))
          ((= idx 3) (list (- c) r))
          ((= idx 4) (list r (- c)))
          ((= idx 5) (list (- c) (- r)))
          ((= idx 6) (list (- r) c))
          (else (list c r)))))
;; normalized variant set of a shape:
(define (dihedral cells)
  (remove-duplicates
   (for/list ((t (in-range 8)))
     (let* ((raw (map (lambda (p) (spin p t)) cells))
            (mr (min-of first raw)) (mc (min-of second raw)))
       (sort (map (lambda (p) (list (- (first p) mr) (- (second p) mc)))
                  raw)
             cell<)))))
```

For whole grids the table is `identity / rotate-cw / rotate-180 /
rotate-ccw / flip-lr / flip-ud / transpose / (rotate-180 (transpose ·))`.

---

## merge-to-fixpoint — group things by a pairwise relation

```scheme
(define (merge-pass gs)              ;; merge FIRST mergeable pair
  (if (null? gs)
      (list #f (list))
      (let ((partner (find-first (lambda (o) (related? (first gs) o))
                                 (rest gs))))
        (if partner
            (list #t (cons (append (first gs) partner)
                           (filter (lambda (o) (not (equal? o partner)))
                                   (rest gs))))
            (let ((sub (merge-pass (rest gs))))
              (list (first sub) (cons (first gs) (second sub))))))))
(define groups
  (let loop ((gs seed-groups))
    (let ((p (merge-pass gs)))
      (if (first p) (loop (second p)) (second p)))))
```

Used for gap-bridged clusters, satellite-dot absorption, etc. Replaces
hash-based union-find; keeps earliest-first ordering.

---

## state-threading folds

Two accumulators (e.g. an output grid plus a "used" set):

```scheme
;; as a 2-element list:
(first
 (for/fold ((st (list (empty-grid h w 0) (list)))) ((x xs))
   (if (blocked? x (second st))
       st
       (list (paint (first st) x)
             (cons (claim x) (second st))))))

;; or multi-accumulator for/fold with values:
(for/fold ((out g) (used (list)) #:result out) ((x xs))
  (if (member? (key x) used)
      (values out used)
      (values (paint out x) (cons (key x) used))))
```

---

## walks and rays

```scheme
;; ride a direction until a predicate fails; return the last good cell
(define (walk r c dr dc)
  (if (inside? (+ r dr) (+ c dc))
      (walk (+ r dr) (+ c dc) dr dc)
      (list r c)))

;; collect a ray's cells, stopping at a blocker (exclusive)
(define (ray from to step pos-of)
  (let loop ((x from) (acc (list)))
    (cond ((if (> step 0) (>= x to) (<= x to)) (reverse acc))
          ((blocked? (pos-of x)) (reverse acc))
          (else (loop (+ x step) (cons (pos-of x) acc))))))
;; horizontal use: (ray (+ left 1) right 1 (lambda (c) (list row c)))
```

---

## gravity / settle — whole-object fall with collision

```scheme
(define (drop state shape from step)  ;; state = (out occupancy-mask)
  (let* ((cells (obj-cells shape))
         (r1 (obj-r1 shape))
         (fits? (lambda (t)
                  (all? (lambda (p) (zero? (at (second state)
                                               (+ t (- (first p) r1))
                                               (second p))))
                        cells))))
    (let loop ((t from))
      (cond ((or (< t 0) (> t (- h (obj-h shape)))) state)
            ((fits? t)
             (let ((placed (map (lambda (p) (list (+ t (- (first p) r1))
                                                  (second p)))
                                cells)))
               (list (paint-cells (first state) placed (obj-color shape))
                     (paint-cells (second state) placed 1))))
            (else (loop (+ t step)))))))
```

An occupancy **mask grid** gives O(1) collision checks — never a `member`
scan over placed cells for physics.

---

## fixpoint erosion / pruning

```scheme
(define clean  ;; strip weakly-attached cells (degree <= 1) to fixpoint
  (let strip ((mask start-mask))
    (let ((weak (filter (lambda (p) (<= (nb mask (first p) (second p)) 1))
                        (find-color mask 1))))
      (if (null? weak) mask (strip (erase-cells mask weak 0))))))
```

---

## per-band lattices (separator grids)

```scheme
(define sep-rows
  (filter (lambda (r) (and (> (at g r 0) 0) (row-uniform? g r))) (range 0 h)))
(define (spans bounds)               ;; bands between separators
  (filter (lambda (p) (<= (first p) (second p)))
          (map (lambda (i) (list (+ 1 (nth bounds i))
                                 (- (nth bounds (+ i 1)) 1)))
               (range 0 (- (length bounds) 1)))))
(define row-spans (spans (append (list -1) sep-rows (list h))))
;; macro value of a band intersection = modal nonzero color:
(define macro
  (build-grid (length row-spans) (length col-spans) (i j)
    (let ((vals (for*/list ((r (span row-spans i)) (c (span col-spans j))
                            #:when (> (at g r c) 0))
                  (at g r c))))
      (if (empty? vals) 0 (mode-list vals)))))
```

---

## first-appearance color order (deterministic tie-breaks)

```scheme
(define present  ;; non-bg colors in row-major first-appearance order
  (filter (lambda (v) (not (= v bg)))
          (remove-duplicates
           (map (lambda (p) (at g (first p) (second p)))
                (grid-positions g)))))
(define main (pick-max present (lambda (c) (length (find-color g c)))))
```
