# Working notes: 241567a35764

## review-d122508d0079b17e — 2026-10-25

- **Base defect and repair:** version 2.1.x selected marker pairs from vector geometry alone, so the control-transformed template could fit at neither marker and the canonical output could contain zero stamps. Version 2.2.0 computes the transformed footprint before selecting markers, requires both the 7 and 8 anchors to fit, and makes `self_check` enforce at least two fully in-bounds forward stamps. The retained zero-stamp input is now a regression test.
- **Canonical preservation:** `workspace/parametric/canonical.rkt` is byte-for-byte the catalog executable canonical program (`dbb2464b1f776e8d93a10f5c4262f05a929a2dcd0a61292bc926758c77c02c18`). No canonical authority or approval flag changed.
- **Native family:** default `forward` preserves the canonical control-derived template transform and forward stamping. `bidirectional` derives the same normalized transformed footprint, then stamps it along both the 7→8 vector and its inverse; Step B cannot be evaluated without Step A’s footprint.
- **Teaching repair during self-review:** the first bounded audit found seeds 4, 7, 10, 12, 13, 18, 23, and 27 allowed an `ignore_flip_control` rival to fit both minimum demonstrations because the flipped template was mirror-symmetric. The sampler now skips only flip-invariant template/control combinations, and a 32-seed minimum-prefix regression protects the distinction.
- **Teaching/self-review:** the repaired audit covered 192 episodes, 1,472 visible pairs, 192 declared-rival certificates, 768 sequential public turns, 192 substantive 30×30 checks, and 65 protected-Racket evaluations with no failures.
- **Evidence status:** authoring preflight and protected causal replay passed on the exact source. Public projection/export/first-turn invariance passed. These are reviewer checks only; owner source review, native qualification/acceptance, and any training admission remain pending.
- **Next owner action:** apply the returned patch, verify the live source binding, run fresh native qualification and acceptance, then decide training admission separately.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/241567a35764/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
