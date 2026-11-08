# public_eval_dfadab01: current authoring decision

**Reviewer-ready prototype; owner registration, native qualification and acceptance pending. Training admitted: false.**

## Rule and family
Expand nonlegend code colors 2/3/5/8 into the fixed 4x4 square/ring/diagonal-block/X glyphs; discard exemplar pixels and clip edge stamps. A southeast code next to a matching exemplar is a legend label. Match occupied exemplar pixels, allowing a genuine target in a blank exemplar corner.

finish_rule=decode preserves reference.rkt exactly. finish_rule=highlight_largest first decodes every marker, then computes multicolor eight-connected components and recolors the largest component 9. The sampler has a unique largest component; outside that grammar ties use top-left discovery order.

## Decisions and repairs
Post-decoding connectivity was chosen instead of a cosmetic palette/rotation variant. Opposing minimum demonstrations make three square frames (36 painted cells) beat four smaller symbols (32), and five smaller symbols (40) beat the frames, separating painted mass from marker count and fixed glyph choice. Legend, clipped-anchor, transposition and mixed-symbol cases are retained.

Resolved integration defects: use the shared canonical public-byte serializer (including its newline), validate identifiers against the bytes actually saved, reject duplicate views before writing, and emit the exact protected-Racket causal-witness header accepted by the native validator. Regression tests cover the writer contract. The initial relocated-generator test failure was also repaired with an adjacent-file import.

## Current evidence
The final protected authoring preflight matches all **5 supplied original labels**.
It runs both settings at seeds 17 and 43 with two demonstrations and four queries.
Fresh replay reproduces preflight.json, execution.json and original-pairs.json byte-for-byte.
These are authoring receipts, not owner qualification.

The final audit runs eight episodes (both settings, seeds 0,17,43,101),
136 protected-Racket audit evaluations, a 640-scene sampler sweep,
and 160 count/prefix requests. The audit counter excludes the additional causal
counterfactual and two independent protected replay evaluations.
The source-bound wrong-intermediate witness changes **53 cells** in its 30x30 query;
the native static witness validator and strict single-expression parser both accept it.
The exact-byte official export checker validates 16 single-query files with zero findings;
private-metadata/future-query/count invariance is separately exercised by the audit.

Each family supports independently selected 2–6 demonstrations and 1–4 queries;
controller presentation shuffles the complete four-query bank before truncation.
Only a single `challenge` is model-visible. Never expose private bundles or directory listings.
Both task suites together pass **58 tests**. The legacy `task-tests` wrapper still exits 1
with `Unknown puzzle` because these public IDs are not registered; that failure is retained,
not treated as a pass. No catalog, canonical authority or approval files were modified.

Author self-review was performed; no independent reviewer was available.
The sampler deliberately uses a lane/chain grammar, not arbitrary marker arrangements. Its 640 sampled scenes contain 635 distinct inputs across seeds, while episode inputs remain distinct. All 13 mode-specific rival slots are rejected at the four audited seeds; this is not uniqueness against arbitrary programs.

## Evidence and next action
Final evidence is under `WORK/checks/public_eval_dfadab01/preflight-final/` and
`WORK/checks/public_eval_dfadab01/audit-release/`. Reproduction commands are in `workspace/parametric/README.md`.
Owner: reconcile any overlapping parent return, review the inferred grammar, register source
with the literal RULE_TASK_ID, refresh the native inventory, then run unchanged native
qualification and acceptance. Do not train on these prototypes before that gate.

Owner worker API correction: use the existing worker input/findings contract. Earlier author checks used the incompatible return convention. Reference programs are unchanged; owner preflight and native acceptance determine current readiness. See evidence/owner-base-api-repair.json.

## Current repeated-return reconciliation

Full semantics and overlap sampler incorporated; exact earlier return baseline reconstructed, with all executable source hashes matched before applying the delta. Exact incumbent programs and original lane sampler retained.

All original accepted programs and defaults remain exact. Two to six demonstrations and four shuffled, sequential private queries are supported. Finite rival checks and sampled protected labels are bounded evidence. Fresh private native qualification and acceptance re-execution passed. Live publication and training admission remain separate. Source-bound decisions and witnesses: `evidence/reconcile-18/`.
