# 02 · Function reference

Every entry: **signature** → what it does → example → sharp edges.
Optional arguments are shown in brackets with their defaults.
All examples assume `g`, `h`, `w` auto-bound.

---

## A. Reading the grid

### `(at g r c)`
Value at row `r`, column `c`. Crashes out of bounds.
```scheme
(at g 0 0)                       ;; top-left cell
```
`cell-at` is a deprecated alias — always write `at`.

### `(safe-at g r c [default 0])`
Bounds-checked `at`; returns `default` when `(r c)` is off-grid.
Use it when scanning neighborhoods near edges instead of writing
`(and (in-bounds? ...) (at ...))` pairs.
```scheme
(= (safe-at mask r c 0) 1)       ;; treat off-grid as empty
```

### `(rows g)` / `(cols g)`
Height / width of any grid (not just `g` — any sub-grid too).

### `(in-bounds? r c h w)`
`#t` when `0 <= r < h` and `0 <= c < w`. Note the argument order:
position first, then the *bounds*.

### `(row g r)` / `(col g c)`
Row `r` as a list / column `c` as a list.
```scheme
(count-if (lambda (v) (= v 4)) (row g 0))   ;; count 4s in the top row
```

### `(grid-positions g)`
All `(r c)` positions, row-major. The standard way to scan every cell
functionally:
```scheme
(filter (lambda (p) (> (at g (first p) (second p)) 0)) (grid-positions g))
```

### `(positions-in-rect r1 c1 r2 c2)`
All `(r c)` in the inclusive rectangle, row-major. Pure arithmetic — the
rectangle does not need to lie inside any grid.

### `(row-uniform? g r)` / `(col-uniform? g c)`
`#t` when every cell in the row/column has the same value (any value,
including 0). The standard separator-line detector:
```scheme
(filter (lambda (r) (and (> (at g r 0) 0) (row-uniform? g r))) (range 0 h))
```

### `(subgrid g r1 c1 r2 c2)`
Rectangular crop, inclusive corners.
```scheme
(subgrid g 1 0 (- h 1) (- w 1))  ;; drop the first row
```

### `(crop-to-content g [bg 0])`
Crop away any all-`bg` border rows/columns.

---

## B. Colors and counting

### `(grid-colors g [exclude -999])`
Distinct values present, **sorted ascending**, INCLUDING 0 by default (the
second argument excludes one value: `(grid-colors g 0)` skips background 0).
Because the result is sorted, it cannot express "which color appeared
first" — when first-appearance order matters (tie-breaks!), derive it
yourself:
```scheme
(remove-duplicates (map (lambda (p) (at g (first p) (second p)))
                        (grid-positions g)))
```

### `(find-color g color)`
All positions holding `color`, row-major, as proper `(r c)` lists.

### `(count-color g color)`
Number of cells holding `color`.

### `(mode g [bg 0])` ⚠
Most common value **excluding `bg`** — and `bg` defaults to 0! For the true
most-common-value use `(mode g -1)`. Getting this wrong is a classic bug on
grids whose background is not 0.

### `(minority g [bg 0])`
Least common non-`bg` value.

### `(mode-list vals [ignore #f])`
Most frequent element of a list; skips `ignore` if given; `#f` on empty.
Works on numbers. Tie-break is unspecified — don't rely on it.

### `(mode-in cells g [bg 0])`
Most common color among grid cells at the given positions (skipping `bg`).

### `(color-frequency g)`
Hash of color → count. Prefer `pick-max` + `count-if` in new code (no hash).

### `(count-if pred lst)` / `(count-where pred lst)`
Count matching elements (aliases; prefer `count-if`).

---

## C. Cells-as-shapes (position-list geometry)

A "shape" here is just a list of `(r c)` cells.

### `(bbox-of-cells cells)`
`(r1 c1 r2 c2)` inclusive bounding box.

### `(normalize-cells cells)`
Shift cells so the bbox corner is `(0 0)`. Does **not** sort.

### `(cell< a b)`
Row-major comparator for cells — use it wherever you need a canonical cell
ordering: `(sort cells cell<)`.

### `(cells-equal? a b)`
Same shape? Normalizes **and** sorts both sides internally, so raw
`obj-cells` lists compare correctly. Beware: because it re-normalizes,
it is *positionless* — two identical shapes at different offsets are equal.

### `(all-transforms cells)`
The 8 dihedral variants (4 rotations × 2 reflections), each normalized and
row-major sorted. Membership test = orientation-independent shape match:
```scheme
(member (sort (normalize-cells target) cell<) (all-transforms proto))
```

### `(match-transform a b)`
Which of the 8 transforms of `a` equals `b`? Returns 0–7 or `#f`
(0=identity, 1=cw90, 2=180, 3=ccw90, 4=flip-lr, 5–7=flip+rotations).

### `(rotate-cells-cw cells)` / `(flip-cells-lr cells)`
Transform a cell list (re-normalize after if you need canonical form).

### Delta constants
`cardinal-deltas` = `((-1 0) (1 0) (0 -1) (0 1))`,
`diagonal-deltas`, `all-8-deltas`. Never write these lists inline.

---

## D. Objects (connected components)

### `(objects g [bg 0])` / `(objects-8 g [bg 0])`
Same-color connected components (4- / 8-connectivity), skipping `bg`.
Returned in row-major discovery order.

### `(objects-multicolor g [bg 0])`
8-connected components of **all** non-`bg` cells, colors mixed.

### Object accessors
```scheme
(obj-color o)   ;; dominant color (for objects/objects-8: the color)
(obj-cells o)   ;; list of (r c) positions
(obj-size o)    ;; cell count
(obj-bbox o)    ;; (r1 c1 r2 c2)
(obj-r1 o) (obj-c1 o) (obj-r2 o) (obj-c2 o)   ;; bbox corners
(obj-h o) (obj-w o)                            ;; bbox dimensions
```
Always use these instead of recomputing from `obj-cells`.

### `(with-bbox obj (r1 c1 r2 c2) body ...)`
Macro destructuring the bbox into four names. Fine in dense code; in staged
rules prefer the direct accessors.

### `(pick-max objs key-fn)` / `(pick-min objs key-fn)`
Element maximizing/minimizing `key-fn`. Ties keep the **earliest** element
— combine with row-major object order for deterministic tie-breaks.
```scheme
(pick-max (objects g 0) obj-size)          ;; the largest object
```

### `(select-object-by objs score-fn ['max])`
Like `pick-max` but with an explicit row-major-bbox tie-break and `'min`
mode. `#f` on empty list.

### `(solid-rect? obj)`
`#t` when the object's cells exactly fill its bbox (a filled rectangle).
Combine with the `frame?` idiom (04) to separate plates from outlines.

---

## E. Painting and building grids

### `(recolor-cells g cells color)`
Paint every position in `cells` with one color. **The** workhorse — replaces
any fold of `set-cell` with a constant value.

### `(paint-cells g cells [color #f])`
Like `recolor-cells`, but: with `color` omitted, cells may be `(r c v)`
triples and each paints its own `v`. Silently **skips out-of-bounds cells**
(recolor-cells does too) — useful for clipped stamps.

### `(erase-cells g cells [bg 0])`
Paint cells to background.

### `(set-cell g r c v)`
One cell (returns a new grid). Crashes out of bounds — guard with
`in-bounds?` when the target is computed.

### `(cellmap g (r c v) body ...)`  — macro
Same-size transform: body computes the output value for each cell.
```scheme
(cellmap g (r c v) (if (= v 3) 0 v))       ;; delete all green
```

### `(build-grid H W (r c) body ...)`  — macro
New grid of a *different* size, value per cell from body.

### `(grid-from-fn h w fn)`
Function form of `build-grid` (`fn` = `(lambda (r c) ...)`) — use when the
per-cell function is a named helper. ⚠ its lambda's `r c` shadow outer
bindings; rename outer variables if you must reference them.

### `(empty-grid h w [fill 0])`
Constant grid.

### `(overlay g1 g2 [bg 0])`
Same-size layering: `g2`'s non-`bg` cells win over `g1`.

### `(paste g sub r c)`
Place `sub` with its corner at `(r c)`. Overwrites **everything** in the
window — including `sub`'s zeros — and self-clips at `g`'s edges. For
"paste skipping zeros" write the explicit stamp fold (see 04-idioms).

### The `recolor` family (whole-grid, NOT curried)
```scheme
(recolor g from to)          ;; one color -> another
(recolor-map g (hash 8 7 1 0)) ;; simultaneous mapping (hash)
(remove-color g color [bg 0])  ;; color -> bg
(swap-colors g c1 c2)
(keep-only g color [bg 0])     ;; everything else -> bg
```
All take the grid as the FIRST argument. (The REPL layer offers curried
one-argument forms for `pipe` chains; stored rules use the direct forms.)

### Whole-grid transforms
`(transpose g)` `(flip-lr g)` `(flip-ud g)` `(rotate-cw g)`
`(rotate-ccw g)` `(rotate-180 g)` `(upscale g k)` `(downscale g k)`.

### `(casev v table [default v])`  — value dispatch
`table` is a hash: `(casev v (hash 5 4 7 5) v)` maps 5→4, 7→5, else keeps
`v`. The REPL also accepts `{5 4 7 5}` brace sugar for `(hash ...)`, but
the `(hash ...)` form is what works everywhere — prefer it in stored rules.
⚠ Because of that sugar, never put `{` or `}` inside comments (they get
preprocessed and eaten).

---

## F. Regions, flood, topology

### `(connected-region g r c pred? [connectivity 4])`
BFS from `(r c)` over cells satisfying `pred?` = `(lambda (r c v) ...)`.
Returns the region's `(r c)` list. **Replaces every hand-rolled BFS.**
```scheme
(connected-region g sr sc (lambda (r c v) (= v 1)) 8)   ;; the blue blob at (sr,sc)
```

### `(find-0-regions g [bg 0])`
All 4-connected components of `bg` cells, as lists of cells. Standard trick
for hole detection: filter for regions that never touch the border.

### `(topo-count-holes g obj [bg 0])`
Number of `bg` regions inside `obj`'s bbox not connected to the bbox border
— i.e. holes the object encloses.

### `(flood-fill g r c color)`
Repaint the connected same-color region containing `(r c)`.

### `(fill-all-enclosed g color [bg])`
Fill every background pocket not reachable from the border.

⚠ **Phantoms:** `flood-from`, `largest-rect`, `best-orientation` appear in
old docs but are **not defined**. Use `flood-fill`, an explicit rect scan,
and `all-transforms`/`match-transform`.

---

## G. Lists and higher-order helpers

### Access
`first second third fourth` · `(nth lst i)` · `(rest lst)` · `last`
(Racket built-in; crashes on empty) · `(empty? lst)` / `(null? lst)` ·
`(fst p)` / `(snd p)` — first/second that also accept dotted pairs
(useful when consuming legacy cons-cell data).

### Membership — three different tools ⚠
- `(member x lst)` — Racket built-in, `equal?`-based, returns the tail (truthy)
  or `#f`. Works on **any** values including cell lists. Use in conditions.
- `(member? x lst)` — boolean wrapper of the same. Preferred for readability.
- `(unique lst)` — **`(sort (set->list ...) <)`** — numbers ONLY, and it
  sorts ascending. It **crashes on lists of lists**. For cells or any
  non-numeric values use `remove-duplicates` (preserves first-appearance
  order).

### Transform / select
`(map f lst)` · `(filter pred lst)` · `(flatmap f lst)` (one-level flatten)
· `(find pred lst)` / `(find-first pred lst)` (identical: first match or
`#f`) · `(any? pred lst)` · `(all? pred lst)`.

### Reduce
`(foldl f init lst)` — f takes `(elem acc)`.
`(reduce f init lst)` — f takes `(acc elem)`. ⚠ opposite argument orders;
pick one per rule and stay consistent (prefer `for/fold` for anything
non-trivial).

### Numeric
`(min-list lst)` `(max-list lst)` — min/max of a list.
`(min-of f lst)` `(max-of f lst)` — min/max of a mapped list.
`(count-if pred lst)`.

### Misc
`(sort lst less?)` — stable. `(sort-by lst key-fn)` = ascending by key.
`(remove-duplicates lst)` — order-preserving dedup, any values.
`(enumerate-list lst)` — `((0 x0) (1 x1) ...)`.
`(range a b [step])` — half-open. `(make-list n v)`. `(zip-lists l1 l2)`.
`(apply min lst)` etc. — fine, but crashes on empty lists; prefer
`min-list` on lists you know are non-empty and guard otherwise.

---

## H. Iteration forms (the fold family)

```scheme
(for/list  ((x xs) #:when (ok? x)) body)          ;; map+filter
(for*/list ((r (range 0 h)) (c (range 0 w))) ...)  ;; nested product
(for/fold  ((acc init)) ((x xs)) body)             ;; thread one accumulator
(for*/fold ((acc init)) ((a as) (b bs)) body)      ;; nested product fold
(for/fold  ((a i1) (b i2) #:result a) ((x xs))     ;; multiple accumulators —
  (values ...new-a ...new-b))                      ;;   body returns (values ...)
(for/sum ((x xs)) body)  (for/or ...)  (for/and ...)
```

⚠ **`for/fold` with two parallel clauses ZIPS the sequences.** For a nested
product you must use `for*/fold` (this exact bug has shipped).

Named `let` is the loop of choice for walks and fixpoints:
```scheme
(let loop ((x start) (acc (list)))
  (if (done? x) (reverse acc) (loop (step x) (cons x acc))))
```
