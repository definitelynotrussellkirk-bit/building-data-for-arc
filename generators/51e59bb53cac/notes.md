# Working notes: 51e59bb53cac

## Current decision

Keep the approved canonical generator and canonical Racket authority unchanged. The missing support work is now a **proposed task-local parametric prototype** with one hidden episode parameter:

- `swap_scope=interior` is the exact canonical/default rule: infer the two role colors inside the sole gray frame and swap those colors only in the strict interior.
- `swap_scope=exterior` preserves the same frame detection, color-role inference, palette, and swap operation, but applies the exchange only strictly outside the frame rectangle.

The setting is selected before input sampling and remains fixed across every demonstration and query. Inputs are sampled independently from the existing approved generator; the prototype fails rather than cloning or silently omitting requested pairs. Demo and query counts are separate (`1..32`).

## Retained implementation and evidence

Exact Racket programs are materialized under `workspace/parametric/rules/`. `interior.rkt` is byte-for-byte the canonical program; `exterior.rkt` is checked as the single strict-interior-predicate substitution. All labels run through the matching Racket program and are independently compared with a Python mirror.

The seed-17 retained bundle has both settings, two demonstrations and four distinct queries per episode, six unique inputs per episode, canonical parity on 8/8 ledger pairs, and 62 recorded Racket executions. Demonstrations alone leave only the selected setting after comparison with `interior`, `exterior`, global-swap, and identity rivals. Public files contain only visible demonstrations and query inputs, use SHA-256 IDs over those exact bytes, and are emitted in public-ID order; settings, seed, programs, query answers, and setting maps remain private.

Evidence: `checks/parametric/swap-scope-seed17/summary.json`. Focused prototype tests pass 6/6; the portable selected-task suite passes 63/63.

## Harness corrections

The existing selected-task test used a checkout-relative root and exact raw Racket formatting. It now uses `reviewer_support.find_root(__file__)` and compares normalized rule text, matching the existing normalized rule-hash contract. These are test portability corrections only; canonical source and labels are unchanged.

## Limits and next useful action

This is bounded prototype evidence, not production integration, variant approval, or training admission. Identifiability is finite over four declared rivals and the recorded seeds/current generator domain, not a proof against every alternative rule. A maintainer can next decide whether `exterior` is a desirable family member; only after that decision would broader seed coverage or a production parameter API be warranted.
