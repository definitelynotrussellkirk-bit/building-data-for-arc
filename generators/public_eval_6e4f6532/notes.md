# Public creation notes: 6e4f6532

## Rule and parameter

The canonical rule removes uniform guide strips from component extraction,
identifies azure movers with maroon anchor cells, matches each mover to the
detached maroon target of the same anchor geometry, and infers a rigid D4
transform from the mover's coloured tabs and the matching guide-line colours.
It erases each source and stamps the complete transformed object over its target.

The native family adds episode-fixed `orientation_mode: toward | away`, with
`toward` as the byte-identical canonical default. `Away` reverses only the
inferred target-facing guide side before transform selection. Both settings use
identical inputs. The object/target match and D4 transform are the intermediate
consumed by the final erase-and-stamp stage.

## Constructive domain

The sampler emits six demonstrations and four queries, supports prefixes of 2–6
demonstrations and 1–4 queries, shuffles query presentation independently of
query ordinal, and includes a 30×30 query. It uses four outer two-cell guide
strips, two asymmetric movers with different anchor cardinalities, detached
maroon targets, collision-free separated quadrants, seeded palettes, and all
eight D4 branches. Arbitrary repeated-key assignment and general internal guide
networks remain outside the constructive sampler, although the general canonical
rule executes the official internal-divider examples.

A construction regression test preserves the case where destination jitter could
merge a target with a source object. Targets are now placed in separated
quadrants by construction rather than accepted through retries. The first two
demonstrations also use distinct backgrounds, rejecting a fixed-background
shortcut.

## Current packet evidence

- `checks/public_eval_6e4f6532/preflight/`: protected-Racket authoring preflight
  passed all four official labels and four 2-demo/4-query jobs. This is not owner
  qualification or acceptance.
- `checks/review-800deaecef69f120/6e4-tests-final.log`: 32 focused tests passed.
- `checks/public_eval_6e4f6532/audit/audit.json`: 64 protected Racket evaluations
  across two seeds, both settings, and eight authored rivals. Every rival was
  rejected by the first two demonstrations; there were no invalid or unresolved
  candidates.
- `checks/public_eval_6e4f6532/causal/witness.json` and replay: replacing the
  toward-guide D4 transforms with opposite-guide transforms changes 10 cells.
- `checks/public_eval_6e4f6532/export/`: 16 one-query public challenges passed
  saved-file conformance and 16 hidden-field byte-invariance mutations.

These checks are finite rather than a universal proof. Owner registration,
source review, native qualification, and acceptance remain pending; no production
authority or training state is changed here.
