# Review: 22d1f016cb3d
**Assignment:** `review-b8268a1423152fed`; prototype `1.0.0` → `1.1.0`.
**Defect → repair:** palette-revealing filenames and fixed 4/1 counts → visible-byte SHA-256 exports, independent 1..32 demo/query counts, default 4/4, and globally distinct inputs.
**Label authority:** `build_episode` now derives every label from matching Racket execution, with no Python fallback.
**Source:** prototype SHA-256 `8fe30f9348808f17f81a974b6043bd6f0e41b9300b2a3a62a467422ea6f6e59a`.
**Checks run:** 36 focused tests passed; both 4/4 episodes executed (16 labels, 8 demonstration-only query-identifiability checks); one 32/32 episode produced 64 distinct Racket-labelled pairs.
**Export checks:** exact written-byte hashes, sorted opaque IDs, private-metadata/query-answer invariance, collision/duplicate refusal and private-report separation passed.
**Canonical changes:** none; production generator SHA-256 `26f3491ab54d2e4cd38590da33f59a567f140c2e8a342a1dcfd5ab59f701abbd`, both retained Racket programs and canonical ledger unchanged; canonical rule `2219db85ca5f`.
**Tickets:** 7c2a3ec6c4fb yielded two lawful color-signature-rival refuters; 70c1f7fc5056 reproduced its existing documentation/authority mismatch and five ignored controls.
**Limits:** prototype only; two declared palette rivals, bounded seeds and sampling; unchanged production batteries not rerun. No variant approval or training admission.
**Acceptance:** routine prototype repair; existing peer audit remains unresolved. Current manifest validates as `current`, with `variant_approved=false`.

## Evidence and rerun

- `checks/parametric-final-v2/tests.log`, `evidence.json`, `count-boundaries.json`, `manifest-validation.json`, and `unchanged-authorities.json` retain the final scoped evidence.
- `checks/parametric-before/regressions.log` retains the pre-repair 15 failures; `reference-isolation.log` retains two additional pre-repair failures. They are expected failing regressions, not unresolved final failures.
- `checks/parametric-final-v2/verify_export_limits.py` is a reusable exact-byte export and 32/32 support verifier.
- Ticket source bindings, runnable probes and actual results are under `checks/tickets/ticket-7487737a40559cfa/` and `checks/tickets/ticket-aada123b5e5fd083/`; the reproduced safety finding is described in `AUDIT.md`.
- Exact commands and scopes are in `RESULTS.json`. The task-local prototype README gives the portable four-query command. Use fresh output directories.

The old setting-named examples remain inherited private historical fixtures because baseline deletions are prohibited. Only `examples/public/` is the current shareable example directory, with content-derived filenames. The previous evidence manifest is preserved under `evidence/reviewer-reported/prior-manifest.json`; the current manifest binds only the newly validated prototype assets. This updates authoring evidence, not approval.
