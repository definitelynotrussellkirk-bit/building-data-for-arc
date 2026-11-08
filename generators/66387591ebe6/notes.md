# Current decisions: 66387591ebe6

## Production authority and unresolved scope

The selected production generator remains version 2.1.0, SHA-256
`a9441145ece90f77e0f9ae76aac15706055e0daf6648d6fcd93910ee48119782`.
The selected canonical program is unchanged, rule hash `60007e76f218`, exact
program SHA-256
`60007e76f2188c327bb9fde3962cc36c3b0573e38d45735fa937fcddceb27673`.
It reads key k at (0,0), keeps the unique color-9 pivot, and transports every
other foreground cell and its color by k-1 clockwise quarter-turns onto a
fresh zero canvas. Identity at key 1 is lawful.

Production still samples a connected three/four-cell object near the pivot,
9/11-scale canvases, keys 2–4, scheduled multicolor and off-center witnesses.
Exact overrides additionally support key 1 and rectangular 9×11/11×9 cases.
The October 24 scalar repair requires exact integer seed and nonnegative exact
integer sample_index; signed integer seeds remain valid. Its prior 20 staged
tests and source-bound parity evidence remain under
`evidence/repair-review-400900fb9684fbbd-v0001/`.

The existing audit in `evidence/review_index.json` remains **unresolved**:
ordinary production lessons omit key 1 because the shared identity-output gate
was calibrated against canonical pairs without identity. The new family below
teaches key 1 but does not alter production, its audit, approval or sampling.

## Separate native family

`workspace/parametric/adapter.py` exposes `turn_source=key|hit_size`.
The key setting returns the exact selected canonical bytes. The alternative
traces a keyed N/E/S/W ray, selects its first same-color four-connected object,
and uses `(size-1) mod 4` to choose the rotation of all payload. No hit means
no action. This is a genuine dependency: the hit object's size varies by input
and determines the later transform. The causal witness in the return compares
it with a protected-Racket skip-ray/key-only rule on the same input.

Five to six demos and one to four queries are independently supported. Five
mandatory demos teach all four keys, all rotation residues, size wraparound,
no-hit behavior, and differing results for repeated key and hit color. This
cost is above the usual three demos, but avoids leaving those branches untaught.
The first two demos share 9×9 dimensions while needing different rotations.
The four novel queries are 9×9, 17×17, 23×23, 30×30. Long colored structures rotate
across a 29×29 safe square on the 30×30 canvas; all cells are safe under all turns.
A common seeded palette and independent scene streams give identical inputs
across settings and stable demo/query prefixes.

The extended grammar is deliberately bounded: staircase target shapes and a
three-sided colored frame aligned with the key, not arbitrary objects or
independently varied cue layouts. It extends the separate family without
widening the production sampler. Labels execute through protected Racket;
private settings/programs/answers never enter public challenges or their IDs.

## Observed draft failures and repairs

- Different canvas sizes for every demo admitted a size-to-turn lookup in both
  settings. Two same-size, different-turn demos now eliminate that shortcut.
- The initial composed rule used key-controlled fallback on no hit. With one
  such demo, constant-three-turn fallback fit all demos but failed a query.
  The current alternative uses no-hit/no-action, following its dependency
  instead of borrowing a second fallback law. This changes only the draft
  alternative; the canonical default is unchanged.
- A proposed atomic `(rule! g)` identity rival did not normalize in the native
  wrapper. It now uses `(rule! (let () g))`; runtime errors never count as
  eliminated rivals.

These are actual executed failures in `workspace/parametric/evidence/teaching-before/`
and the historical failed `evidence/final-seed0/`. Three original ambiguous
lessons with exact executable hypotheses are retained under
`evidence/alternative-solutions/`, separate from the repaired curriculum.

Current self-audits in `evidence/repaired-seed0/` and `repaired-seed17/` each
made 208 protected Racket evaluations: both settings passed, thirteen canonical
and thirty composed-rule rivals were eliminated from demos, and three lookup
families were checked per setting. Only the correct canonical key lookup
survived and agreed on every query. Source hashes, label replay, public mutation
invariance and identical one/four-query first-turn content are recorded there.
This covers the finite tested family, not universal identifiability.

The direct native suite passes 41 tests. The inherited full test suite requires
the packet's staged task-test layout; direct pytest collection fails on its
legacy import path. The official staged task-tests pass 61 tests. Failed direct
collection and successful staged receipts are retained separately in the return.

Native source inventory, qualification and executed causal witness accompany
the return. Exact-source owner qualification/acceptance remains the next action;
reviewer-ready evidence does not approve variants or admit training data.
