# 03 · Style — naming and structure

The corpus is training data for a model, so consistency **is** quality:
one naming pattern per role, one structural shape per kind of rule.

## 1. The structural template

Every non-trivial rule has the same skeleton:

```scheme
(rule!
 ;; COMMENT HEADER: what the transformation IS. Name the roles in caps
 ;; the first time (the WALL, the KEY), state the decision rule and any
 ;; tie-breaks. 3-12 lines. Written for the next reader, not the model.
 (lambda (g)
   (let ()
     ;; --- predicates & small helpers -------------------------------
     (define (frame? o) ...)
     (define (key-of fr) ...)
     ;; --- data stages, each a named define -------------------------
     (define frames (sort (filter frame? (objects g 0)) ...))
     (define scene (erase-cells g ... 0))
     ;; --- the answer: ONE final expression -------------------------
     (for/fold ((out scene)) ((fr (in-list frames)))
       (process out fr)))))
```

Rules of thumb:

- **Stage, don't nest.** Each conceptual step gets its own `define` with a
  descriptive name. A reader should be able to read only the define names
  and know the algorithm. Avoid `let*` towers more than ~6 bindings deep —
  promote to `define`s.
- **One final expression.** The last form produces the output grid. No
  trailing `define`s, no `begin`.
- **Helpers over repetition.** The moment the same 3+ line computation
  appears twice (per-axis, per-frame, per-orientation), name it. Symmetric
  branches usually collapse: either one axis-parametric helper, or
  transpose/flip projection (see 04-idioms).
- **Folds, not mutation.** No `set!`, no `make-hash` scratch state, no
  `vector-set!`. Thread state through `for/fold` / named `let`. When you
  need two pieces of state, use a multi-accumulator `for/fold` with
  `values`, or thread a 2-element list.
- **Prelude first.** Before writing a loop, check 02: components → `objects`
  on a (possibly painted) mask; flood → `connected-region`; painting →
  `recolor-cells`/`paint-cells`; extremum → `pick-max`. A hand-rolled BFS
  in a new rule is a review defect.
- **Comments inside the body** only where the code cannot say it: a
  non-obvious invariant, a deliberate quirk kept for compatibility, the
  meaning of a magic constant. One `;;` line, sentence case, no banners
  except the optional stage separators shown above.

## 2. Naming conventions

Kebab-case everywhere. Short names for ubiquitous roles, full words for
rule-specific concepts.

### Fixed single-letter / short names (never repurpose these)

| Name | Meaning |
|------|---------|
| `g` | the input grid (auto-bound) |
| `h` `w` | grid height/width (auto-bound) |
| `r` `c` | row / column index |
| `v` | the color value at a cell |
| `p` | a cell `(r c)` in a lambda or fold |
| `o` / `obj` | an object (component) |
| `d` | a delta `(dr dc)` |
| `bb` | a bbox `(r1 c1 r2 c2)` |
| `acc` | fold accumulator (grid or list) |
| `out` | the output grid being threaded through folds |

### Standard binder per construct

| Construct | Binder |
|-----------|--------|
| `(cellmap g (r c v) ...)` | exactly `r c v` |
| `(build-grid H W (r c) ...)` | exactly `r c` |
| object filters/maps | `(lambda (o) ...)` |
| cell filters/maps | `(lambda (p) ...)` |
| grid-threading fold | `((out g)) ((x xs))` |
| nested grid folds | outer `out`, inner `acc` (or `a2`, `gg` when both taken) |

### Derived-value spellings

| Value | Spelling |
|-------|----------|
| bbox corners of a thing X | `r1 c1 r2 c2` (locally), or `xr1 xc1 ...` when two things coexist |
| a normalized cell list | `cells` (after `normalize-cells`) |
| the chosen/selected item | `chosen`, `best`, `hit`, `target` |
| a per-item record list | plural noun: `frames`, `movers`, `panels`, `candidates` |
| predicates | question mark: `frame?`, `wall?`, `interior?`, `fits?` |
| painter/step helpers | verb: `stamp`, `settle`, `pour`, `corridor`, `drop`, `fill-tile` |
| numeric targets read from the input | `<what>-target`: `holes-target`, `sym-target` |

### Domain-role names (capitalize in the comment, kebab in code)

Name grid entities by their role, not their color: `template`, `anchor`,
`marker`, `key`, `frame`, `scene` (the grid after removing scaffolding),
`base` (the canvas being built), `interior`, `rim`, `blockers`, `emitters`,
`glyph`, `motif`, `palette`. Color numbers appear in the comment header
("gray(5) frames") and as literals in the code — never as names like
`color5`.

## 3. Canonical micro-forms

These come from `docs/CANONICAL_STYLE.md` (compactor-enforced); follow them
when authoring so the code is born canonical:

- `(at g r c)` — never `cell-at`.
- `(!= a b)` — never `(not (= a b))` (in dense expressions; `not`+`=` is
  tolerated in beautified multi-line code where it reads better).
- `(zero? x)` — never `(= x 0)`.
- `let*` over nested `let`s; `(let ()` only as the define-scope opener.
- `(unless X Y)` over `(when (not X) Y)`.
- `(recolor-cells g cells COLOR)` over any set-cell fold with constant color.
- `(cellmap ...)`/`(build-grid ...)` over `grid-from-fn` with a literal
  lambda (keep `grid-from-fn` when passing a *named* function).
- `(min-of f xs)` / `(max-of f xs)` over `(min-list (map f xs))`.
- `(find-first pred xs)` over `(first (filter pred xs))`;
  `(count-if pred xs)` over `(length (filter pred xs))`.
- `eq?` for symbols, `equal?` for lists, `=` for numbers.

## 4. Equality and comparators

- Lexicographic comparators are written as an explicit loop over key lists:

```scheme
(define (bb< a b)
  (let loop ((xs (list (obj-r1 a) (obj-c1 a) (obj-r2 a) (obj-c2 a)))
             (ys (list (obj-r1 b) (obj-c1 b) (obj-r2 b) (obj-c2 b))))
    (cond ((null? xs) #f)
          ((< (first xs) (first ys)) #t)
          ((> (first xs) (first ys)) #f)
          (else (loop (rest xs) (rest ys))))))
```

- `sort` is stable — rely on it for tie-breaks: sort by the primary key and
  let input (row-major) order settle ties, or state the tie-break in the
  comparator explicitly.
- Top-left ordering of objects is the default presentation order:

```scheme
(sort objs (lambda (a b) (or (< (obj-r1 a) (obj-r1 b))
                             (and (= (obj-r1 a) (obj-r1 b))
                                  (< (obj-c1 a) (obj-c1 b))))))
```

## 5. Determinism requirements

Anything order-dependent must not rest on unspecified order:

- Never iterate `hash-keys`/`hash-values`/`hash-for-each` for logic (don't
  create hashes at all).
- Never rely on `grid-colors` ordering — derive first-appearance order from
  a row-major scan when the choice of "first color" matters.
- When replacing legacy code that used hash order, replace it with
  first-appearance or sorted order and verify parity on generated inputs.
