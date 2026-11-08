# 05 · Gotchas — every way rules have actually broken

Ordered roughly by how often each one bites. Read before submitting.

## 1. `unique` sorts numerically — and CRASHES on lists
`(unique lst)` is literally `(sort (set->list (list->set lst)) <)`.
- On numbers: fine, but the result is **ascending order**, not input order.
- On cell lists / any non-numbers: `<` throws
  (`<: contract violation ... given '(5 16)`).
**Rule:** `unique` for numbers when ascending order is acceptable;
`remove-duplicates` (order-preserving, any values) for everything else.

## 2. `mode` excludes 0 by default
`(mode g)` = most common value **ignoring 0**. On a grid whose background
is 0 that's usually what you want; on any other background it silently lies.
`(mode g -1)` = true modal value. Same trap in `mode-in`.

## 3. Phantom primitives
`flood-from`, `largest-rect`, `best-orientation` are referenced by old docs
but **do not exist**. Substitutes: `flood-fill`; an explicit
`for*/fold` rectangle scan; `all-transforms` / `match-transform`.

## 4. `for/fold` parallel clauses ZIP
```scheme
(for/fold ((acc x)) ((a as) (b bs)) ...)   ;; pairs as[i] with bs[i]!
(for*/fold ((acc x)) ((a as) (b bs)) ...)  ;; full nested product
```
Symptom: rule silently processes a fraction of the combinations.

## 5. Check shape BEFORE reading at computed positions
`(at pat r c)` crashes (or worse, wraps) when a computed position leaves the
grid. Any time an index is derived from *another* object's geometry, guard
with the size test first:
```scheme
(and (same-shape? o) (matches-pattern? o))   ;; NOT the other order
```

## 6. `for/or` and `for/first` value traps
- `(for/or (v lst) v-or-#f)` returns `#t`, not the value.
- `(for/first (v lst) body)` returns the first **body** value — including
  `#f` from a failed first iteration, ending the search early.
Canonical: `(find-first pred lst)` — first element satisfying pred, or `#f`.

## 7. Braces in comments get eaten
`{...}` is preprocessed into hash literals **everywhere in the source,
including comments**. Never write `{` or `}` in a `;;` comment.

## 8. Integer division
`(/ 3 9)` → `0`. For fractions force a float: `(/ (+ 0.0 3) 9)`.
`quotient`, `modulo`, `remainder` for explicit integer arithmetic.
Convert back with `(inexact->exact (round x))`.

## 9. Nullary lambdas break
`(lambda () body)` — the empty parameter list gets mangled by the bridge.
Use `(define (f) body)` at the rule's define level instead.

## 10. `grid-from-fn` lambda shadows `r`/`c`
```scheme
(let ((c (at g 1 0)))                 ;; c = a color...
  (grid-from-fn h w (lambda (r c)     ;; ...now c is a COLUMN
    ...)))
```
Rename the outer binding (`kc`, `tc`) or use `cellmap`/`build-grid` whose
binders are always fresh `r c (v)` by convention.

## 11. Equality operators by type
`=` numbers · `eq?` symbols · `equal?` lists/grids. `(= 'up 'up)` may work
on the bridge but is wrong Racket — use `eq?`. `member`/`member?` use
`equal?` (safe for cells).

## 12. Empty-list crashes
`(apply min '())`, `(first '())`, `bbox-of-cells` on no cells — all crash.
Legacy rules often share this behavior; when beautifying, preserve it
(a crash the generator never triggers is not yours to fix silently), but in
NEW rules guard the empty case explicitly.

## 13. Cells are proper lists — but `fst`/`snd` exist for a reason
In the current prelude `find-color`, `obj-cells`, `grid-positions` all
return proper `(r c)` lists, and `first`/`second` are always safe on them.
Legacy rules sometimes carry cons pairs `(r . c)`; the accessors
`fst`/`snd` and the paint helpers accept both forms. When editing an old
rule that uses `(cons r c)`, either keep its representation consistently or
convert at the boundary — never mix within one list.

## 14. `reduce` vs `foldl` argument order
`(reduce (lambda (acc x) ...) init lst)` but
`(foldl (lambda (x acc) ...) init lst)`. Mixing them up type-checks and
produces garbage. Prefer `for/fold`, which has no ambiguity.

## 15. Orders you must not depend on
- `hash-keys` / `hash-values` / `hash->list` iteration is unspecified
  (don't use hashes for logic at all),
- tie-breaks in `mode-list` are unspecified,
- `grid-colors` IS deterministic but **sorted ascending** — it can never
  tell you which color appeared first.
When logic depends on "first" or "which of the tied", make the order
explicit: row-major scans, `sort` with a full comparator, `pick-max`
(earliest-wins ties).

## 16. Deliberate legacy quirks are semantics
Beautification must preserve behavior EXACTLY — including hardcoded
special cases, weird tie-breaks, and even out-of-bounds crashes on inputs
the generators produce. The parity gate is: all demo pairs + ~36 generated
inputs bit-identical against the old rule. "The old code was wrong" is not
a reason to change behavior inside a beautification.

## 17. The verifier only accepts real grids
A program that evaluates to `#t`, a number, or ragged rows is a failure —
make sure every branch of the final expression returns a rectangular grid.
