# Racket DSL — canonical contract

This is the language we teach the model. Everything below is enforced
by `arc_repl/racket_prelude/arc-prelude.rkt` plus the `rule!` macro in
`arc_repl/executor.py`. New solutions, new tests, and new prelude
extensions all conform to it.

## `rule!` — two equivalent shapes

The `rule!` REPL command accepts either a callable-producing form
**or** a body expression. Both work; the body form is canonical.

### Body form (canonical)

```scheme
(rule! BODY)
```

`BODY` is any expression that returns a grid. It runs inside an
auto-bound preamble — no boilerplate `(let* ((h (rows g)) ...))`:

```scheme
;; Canonical
(rule!
  (grid-from-fn h w (lambda (r c) (cell-at g r c))))
```

The wrap that fires is exactly:

```scheme
(lambda (g)
  (let* ((h (rows g))
         (w (cols g)))
    BODY))
```

### Auto-bound names

| Name | Value | When used |
|------|-------|-----------|
| `g` | the input grid | always |
| `h` | `(rows g)` | always |
| `w` | `(cols g)` | always |

That's the whole list. Specifically, **`bg` is NOT auto-bound** —
the semantic background varies by task (sometimes 0, sometimes the
mode color, sometimes the frame color). Bind it locally when you need
it:

```scheme
(rule!
  (let ((bg (mode g 0)))
    ...))
```

### Callable form (legacy / advanced)

When `(rule! ...)` sees one of these heads it skips the auto-bind
wrap and uses the expression as-is:

- `lambda` — `(rule! (lambda (g) ...))`
- `pipe` — `(rule! (pipe f g h))`
- `compose` — `(rule! (compose f g))`
- `fork`, `power` — combinator forms
- A bare symbol bound to a function: `(rule! my-named-rule)`

The 994 existing legacy `(rule! (lambda (g) ...))` rules continue to
work bit-for-bit. Use the body form for new code.

## Canonical primitive names

The prelude is alias-free as of 2026-04-25. There is **one** name per
operation. If you reach for a synonym and the bridge says
`undefined`, use the canonical name from the table below.

| Concept | Canonical name |
|---|---|
| Read a cell | `cell-at` |
| Grid dimensions | `rows`, `cols` |
| Set of distinct colors | `grid-colors` |
| Construct a blank grid | `empty-grid` |
| Slide cells in a direction | `gravity` |
| Flip / rotate | `flip-lr`, `flip-ud`, `rotate-cw`, `rotate-ccw` |
| Object accessors | `obj-color`, `obj-size`, `obj-cells`, `obj-bbox` |
| Connected components | `objects`, `objects-8`, `objects-multicolor` |

The earlier 35 compatibility aliases (`grid-rows`, `num-rows`,
`mirror-h`, `rotate-90`, `object-color`, `get-cell`, `colors-of`,
`flood`, …) were removed when the audit confirmed every apparent
callsite was a local let-binding rather than a real call. **Do not
introduce new aliases** — they accrete shadow vocabulary that the
model has to learn.

### Color / shape primitives

```scheme
;; Whole grid
(mode g [bg])               ;; most common color (excluding bg)
(color-majority g [bg])     ;; >50% of non-bg cells, or #f

;; Within a list of (r c) cells
(mode-in cells g [bg])              ;; argmax color in cells
(majority-color-in cells g [bg])    ;; >50% in cells, or #f

;; Convenience over an object
(obj-mode-color obj g [bg])
(obj-majority-color obj g [bg])
```

The `*-in` family was added 2026-04-25 to retire the inlined
`(map (λ (p) (cell-at g (first p) (second p))) cells)` →
`(sort-by ...)` → `(first (first ...))` pattern that recurred ~50
times across grounded rules. New code: use the primitive.

## Banned forms

### `for/or` for value-search

`for/or` returns `#t/#f`, not the matching value. Repeatedly bites
us — at least 11 grounded rules have been repaired specifically for
this bug (see AGENTS.md). When you want "the first element where
predicate holds":

```scheme
;; WRONG — returns #t, not the value
(for/or (v lst) (if (good? v) v #f))

;; RIGHT — returns the value, #f if none
(find-first good? lst)
;; or
(let ((hits (filter good? lst)))
  (if (null? hits) #f (first hits)))
```

`for/first` has the same trap — it returns `#f` if the *first*
iteration produces a falsy value, even if a later iteration would
succeed. Same fix: filter then take.

### Naked `(/ a b)` between integers

Racket's `/` does integer division when both arguments are integers,
which is rarely what an ARC rule wants. Use `arc/` or coerce with
`(+ 0.0 a)`:

```scheme
(/ 3 9)            ;; → 0   (integer div, almost certainly a bug)
(arc/ 3 9)         ;; → 1/3
(/ (+ 0.0 3) 9)    ;; → 0.333…
```

### Variable names that shadow auto-binds

Don't rebind `g`, `h`, `w` to mean something else. If you need
"height of an object", call it `oh`/`obj-h`/etc. Shadowing the
preamble works lexically but reads as a bug.

## Adding a primitive

Three rules:

1. **Implement in `arc_repl/racket_prelude/arc-prelude.rkt`.** Not in
   the legacy `arc_repl/prelude/*.rkt` files (those are kept around
   for the Python evaluator fallback and should stop accumulating).
2. **No alias unless it has documented usage.** A name with zero
   uses in `solvers/grounded_rules.py` is dead code by month's end.
3. **Smoke-test from `scripts/check_racket_primitives.py`.** Add an
   assertion that the primitive returns the expected value on a
   small grid.

## Inventory commands

```bash
# All defines in the prelude:
grep -nE '^\(define' arc_repl/racket_prelude/arc-prelude.rkt | wc -l

# Most-used primitives across grounded rules:
python3 -c '
import re, collections
src = open("solvers/grounded_rules.py").read()
ctr = collections.Counter(re.findall(r"\(([a-z][a-zA-Z0-9!?+*/<>=._-]+)", src))
for k, v in ctr.most_common(40): print(f"{v:6d}  {k}")'

# Deprecated-alias usage (should trend to 0):
python3 -c '
import re; src = open("solvers/grounded_rules.py").read()
for n in ["get-cell","num-rows","num-cols","width","height","colors-of","new-grid","flood"]:
    print(f"{n:12s}: {len(re.findall(rf\"\\({n}[ )]\", src))}")'
```
