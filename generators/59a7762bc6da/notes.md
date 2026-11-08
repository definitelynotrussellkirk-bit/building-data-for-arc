# Working notes: 59a7762bc6da

## Current decision

Retain the canonical generator and authoritative rule unchanged. The opt-in
native prototype is in `workspace/parametric/`; its episode-fixed parameter is
`gap_policy = keep | bridge_once`, default `keep`. The default returns the exact
931-byte canonical source (rule hash `108478b11257`). The alternate fills
one-cell diagonal gaps simultaneously, then recomputes the original
8-connected-component/diagonal-run rule on that intermediate grid.

Gap filling can join formerly separate pieces, create a qualifying run, and
recolor an attached branch. This supplies a changed-state dependency beyond
renaming feature extraction and painting as two steps. A native source-bound
`skip_a` witness compares the alternate against the canonical program on a
qualified example. Final qualification and witness records are packaged under
`checks/59a7762bc6da/`; owner acceptance remains a separate mandatory action.

## Teaching and current evidence

The first two demos constructively distinguish both slopes, whole-component
propagation, threshold three versus exact length, larger dense negatives,
orthogonal gaps and a once-versus-iterative cascade. Shared episode reflection
preserves the complementary slopes. Additional demos are optional variation;
they do not repair an ambiguity in the mandatory prefix.

`workspace/parametric/evidence/current/summary.json` binds the actual authoring
sources. The protected-Racket audit passed 12 jobs, 92 demo/query labels,
62/62 finite rival refutations across four two-demo prefixes, eight boundary
labels and all four canonical pairs. The 120-request construction census had
zero failures. That census checks construction, counts, novelty, prefixes and
paired inputs in Python; it does not independently execute every label.

The focused native suite passed 33 tests. Independent source review found no
material defect in the sampler, rule composition, teaching construction or
single-query projection; it did not rerun the protected audit. Finite rival
coverage is not a claim of universal uniqueness or all-seed correctness.

## Sampling and consumer limits

The prototype supports 2–6 demos and independently 1–4 queries; request three
demos and four queries for ordinary use. Seed and count types are strict.
Scenes span 16–30 rows and columns, with distinct dimension pairs guaranteeing
within-episode novelty and count-stable prefixes. Setting-independent geometry
permits matched-input comparisons. Explicit 16×16, 16×30, 30×16 and 30×30
stress scenes contain substantive content across all quadrants and boundaries.
These dimensions belong to this separate prototype; they are not newly
advertised production-generator overrides.

Eight retained public files each contain demonstrations plus one query input,
and use SHA256 names derived only from visible bytes. Their ordering map,
settings, seeds, programs and query answers are private. The existing consumer
must reveal one selected view per turn; the first matches single-query use.
No controller or training loop is included.

## Next owner action

Integrate the assigned delta, inspect the current native qualification and
causal replay, then requalify and accept the exact live bytes through the native
promotion flow. Reviewer-ready evidence does not itself accept this family or
admit training data. Preserve the imported associated semantic note in
`evidence/associated_notes.jsonl`; there is no unresolved canonical-rule repair.
