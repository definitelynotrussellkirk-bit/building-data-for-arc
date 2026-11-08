# 01 · Execution model — the contract

## The shape of a rule

Authored (source) form — what you write, submit, and store:

```scheme
(rule!
 ;; 3-12 line comment: what the transformation IS, in plain language.
 ;; Name the roles ("the WALL", "the KEY dot"), the decision the rule
 ;; makes, and any tie-breaks. This header is for the next reader.
 (lambda (g)
   (let ()
     (define stage-one ...)
     (define (helper x) ...)
     ...
     final-expression)))
```

- `(rule! ...)` marks the expression as the rule. Inside it, one
  `(lambda (g) body)`.
- The `(let ()` opens a scope for internal `define`s — the house pattern for
  any rule with more than one step. Trivial rules can be a single expression:
  `(rule! (recolor (recolor g 8 7) 1 0))` (body form; `g h w` auto-bound).
- The training pipeline later strips the wrapper and comments automatically —
  **you never minify by hand**. Source stays pretty and commented.

## Auto-bound names

Inside the rule body these are already bound; **do not** redefine them:

| Name | Value |
|------|-------|
| `g`  | the input grid |
| `h`  | `(rows g)` — number of rows |
| `w`  | `(cols g)` — number of columns |

Writing `(let* ((h (rows g)) (w (cols g))) ...)` is legacy noise; it appears
in old rules and gets removed on beautification.

## Data types

| Type | Representation | Notes |
|------|----------------|-------|
| grid | list of rows; each row a list of ints 0–9 | `[[0 1] [2 3]]` literal syntax works |
| cell / position | 2-element **list** `(list r c)` | row first. NOT a cons pair. `first`/`second` access. |
| cell with value | 3-element list `(r c v)` | accepted by `paint-cells` |
| bbox | 4-element list `(r1 c1 r2 c2)` | inclusive corners, row-major |
| object | opaque record from `objects` etc. | use `obj-*` accessors only |
| color | int 0–9 | 0=black 1=blue 2=red 3=green 4=yellow 5=gray 6=magenta 7=orange 8=cyan 9=maroon |

One prelude exception: `find-color` historically returned cons pairs, so
paint helpers (`recolor-cells`, `paint-cells`) accept **both** list and cons
cells. Everything you construct yourself should be proper lists.

## Grids are immutable values

`set-cell` returns a **new** grid. There is no in-place mutation. All
accumulation happens by threading a grid through a fold:

```scheme
(for/fold ((out g)) ((p cells))
  (set-cell out (first p) (second p) 4))
```

## Coordinate conventions

- `r` grows downward, `c` grows rightward; `(at g 0 0)` is the top-left cell.
- Ranges are half-open in `range`: `(range 0 h)` = all row indices.
- Rect helpers (`positions-in-rect`, `subgrid`) take **inclusive** corners.

## Verification — what "done" means

A rule is executed by the Racket bridge against every train pair; it must
reproduce each expected output exactly. There is no partial credit in the
corpus. Programs that evaluate to anything other than a rectangular 0–9 grid
(a boolean, a number, ragged rows) are treated as failures.

Practical loop when developing interactively (REPL):

```scheme
(rule! ...)        ; set the rule
(test-all!)        ; run against every train pair -> PASS/FAIL + diffs
(apply! 0)         ; apply blind to test input 0
(submit! _1)       ; commit
```

## The closed vocabulary

Rules may only use forms the grammar admits: the prelude's primitives plus
core Racket special forms (`define`, `lambda`, `let`/`let*`/named `let`,
`if`/`cond`/`when`/`unless`/`and`/`or`, `for/list` `for*/list` `for/fold`
`for*/fold` `for/sum` `for/first` `for/or` `for/and` with `#:when`/`#:result`,
`sort`, `values`, quasiquote-free quoting of symbols `'up`). If you need a
primitive that doesn't exist — **do not hack around it with exotic Racket**;
compose existing primitives, or flag the gap.
