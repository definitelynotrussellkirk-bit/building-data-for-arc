# Working notes: 661dffbdf39a

## Canonical behavior

Detect strict-majority gray rows and columns, complete their gray lines, clear
off-line noise, and mark every crossing with the unique non-black/non-gray input
color. The production generator and canonical Racket authority remain unchanged
by review `review-ce68771fbbf9aaae` (generator SHA-256
`b69551503d76981fef814186d22a507c5dea6541e0ce96f666ca67a9683d7d15`,
canonical normalized rule hash `d006d6b4ed8b`).

## Current proposed extension

`workspace/parametric/threshold_variant.py` fixes one strict threshold from
`1/3`, `1/2`, or `2/3` per episode. The `1/2` program preserves the exact
canonical Racket text. All demonstration/query labels execute in Racket;
the Python mirror is only an additional agreement check.

The original examples have density gaps and cannot distinguish these three
settings. The prototype therefore supplies exact boundary lines on both axes,
with 18/24-cell dimensions, randomized placements/colors/noise, and two or three
strong lines. Every strong line has a hole, so the strictest setting still
requires completion. Consecutive samples vary line counts to prevent a fixed
top-K rule from explaining the standard three-demonstration lessons.

Demonstration and query counts are independently configurable (1–12 and 1–16).
The standard command exports three demonstrations and four distinct queries for
each setting. Input sampling does not depend on the threshold. The declared
Racket teaching check eliminates the other two thresholds and the chosen
inclusive-boundary rival using demonstrations only. A separate bounded audit
at seed `20261023` also eliminates row-only, column-only, no-completion,
no-recoloring, and all fixed top-K row/column counts in `0..6`; one correct rule
survives among 57 hypotheses for each of the three episodes. This is finite
family evidence, not a uniqueness theorem for arbitrary programs.

`workspace/parametric/export_challenges.py` writes exact shared public-projection
bytes under content-only SHA-256 filenames, rejects duplicate visible payloads
and overlapping inputs, and keeps all private labels/settings/programs separate.
Its verifier checks export integrity; `--replay` additionally matches current
source identities and executes retained labels. Replay does not regenerate
seed/sample-index lineage or independently recheck teaching metadata; focused
core tests and the semantic audit exercise those separately.

Complete examples and source-bound evidence live in
`workspace/parametric/evidence/`; usage is in `workspace/parametric/README.md`.
The source-bound manifest reports reviewer evidence, not variant approval.
Canonical compatibility includes all four original pairs, new samples and
transposes, and an odd 15-by-17 majority witness.

## Limits and next useful work

This is an opt-in prototype, with a deliberately bounded 18/24-cell teaching
sampler and one marker color. A single demonstration identifies its declared
threshold family but does not establish broader shortcut resistance. Retain
three demonstrations for the audited standard lesson. No measured model or
training benefit is claimed. A future extension can widen input geometry only
with new demonstration-only witnesses and matching Racket labels. Production
API changes, variant approval, and training admission remain separate decisions.

Imported associated notes retain their original evidence in
`evidence/associated_notes.jsonl`.
