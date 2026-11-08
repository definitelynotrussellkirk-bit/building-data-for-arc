# 06 · Worked examples — one-shot exemplars

Real, verified rules from the corpus, each preceded by the task description
you would have been given. Use them to calibrate scope, structure, naming,
and comment style. Every one passes all of its task's train and test pairs.

---

## Example 0 — trivial compositional rule

**Task:** every cyan(8) cell becomes orange(7), and every blue(1) cell is
erased to background.

```scheme
(rule! (remove-color (recolor-map g (hash 8 7)) 1))
```

When a rule is a chain of whole-grid primitives, write it as a direct body
expression (`g` is in scope) — no lambda scaffolding needed. (The REPL also
offers curried `pipe` forms; the direct form above is what runs everywhere.)

---

## Example 1 — orientation projection (small)

**Task:** each input has one yellow(4) shape and one magenta(6) bar
(horizontal or vertical). The output keeps only yellow: the shape plus its
mirror image, reflected across the shape's own bounding-box edge on the
side AWAY from the bar — unless that reflection would leave the grid, in
which case it reflects to the near side instead. The bar disappears.

```scheme
(rule!
 ;; A yellow(4) shape and a magenta(6) bar. Mirror the shape across its
 ;; own bbox edge on the side AWAY from the bar (falling back to the
 ;; near side when the reflection would leave the grid); the bar
 ;; disappears. A vertical bar mirrors horizontally — handled by
 ;; transposing in and out.
 (lambda (g)
   (let ()
     (define (solve gg)  ;; horizontal bar: mirror across a row edge
       (let* ((yellow (find-color gg 4))
              (yb (bbox-of-cells yellow))
              (ry1 (first yb))
              (ry2 (third yb))
              (six-below (> (first (bbox-of-cells (find-color gg 6)))
                            ry2))
              (up (lambda (r) (- (- (* 2 ry1) 1) r)))
              (down (lambda (r) (- (+ (* 2 ry2) 1) r)))
              (fits? (lambda (mirror)
                       (all? (lambda (p)
                               (let ((nr (mirror (first p))))
                                 (and (>= nr 0) (< nr (rows gg)))))
                             yellow)))
              (mirror (cond ((and six-below (fits? up)) up)
                            (six-below down)
                            ((fits? down) down)
                            (else up))))
         (for/fold ((out (cellmap gg (r c v) (if (= 4 v) 4 0))))
                   ((p yellow))
           (let ((nr (mirror (first p))))
             (if (and (>= nr 0) (< nr (rows gg)))
                 (set-cell out nr (second p) 4)
                 out)))))
     (define sb (bbox-of-cells (find-color g 6)))
     (if (> (- (fourth sb) (second sb)) (- (third sb) (first sb)))
         (solve g)
         (transpose (solve (transpose g)))))))
```

What to notice: ONE `solve` for the horizontal-bar case; the vertical case
is `(transpose (solve (transpose g)))`. Reflections are lambdas (`up`,
`down`) so the fallback `cond` reads like the spec.

---

## Example 2 — frames, keys, and staged rebuilding (medium)

**Task:** gray(5) rectangular frames sit on the grid; just above each
frame's top edge, at its middle column, is a KEY cell of some color k.
Loose objects are scattered around. On a blank canvas, redraw the frames
and keys; inside each frame, center the loose object that has exactly k−1
enclosed holes (largest object on ties).

```scheme
(rule!
 ;; Each gray(5) rectangular frame carries a KEY cell just above its top
 ;; edge at the middle column: key color k selects the loose object with
 ;; exactly k-1 enclosed holes (largest on ties). Redraw frames + keys
 ;; on a blank canvas and center each frame's selected object inside it.
 (lambda (g)
   (let ()
     (define (rim r0 c0 r1 c1)
       (remove-duplicates (append (for/list ((c (in-range c0 (+ c1 1)))) (list r0 c))
                       (for/list ((c (in-range c0 (+ c1 1)))) (list r1 c))
                       (for/list ((r (in-range r0 (+ r1 1)))) (list r c0))
                       (for/list ((r (in-range r0 (+ r1 1)))) (list r c1)))))
     (define (frame? o)
       ;; every cell on its bbox border, and the whole border is gray
       (and (= (obj-color o) 5)
            (all? (lambda (p) (or (= (first p) (obj-r1 o))
                                  (= (first p) (obj-r2 o))
                                  (= (second p) (obj-c1 o))
                                  (= (second p) (obj-c2 o))))
                  (obj-cells o))
            (all? (lambda (p) (= (at g (first p) (second p)) 5))
                  (rim (obj-r1 o) (obj-c1 o) (obj-r2 o) (obj-c2 o)))))
     (define frames
       (sort (filter frame? (objects g 0))
             (lambda (a b)
               (let ((ka (list (obj-r1 a) (obj-r2 a) (obj-c1 a) (obj-c2 a)))
                     (kb (list (obj-r1 b) (obj-r2 b) (obj-c1 b) (obj-c2 b))))
                 (let loop ((xs ka) (ys kb))
                   (cond ((empty? xs) #f)
                         ((< (first xs) (first ys)) #t)
                         ((> (first xs) (first ys)) #f)
                         (else (loop (rest xs) (rest ys)))))))))
     (define (key-pos f)
       (list (- (obj-r1 f) 1) (quotient (+ (obj-c1 f) (obj-c2 f)) 2)))
     (define scene  ;; g with every frame border and key cell erased
       (for/fold ((out g)) ((f (in-list frames)))
         (let ((kp (key-pos f))
               (base (erase-cells out (rim (obj-r1 f) (obj-c1 f)
                                           (obj-r2 f) (obj-c2 f))
                                  0)))
           (if (in-bounds? (first kp) (second kp) h w)
               (set-cell base (first kp) (second kp) 0)
               base))))
     (define objs (objects scene 0))
     (define (floor-half n)  ;; floor division by 2 (negative-safe)
       (if (< n 0) (- (quotient (+ (- n) 1) 2)) (quotient n 2)))
     (define (crop-of obj)
       (paint-cells (empty-grid (obj-h obj) (obj-w obj) 0)
                    (map (lambda (p) (list (- (first p) (obj-r1 obj))
                                           (- (second p) (obj-c1 obj))))
                         (obj-cells obj))
                    (obj-color obj)))
     (define (paste-centered out crop r0 c0 r1 c1)
       (let ((top (+ r0 (floor-half (- (+ 1 (- r1 r0)) (rows crop)))))
             (left (+ c0 (floor-half (- (+ 1 (- c1 c0)) (cols crop))))))
         (for*/fold ((acc out)) ((r (in-range (rows crop)))
                                 (c (in-range (cols crop))))
           (let ((v (at crop r c)))
             (if (and (> v 0) (in-bounds? (+ top r) (+ left c) h w))
                 (set-cell acc (+ top r) (+ left c) v)
                 acc)))))
     (for/fold ((out (for/fold ((acc (empty-grid h w 0)))
                               ((f (in-list frames)))
                       (paint-cells acc (rim (obj-r1 f) (obj-c1 f)
                                             (obj-r2 f) (obj-c2 f))
                                    5))))
               ((f (in-list frames)))
       (let* ((kp (key-pos f))
              (key-ok (in-bounds? (first kp) (second kp) h w))
              (key (if key-ok (at g (first kp) (second kp)) 0))
              (cands (filter (lambda (o)
                               (= (topo-count-holes scene o 0) (- key 1)))
                             objs))
              (with-key (if key-ok
                            (set-cell out (first kp) (second kp) key)
                            out)))
         (if (empty? cands)
             with-key
             (paste-centered with-key
                             (crop-of (first (sort cands
                                                   (lambda (a b)
                                                     (> (obj-size a)
                                                        (obj-size b))))))
                             (+ (obj-r1 f) 1) (+ (obj-c1 f) 1)
                             (- (obj-r2 f) 1) (- (obj-c2 f) 1))))))))
```

What to notice: `rim` built once and reused for detect/erase/redraw;
`scene` = the grid with scaffolding removed, computed once; every paint is
a fold; `floor-half` documents its one quirk in a comment.

---

## Example 3 — physics inside containers (medium)

**Task:** gray(5) rectangular frames each contain loose multicolor objects.
Inside every frame, each object falls straight down as a rigid whole
(objects with the lowest bottom edge settle first) until it rests on the
frame floor or another object. Everything outside frames is unchanged.

```scheme
(rule!
 ;; Gray(5) rectangular frames each hold loose multicolor objects.
 ;; Inside every frame, each 4-connected nonzero component falls
 ;; straight down as a WHOLE object (deepest bottom edge settles
 ;; first). Cells outside the frames pass through unchanged.
 (lambda (g)
   (let ()
     (define (frame? o)
       ;; hollow rectangle outline, at least 3x3
       (and (>= (obj-h o) 3) (>= (obj-w o) 3)
            (= (obj-size o) (- (* 2 (+ (obj-h o) (obj-w o))) 4))
            (all? (lambda (p) (or (= (first p) (obj-r1 o))
                                  (= (first p) (obj-r2 o))
                                  (= (second p) (obj-c1 o))
                                  (= (second p) (obj-c2 o))))
                  (obj-cells o))))
     (define (settle sub)
       ;; drop whole nonzero components onto an empty canvas
       (let ((comps
              (sort (map obj-cells
                         (objects (grid-from-fn (rows sub) (cols sub)
                                                (lambda (r c)
                                                  (if (= (at sub r c) 0) 0 1)))
                                  0))
                    (lambda (a b)
                      (let ((ba (bbox-of-cells a)) (bb (bbox-of-cells b)))
                        (or (> (third ba) (third bb))
                            (and (= (third ba) (third bb))
                                 (or (< (first ba) (first bb))
                                     (and (= (first ba) (first bb))
                                          (< (second ba) (second bb)))))))))))
         (for/fold ((out (empty-grid (rows sub) (cols sub) 0)))
                   ((comp (in-list comps)))
           (let ((shift (let loop ((s 0))
                          (if (all? (lambda (p)
                                      (and (< (+ (first p) s 1) (rows sub))
                                           (= (at out (+ (first p) s 1)
                                                      (second p))
                                              0)))
                                    comp)
                              (loop (+ s 1))
                              s))))
             (for/fold ((acc out)) ((p (in-list comp)))
               (set-cell acc (+ (first p) shift) (second p)
                         (at sub (first p) (second p))))))))
     (define frames
       (sort (filter (lambda (o) (and (= (obj-color o) 5) (frame? o)))
                     (objects g 0))
             (lambda (a b)
               (or (< (obj-r1 a) (obj-r1 b))
                   (and (= (obj-r1 a) (obj-r1 b))
                        (< (obj-c1 a) (obj-c1 b)))))))
     (for/fold ((out g)) ((f (in-list frames)))
       (let* ((r0 (+ (obj-r1 f) 1)) (c0 (+ (obj-c1 f) 1))
              (r1 (- (obj-r2 f) 1)) (c1 (- (obj-c2 f) 1))
              (settled (settle (subgrid g r0 c0 r1 c1))))
         (for*/fold ((acc out)) ((r (in-range (rows settled)))
                                 (c (in-range (cols settled))))
           (set-cell acc (+ r0 r) (+ c0 c) (at settled r c))))))))
```

What to notice: components of "any nonzero cell" via the **mask + objects**
idiom; collision via an occupancy grid threaded through the fold; the
settle order is an explicit, commented sort.

---

## Example 4 — measured geometry chains (medium)

**Task:** the largest object is a TEMPLATE. A row (or column) of single
dots lists stamp colors; one dot shares the template's color — that dot is
the anchor, standing for the template itself. Stamp one copy of the
template per dot, in the dot's color, chained edge-to-edge outward from the
template with the dots' own gaps as spacing.

```scheme
(rule!
 ;; The largest object is a TEMPLATE; the loose dots (one shares its
 ;; color — the anchor) list stamp colors along a row or column. Stamp
 ;; one template copy per dot in that dot's color, chained from the
 ;; anchor edge-to-edge with the dots' own gaps as spacing.
 (lambda (g)
   (let ()
     (define objs (sort (objects-8 g 0)
                        (lambda (a b) (> (obj-size a) (obj-size b)))))
     (define template (first objs))
     (define t-r1 (obj-r1 template))
     (define t-c1 (obj-c1 template))
     (define t-h (obj-h template))
     (define t-w (obj-w template))
     (define pattern (normalize-cells (obj-cells template)))
     (define raw-ms  ;; (color r c) per dot
       (map (lambda (m)
              (let ((c (first (obj-cells m))))
                (list (obj-color m) (first c) (second c))))
            (rest objs)))
     (define horiz?
       (= 1 (length (remove-duplicates (map second raw-ms)))))
     (define ms
       (sort raw-ms (lambda (a b) (if horiz?
                                      (< (third a) (third b))
                                      (< (second a) (second b))))))
     (define n (length ms))
     (define anchor
       (find-first (lambda (i) (= (first (nth ms i))
                                  (obj-color template)))
                   (range 0 n)))
     (define (gap i j)
       (if horiz?
           (- (third (nth ms i)) (third (nth ms j)))
           (- (second (nth ms i)) (second (nth ms j)))))
     (define positions  ;; template corner per dot, chained from anchor
       (let ((fwd (let loop ((i (+ anchor 1)) (prev (list t-r1 t-c1))
                             (acc (list)))
                    (if (>= i n)
                        (reverse acc)
                        (let ((pos (if horiz?
                                       (list t-r1
                                             (+ (second prev) t-w -1
                                                (gap i (- i 1))))
                                       (list (+ (first prev) t-h -1
                                                (gap i (- i 1)))
                                             t-c1))))
                          (loop (+ i 1) pos (cons pos acc))))))
             (bwd (let loop ((i (- anchor 1)) (next (list t-r1 t-c1))
                             (acc (list)))
                    (if (< i 0)
                        acc
                        (let ((pos (if horiz?
                                       (list t-r1
                                             (+ (- (second next)
                                                   (gap (+ i 1) i)
                                                   t-w)
                                                1))
                                       (list (+ (- (first next)
                                                   (gap (+ i 1) i)
                                                   t-h)
                                                1)
                                             t-c1))))
                          (loop (- i 1) pos (cons pos acc)))))))
         (append bwd (list (list t-r1 t-c1)) fwd)))
     (for/fold ((out g)) ((i (range 0 n)))
       (if (= i anchor)
           out
           (paint-cells out
                        (map (lambda (p)
                               (list (+ (first (nth positions i))
                                        (first p))
                                     (+ (second (nth positions i))
                                        (second p))))
                             pattern)
                        (first (nth ms i))))))))
```

What to notice: the forward and backward chains are two named-`let` loops
producing lists (no vectors, no `set!`); `gap` is the single shared
measurement helper; positions are computed once into `positions`, then the
paint step is a plain indexed fold.

---

## Example 5 — dispatch tables over case chains (medium)

**Task:** a blue(1)-bordered panel has four distinct interior corner
colors. Scattered dots outside the panel repeat those corner colors at the
corners of THEIR own bounding box, in some rotated/flipped arrangement.
Output the panel transformed so its corners land the way the dots'
corners do (a missing dot reads as border blue).

```scheme
(rule!
 ;; A framed panel (blue border) has four distinct interior corner
 ;; colors; scattered dots outside repeat those colors at the corners
 ;; of THEIR bounding box, in some orientation. Output the panel
 ;; rotated/flipped so its corners land like the dots' (missing dots
 ;; read as border blue 1).
 (lambda (g)
   (let ()
     (define bb (bbox-of-cells (find-color g 1)))
     (define pr1 (first bb)) (define pc1 (second bb))
     (define pr2 (third bb)) (define pc2 (fourth bb))
     (define panel (subgrid g pr1 pc1 pr2 pc2))
     (define ph (rows panel))
     (define pw (cols panel))
     (define A (at panel 1 1))
     (define B (at panel 1 (- pw 2)))
     (define C (at panel (- ph 2) 1))
     (define D (at panel (- ph 2) (- pw 2)))
     (define scattered
       (filter (lambda (p) (let ((r (first p)) (c (second p)))
                             (and (> (at g r c) 0)
                                  (or (< r pr1) (> r pr2)
                                      (< c pc1) (> c pc2)))))
               (grid-positions g)))
     (define sbb (bbox-of-cells scattered))
     (define (dot r c)  ;; scattered color there, else border blue
       (if (member (list r c) scattered) (at g r c) 1))
     (define signature
       (list (dot (first sbb) (second sbb))
             (dot (first sbb) (fourth sbb))
             (dot (third sbb) (second sbb))
             (dot (third sbb) (fourth sbb))))
     (define transforms  ;; (corner-signature transform), identity first
       (list (list (list A B C D) (lambda (p) p))
             (list (list B A D C) flip-lr)
             (list (list C D A B) flip-ud)
             (list (list D C B A) rotate-180)
             (list (list A C B D) transpose)
             (list (list D B C A)
                   (lambda (p) (rotate-180 (transpose p))))
             (list (list C A D B) rotate-cw)
             (list (list B D A C) rotate-ccw)))
     ((second (find-first (lambda (t) (equal? (first t) signature))
                          transforms))
      panel))))
```

What to notice: eight `cond` branches with hand-written `build-grid`
mirrors became a **data table** of (corner-signature → prelude transform)
pairs plus one `find-first`. When a rule dispatches among fixed cases,
build the table.

---

## Example 6 — rooms, motifs, and learned mappings (large)

**Task:** walls (colors 1/7/9) partition the board into rooms. Some rooms
are EXAMPLES: majority-filled with one color, with a magenta(6) motif
showing through. Each motif shape maps to its example's fill color. The
remaining rooms are queries showing only a motif — paint each query room
entirely with the color its motif maps to.

```scheme
(rule!
 ;; Walls (1/7/9) partition the grid into 4-connected rooms. EXAMPLE
 ;; rooms hold a majority fill color (not 0/6): each maps its motif —
 ;; the room's magenta(6) cells normalized to its bbox origin — to that
 ;; fill. Rooms with no majority fill are QUERIES: paint each one
 ;; entirely with the fill its motif maps to. Everything else passes
 ;; through unchanged.
 (lambda (g)
   (let ()
     (define (wall? v) (member? v (list 1 7 9)))
     (define rooms
       (sort (objects (grid-from-fn h w (lambda (r c)
                                          (if (wall? (at g r c)) 0 1)))
                      0)
             (lambda (a b)
               (or (< (obj-r1 a) (obj-r1 b))
                   (and (= (obj-r1 a) (obj-r1 b))
                        (< (obj-c1 a) (obj-c1 b)))))))
     (define (motif room)
       (sort (filter values
                     (map (lambda (p)
                            (if (= (at g (first p) (second p)) 6)
                                (list (- (first p) (obj-r1 room))
                                      (- (second p) (obj-c1 room)))
                                #f))
                          (obj-cells room)))
             cell<))
     (define (fill-of room)
       ;; majority color of the room excluding 0/6 (ties -> larger), else #f
       (let* ((vals (map (lambda (p) (at g (first p) (second p)))
                         (obj-cells room)))
              (cnt (lambda (col) (count-if (lambda (v) (= v col)) vals)))
              (ranked (sort (unique (filter (lambda (v)
                                              (and (> v 0) (not (= v 6))))
                                            vals))
                            (lambda (a b)
                              (or (> (cnt a) (cnt b))
                                  (and (= (cnt a) (cnt b)) (> a b)))))))
         (if (and (pair? ranked)
                  (> (cnt (first ranked)) (quotient (length vals) 2)))
             (first ranked)
             #f)))
     (define infos
       (map (lambda (room) (list room (motif room) (fill-of room))) rooms))
     (define mapping (filter (lambda (i) (third i)) infos))
     (for/fold ((out g)) ((i (in-list infos)))
       (if (third i)
           out
           (paint-cells out (obj-cells (first i))
                        (third (find (lambda (e) (equal? (second e) (second i)))
                                     mapping))))))))
```

What to notice: rooms come from the **mask + objects** idiom (walls → 0,
everything else → 1); the example/query split and the motif→fill mapping
are plain list operations; the original's 40-line BFS and door-adjacency
graph (dead code!) are gone entirely.

---

## The authoring checklist

1. **Decode the task in prose first.** Write the comment header BEFORE the
   code; if you can't state the rule in ≤12 lines, you don't understand it
   yet.
2. Identify roles (template/marker/frame/scene) and name them.
3. Reach for idioms (04) before inventing: components → mask+objects;
   shapes → normalize-cells/all-transforms; painting → recolor/paint-cells;
   physics → occupancy folds; symmetry → transpose projection.
4. Stage the computation as named `define`s; end on one expression.
5. Check the gotchas (05): mode/unique/for*-fold/shape-before-read.
6. Verify on every train pair; only then apply to test inputs.
