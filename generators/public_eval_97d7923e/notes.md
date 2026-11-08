# Current design and implementation

Parent `97d7923e` uses the colored runs touching the top row as rank keys.  A
run of length `k` and color `c` selects the `k`-th longest vertical wire whose
endpoints are both `c` and whose interior is a uniform nonzero different color.
The selected interior is recolored to `c`; other wires are preserved.  Ties use
top row then column order.  The authored general Racket rule reproduces all
three demonstrations and the private public-evaluation gold.

The native parameter is `relay_mode`.  `rank_only` is the exact canonical
program.  `selected_longest` first performs the same rank-coded recoloring,
then identifies the longest *selected* wire and activates the horizontal
`color,9...,9,color` relay for that winning color.  Inputs are matched across
settings and always materialize four distinct queries; the last is a dense
30x30 stress case.

A produces the stage-A grid and selected length for each legend color.  B
consumes those selections to choose the relay color.  Generated scenes
constructively make the longest raw candidate belong to a different color than
the longest rank-selected wire.  The retained protected-Racket counterfactual
uses the raw longest candidates and therefore changes the final output.

This is unapproved authoring work.  Owner registration, exact-source review,
native qualification/acceptance, and any training admission remain pending.
Finite rival checks do not establish universal rule uniqueness.

## Current repeated-parent reconciliation

Preserve exact rank-only and selected-longest-relay programs. Add longest-selected full-rod highlighting using the incumbent stage-A parser and stage-selected winner; ties retain incumbent legend order rather than restricting the domain. This ports the incoming highlight idea while preserving current relay-bearing domains. Add incoming rod constructor. Current evidence resides in evidence/repeat-eighth-union. Private native acceptance and root publication are separate.

## Current repeated-return reconciliation

- review-57c895bf18063220: Retain exact incoming inverse-rank program and constructor as an episode branch; accepted default and three prior programs stay byte-identical.
- review-384ba30ff2bc508b: Accepted incumbent already contains the exact engine, programs and sampler. Retain its runtime closure and causal evidence.
- review-3fa090d6bdf2e50f: Preserve the previously accepted highlight semantic port and existing sampler diversity. Incoming legend/rank grammar remains unresolved: ten seed-0 inputs disagree with accepted default; no claim that its default grammar was incorporated.

Accepted default and prior program bytes remain unchanged. Evidence and unresolved input/phase witnesses: `evidence/reconcile-16/`. Private native qualification, fresh private native acceptance and accepted generation passed. Live owner publication and training admission remain separate.

Sampler preservation uses a separate outer-bank schedule: all incumbent query banks are observed intact before selecting complementary episode banks. See `evidence/reconcile-16/sampler-diversity.json`.
