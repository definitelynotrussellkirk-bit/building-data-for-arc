# The ARC Racket DSL — Reference Manual

This folder is the **complete, self-contained guide** to writing grid-transformation
rules in our Racket DSL. It is written for two audiences at once:

1. **Humans** joining the project who need to author or review rules.
2. **LLMs with zero prior exposure** to this codebase — paste these files into a
   fresh context and the model has everything it needs to write a correct,
   house-style rule one-shot.

## What a rule is (30 seconds)

A rule is a Racket expression that transforms one colored grid into another:

```scheme
(rule!
 ;; every red(2) cell becomes cyan(8); everything else unchanged
 (lambda (g)
   (recolor-cells g (find-color g 2) 8)))
```

- Input `g` is a grid: a list of rows, each row a list of integers `0–9`
  (0 usually background — but **never assume it**; see 05-gotchas).
- `h` and `w` (the grid's height and width) are **auto-bound** — never rebind them.
- The rule runs on real Racket (Chez) with a ~1000-definition prelude of grid
  primitives preloaded. Everything in `02-function-reference.md` is available
  without imports.
- A rule is correct when it reproduces **every** train pair of its task exactly,
  pixel for pixel.

## Reading order

| File | What it covers | Read when |
|------|----------------|-----------|
| `01-execution-model.md` | The contract: data types, the wrapper, verification | always, first |
| `02-function-reference.md` | Every important primitive: signature, semantics, example, sharp edges | keep open while writing |
| `03-style.md` | Variable naming + how to structure a rule (the house style) | before writing your first rule |
| `04-idioms.md` | The cookbook: named multi-line patterns the corpus uses again and again | when a task smells like a known pattern |
| `05-gotchas.md` | The footgun list — every way rules have actually broken | always, before submitting |
| `06-worked-examples.md` | Complete real rules with their task descriptions (one-shot exemplars) | to calibrate scope and style |
| `07-prelude-inventory.md` | Auto-generated list of EVERY defined function — if a name isn't here, it doesn't exist | grep it before calling anything unusual |
| `08-archetypes.md` | Task-smell → plan decision table (18 archetypes) | at the start of every new task |

## Minimal prompt recipe for an LLM

If you are stuffing a model context, the minimum viable set is:
`01` + `03` + `05` + `06`, and add `02` (or the relevant sections of it)
as the reference the model consults. `04` buys the biggest quality jump
per token after those; `08` primes the plan; `07` is the anti-hallucination
backstop (searchable list of every callable name).

## This documentation is TESTED

`python3 GUIDE/selfcheck.py` extracts every ```scheme block from these
files and executes the runnable ones on the real Racket bridge (full rules
are applied to a probe grid; fragments run with stub bindings). A failing
snippet is a doc bug — fix the doc, keep the check green.
`python3 GUIDE/selfcheck.py --inventory` regenerates `07` from the prelude
so the inventory can never drift.

## The one-paragraph style summary

Write the rule as `(rule! ;; comment header — what the transformation IS
(lambda (g) (let () <named define stages> <final expression>)))`. Decompose
into small `define`d helpers and data stages with descriptive kebab-case
names; build outputs with folds (`for/fold`, `for*/fold`, `foldl`) — never
`set!`, never scratch hashes; use the prelude's object/paint primitives
instead of hand-rolled BFS or per-cell loops; and end on a single expression
that produces the output grid.
