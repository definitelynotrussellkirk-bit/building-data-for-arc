# Working notes: 55cfa127936a

## 2026-10-25 native parametric review

### Decision

Retain the selected canonical rule byte-for-byte as `selection=topmost`, and add
one nearby episode-fixed alternative, `selection=singleton_anchor_nearest`, on a
matched input grammar.  The alternative is intentionally sequential:

1. Find the unique active column containing exactly one yellow cell and derive
   that cell's row.
2. Use that input-dependent anchor row to keep, in every active column, the
   yellow cell nearest the anchor (upper row wins a tie).

Changing the intermediate anchor changes the final grid; this is retained as a
protected-Racket wrong-intermediate witness.  The alternative preserves the
source task's per-column selection structure rather than replacing it with a
cosmetic recolor or an unrelated transform.

### Episode contract

The adapter supports 2–6 demonstrations and 1–4 queries.  Inputs are independent
of the hidden setting and count-prefix stable.  Both settings receive the same
inputs; only labels differ.  The four-query bank contains distinct inputs and a
substantive 30x30 case.  `public_turn()` exposes demonstrations and exactly one
query input, while settings, programs, answers, future queries, and total-query
hints stay private.

The minimum two-demo lesson refutes the other declared setting plus seven named
wrong rules: bottommost, wrong tie direction, farthest from anchor, three fixed
reference rows, and marker-column selection.  This finite audit does not prove
unique inference against every possible program.

### Source binding and verification

- Production generator SHA-256:
  `d79364d3c7e75ea6eabe8b28c94d1a6f648930333dd778ec601f2cd8405c2f20`
- Adapter SHA-256:
  `afb462f9a67feb999cf01dfa55000dc9426dbefe99a95eb01c4ade0b92fc5468`
- Canonical program SHA-256:
  `e0c288d023d5815af299d70ba33f77c8c53f7ff414a4b74672a02319e2e5a3e3`
- Alternative program SHA-256:
  `5187b762045adc6ca5907bbfef9bb28488beb9bc90fc48db05b6dfdf87c054ef`

Fresh final checks passed 17/17 task-local tests.  The bounded teaching audit
covered 320 Python episodes (32 seeds, both settings, every supported demo count,
four queries) plus 88 protected-Racket evaluations, with no surviving declared
rival and with 30x30 coverage.  Native qualification passed both settings on
seeds 0 and 17 with three demonstrations and four queries (40 protected-Racket
evaluations).  The causal witness independently replayed.  Two saved public
projections passed the strict checker.

### Handoff and limits

Reviewer status is `ready`, not accepted.  The owner must integrate these exact
bytes, review the parameter semantics and causal argument, rerun native
qualification, and perform fresh protected acceptance.  No training admission or
measured learning-gain claim is made.
