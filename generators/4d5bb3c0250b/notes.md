# Current notes: 4d5bb3c0250b

## Intended rule

Partition the square input at every full nonzero separator row and column. These
lines form equal square blocks. Exactly one nonempty block has only one distinct
nonzero color; every other block has at least two. Return the complete unique
one-color block, preserving zeros and its original colors. The authoritative
Racket rule remains unchanged at rule hash `0bc50653fe24`.

## 2026-10-23 review repair

Baseline version `3.0.0` / SHA-256
`7c785bf42cc0baed745dcae4d17b02eb30513be354bbfa577f0ecb675adcd80e`
passed nine battery stages, failed defect lint, and had semantic/override
advisories. It silently accepted nonliteral scalar controls and unknown override
keys, represented incompatible equal separator/target colors only as unstructured
failures, and limited `distractor_colors` to 2–4 even though canonical distractor
blocks contain 2–7 distinct nonzero colors.

Version `3.1.0` / SHA-256
`268443a7bf130a55f9d1d6aca5767e0e820edc8bcef4de01d490867bd5be7c54`
now:

- validates `seed`, `sample_index`, `difficulty`, every declared axis, and unknown
  keys before generation; bools, strings, integral floats, and fractional values
  no longer pass exact controls;
- uses strict color draws and a structured two-axis rejection when separator and
  target colors coincide;
- restores the canonical distractor palette support to 2–7 colors;
- exposes a Python rule mirror, the strict lawful-manifold hook, a
  `target_not_top_left` witness, a `crop_top_left_block` rival, and a
  three-demonstration lesson-identifiability hook.

Minimal reproductions are retained in `counterexamples/strict-scalar-distractor-colors.json`
and `counterexamples/canonical-seven-color-distractor-support.json`; focused
regressions live in `tests/test_review_repairs.py`.

## Distribution decisions

The 78% prior on complete canonical linked profiles is unchanged. The remaining
lawful generalized profiles are unchanged. Target colors still appear in every
distractor palette, preventing a unique-output-color shortcut. The repaired
2–7 palette range is not arbitrary broadening: the four labeled canonical pairs
contain distractor blocks across that entire range, including seven-color blocks
in train pairs 0–1 and test pair 0.

`EXAMPLES_NEEDED = 3` is the minimum used by the lesson hook. The explicit rival
is deliberately small and falsifiable: demonstrations must include evidence that
the target need not be the top-left block whenever a held-out query would expose
that shortcut. This is finite evidence against one named rival, not proof of
unique human induction.

## Parametric extension

`workspace/parametric/` contains a separate **proposed, unapproved**
`selected_color_count ∈ {1, 2}` prototype. Setting 1 materializes byte-identical
canonical Racket source (SHA-256
`0bc50653fe240f5837696c7c20156315278dbb9f9cd295877e76d28799fb5dc5`);
setting 2 selects the unique block with exactly two nonzero colors. Each retained
episode fixes one setting across three demonstrations and four distinct queries.
This prototype does not alter the production rule or approval state.

## Verification and known limits

The final twelve-stage battery is all green, focused tests are 41 passed / 1
intentional skip, the strict 300-episode lesson census found 0 production or
rotation ambiguities across 1,200 pairs/rotations, and one production episode
successfully materialized three demonstrations plus four distinct Racket-labelled
queries. The task-test stage remains blocked before collection by the inherited
frozen root test's fixed-depth canonical path; duties prohibit editing that
fixture. Masked-query correctness for both reviewer solves is intentionally
unknown pending maintainer scoring.


## Current portable test limit

The inherited frozen fixture remains unchanged; its portable data-path preflight is blocked. The 41 focused passes and one intentional skip, including fresh replay, and the separate 12/12 battery are reviewer-reported; none upgrades the blocked aggregate task-test stage. Current source-bound receipt: `generators/4d5bb3c0250b/evidence/frozen-fixture-blocker-f13c91d5a95551cb/manifest.json`. The separate selected-color-count prototype remains proposed and unapproved.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/4d5bb3c0250b/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
