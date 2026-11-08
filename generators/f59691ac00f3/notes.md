# Current decisions: f59691ac00f3

The canonical generator and Racket authority are unchanged. Generator SHA-256:
`26a305e8ce1c8708c974cd550c722b9fac5e4aed59be27605ca5f8e8e2c5b7c1`;
canonical program SHA-256:
`2e50ecc613be187d84268664bd1c2c33cf187efe48d02ecf8330366abd929a63`
(normalized short hash `343570d857e4`).

## Native parametric family

`workspace/parametric/adapter.py` is the current native entrypoint. It preserves
the `different_parent` parameter (`right` canonical, `left` alternative), gated
2/5 color propagation and exact materialized Racket programs. It independently
supports 2–6 demonstrations and 1–4 queries; retained training examples use four
queries. Setting-independent RNG streams preserve matched inputs and stable
query prefixes when counts change.

The previous short-demo sampler allowed an early-stop shortcut: seed 0 demos
reach depths 2 and 3 while queries reach 4–6; seed 1 demos reach 5 while one
query reaches 6. A depth-capped Racket rule fits all those demos and disagrees
on a query. Original lessons/programs/labels are retained in
`checks/f59691ac00f3/self-audit/original-ambiguity.json`. The native sampler fixes
the teaching gap with a 16×30 dense demonstration that reaches the maximum
possible depth 14 and includes the extinct next row. A second gapped demo
rejects an endpoint-only support shortcut. The legacy sampler remains solely
for replay; it is not the promoted generation API.

The separate native grammar extends to 30×30 while production bounds remain
3–8 by 5–16. Four query profiles include minimum 3×5, internal gaps, full-width
dense 30×30, and a second 30×30 profile cycling among gapped, uniform and single
parity supports. The dense output's 240 active cells / 210 descendants / depth
14 are mathematically maximal; all rows from 15 onward must be background.

Finite self-review checks six explicit hypotheses using protected Racket.
Opposite setting, frozen parents and a missing gate are rejected by demo 0;
endpoint-only support is rejected by demo 1. Depth cap 14 and gated complement
survive with identical answers, so they are valid equivalent formulations.
Evidence: `checks/f59691ac00f3/self-audit/native-rivals.json`.

## Sequential dependency and its limit

A computes the next row's supported colors from diagonal parents. Its generated
row supplies the active-parent mask and colors to B, which computes the
following row. Substituting the original blank parent row changes final output;
the official source-bound protected witness lives at
`checks/f59691ac00f3/causal/witness.json` with `replay.json`.
The support also has an equivalent closed form: row r at c requires every
top ancestor c−r,c−r+2,…,c+r, and the color is the chosen endpoint complemented
r times. The witness does not prove every correct solver must literally iterate.

## Resolved public writer finding

`prototype.materialize` previously wrote public files in private seed order,
then sorted rows and detected duplicates. It now prepares the entire batch,
validates unique visible IDs and writes in visible-hash order. Both regressions
failed before the edit; both and the 25 prior prototype tests passed afterward.
The pending public-identifier hold is resolved by this actual repair; the new
inventory pins current sources rather than reusing the earlier passing claims.
Receipt: `workspace/parametric/evidence/current/public-writer-repair.json`.

The existing canonical test portability repair remains: use same-checkout
`reviewer_support` and compare normalized hashes where Racket formatting differs.

## Acceptance boundary

The returned native qualification and execution receipts support owner review
of exact bytes; native owner acceptance is still required after integration.
No canonical approval hashes, allocation weights or training admission changed.
Finite seeds/rivals establish neither universal identifiability nor measured
learning benefit. See the parametric README for rerun commands.
