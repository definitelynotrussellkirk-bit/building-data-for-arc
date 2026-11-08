# Working notes: 02a33ab58da6

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/02a33ab58da6/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Parametric turn-policy proposal — review-5b7b5236332485e6

`workspace/parametric/` now exposes one episode-fixed parameter,
`turn_policy=toward_center|away_from_center`. The default program is the exact
canonical rule. The constructive sampler reserves both perpendicular tails for
every motif and gives every demonstration both clockwise and counterclockwise
center-directed witnesses, so fixed-turn and no-move shortcuts do not survive.
Inputs are matched across settings, counts are 2–6 demonstrations and 1–4
queries, and the fourth query is a 30×30 scene with eight long motifs and source
contacts on all four boundaries.

Public turns use only visible demonstrations and the current query input; first
turn bytes are identical between one-query and four-query requests. The bounded
adversarial pass retained regressions for merged-ray collisions, incompatible
boundary anchors, malformed settings, tampered labels and duplicate inputs.
The existing canonical test now discovers its own source tree with
`reviewer_support.find_root/canonical_path`, fixing copied-runtime portability
without changing production generator or Racket behavior.

Fresh evidence: 16 focused parametric tests and all four canonical pairs passed;
protected Racket executed five programs over seven inputs (35 evaluations).
The native inventory SHA-256 is
`3158b8a7374d894cafb78dbe2831e39aea3636aa7b95ffb9127ae4d8f26e6dca`.
The exhaustive pre-existing generator suite exceeded the harness window after
19 completed tests, so no full-suite claim is made. This proposal is not owner
qualification or training admission.
