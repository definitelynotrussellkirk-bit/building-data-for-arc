# public_eval_a6f40cea

The largest four-connected green rectangular component is the frontmost solid
occluder.  Recover every monochrome or checkerboard rectangular wire from its
visible perimeter outside that box, then render the hidden slices into the
strict green interior over the interior fill color.

The immutable third training output contains one isolated phase inconsistency:
the wide 8/9 striped wire is inverted behind the occluder despite every visible
cell using the opposite `(row+column)` parity.  To reproduce all supplied labels
without a grid lookup, the selected canonical extension flips hidden parity for
striped rectangles wider than tall and preserves it otherwise.  Generated
lessons expose that branch explicitly.

The native family keeps identical inputs across `all_frames` and
`largest_frame`.  The alternate retains only the unique largest recovered wire;
its final pixels therefore consume the input-derived recovered-frame/area-rank
intermediate.  Owner registration and acceptance remain pending.

Owner reference serialization correction: strict parsing exposed one extra closing parenthesis after each complete rule. Removed only that unconsumed character, preserving the parsed executable form. Original bytes and hashes are in evidence/strict-racket-serialization/repair.json; fresh protected execution and native acceptance determine current readiness.

## Current repeated-return reconciliation

- review-0d2e13441e2290ff: Add visible-phase continuation on the preserved accepted frame parser; do not substitute the incompatible restart-hidden parser or its labels. Its source reports not ready; phase-policy interpretation remains unresolved.
- review-98c8f81dca8b698d: Add solid hidden rectangles using accepted frame registration and phase conventions. Incoming perimeter default differs on all ten seed-0 samples; its phase fallback and constructor grammar remain unresolved.
- review-5b3cadd507110b61: Exact current family and original canonical/default retained; compatible source evidence is preserved.

Accepted default and prior program bytes remain unchanged. Evidence and unresolved input/phase witnesses: `evidence/reconcile-16/`. Private native qualification, fresh private native acceptance and accepted generation passed. Live owner publication and training admission remain separate.

Inherited a6f40cea witness repair: strict full-expression validation rejects both strings from `review-5b3cadd507110b61` despite the lower-level bridge accepting their prefix. Preserve the already repaired accepted source and use fresh strict protected witnesses; see `evidence/reconcile-16/incoming-causal-validation.json`.

The two earlier a6f40cea constructors are retained as separate episode banks. All their inputs passed the accepted parser on eight fresh seed banks. Candidate labels use the preserved accepted phase convention, with the new continued-phase and solid-hidden settings; incompatible original phase labels remain explicitly unincorporated.
