# Working notes: 1314f4ccf5cc

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/1314f4ccf5cc/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-24 parametric review

- Built `workspace/parametric/` with episode-fixed `footprint=cardinal|diagonal`.
  The cardinal program is the byte-exact selected authority. Both settings use
  identical matched inputs, 2–6 demonstrations, and 1–4 prefix-stable queries.
- The sampler constructs fragments that have one lawful cardinal-plus center and
  one lawful diagonal-X center; outputs, not input statistics, identify the rule.
- Adversarial placement found that a motif touching a boundary admitted a second
  clipped diagonal footprint. The placer now reserves a one-cell frame, and the
  retained seed-0 regression verifies one candidate per rule for every fragment.
- The fourth query is a 30×30 dense-noise scene with eight completion motifs.
  Qualification evidence executes both settings through protected Racket and
  checks demonstration-only finite-survivor identification and public projection.
- The packet-native broad task-test census was attempted twice and exceeded ten
  minutes in the unchanged distribution test. Focused source-bound checks passed;
  this timeout is reported rather than represented as green.
- Prototype remains proposed only: no owner acceptance or training admission.
