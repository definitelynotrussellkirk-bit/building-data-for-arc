# Current authoring decision
A full-height separator divides source templates from a marked rectangular frame.
For each source color, agree BOTH opposite row markers and BOTH opposite column
markers. Translate the template's bounding-box center to every Cartesian-product
intersection. Erase only templates with valid destinations; unmatched sources stay.
Paint only blank cells, so frame markers and earlier source templates win overlaps.
Supplied test 1 distinguishes source-order priority from numeric-color priority.

Build: `overlap_priority=source_order` preserves this reference exactly;
`largest_first` first matches and measures every eligible template, then sorts its
placement records by occupied area (source order resolves ties) before painting.
The causal foil ranks by bounding-box area instead of occupied area. Preserve
paired-marker agreement, all crossing destinations, original holes, clipped copies,
source deletion, and untouched unmatched shapes. Include competing sparse/dense
shapes, repeated markers, mismatches, boundary contact, both priority orders and
substantive 30x30 queries. Inputs are setting-neutral.

Plan: execute all five supplied labels; build standalone input sampler and native
adapter; regression-test overlaps and paired markers; use bounded demos-only
teaching selection against declared rivals; run finite audit, protected preflight,
public/private projection tests and a source-bound wrong-size causal replay.
This is unapproved authoring; owner registration and acceptance remain pending.

## Verified handoff and limits
- Exact reference: all 3 original train and 2 supplied test labels reproduce in protected Racket.
- 24 task-local tests pass, including relocation, mismatched opposing markers, source-versus-color overlap priority, occupied-area reversals/ties, and dense 30x30 content.
- The 32-seed audit covers 192 lessons / 1,472 pairs and 17 named Python rivals; every rival is rejected by visible demonstrations.
- Initial two-way overlaps left inseparable fixed priorities. Three-way teaching overlaps repair this; selection is bounded to 128 attempts, uses only two demonstration inputs/labels, and never inspects queries. Over tested seeds 0..31 it required at most 10 rejected draws.
- Area order now reverses and ties between 5x5 sparse templates, 3x3 templates with 4/5/7/8/9 occupied cells, and 2..5-cell bars. Neither dense appearance nor smaller/larger bounding box substitutes for occupied-area measurement.
- The new sparse branch initially reduced seed 24's max-case interior occupancy to 72; an additional repeated bar-marker row repairs it without weakening the >=75-cell check. The failed check and passing regression are retained.
- Preflight passes both settings on seeds 17 and 43, two demos and four queries. Protected parity also verifies 40 pairs at six demos on seeds 0 and 31.
- The 30x30 largest-first causal witness ranks by bbox area instead of occupied area: 9 final cells change; fresh protected replay agrees. Sixteen shuffled one-query exports pass identity/leakage checks.
- Grammar: zero interior background, left palette, full-height separator, rectangular edge-marked right frame; even bbox centers use floor. The source-order rule preserves original occupied destination cells and unmatched templates. Synthetic templates are a bounded structural family, not every possible parent input.
- Finite seeds/rivals are not universal uniqueness. Owner registration, exact-source native qualification and acceptance remain pending. All evidence is under checks/public_eval_247ef758/.

## Current repeated-parent reconciliation

Retain both exact accepted programs, current demo-only teaching gate and unchanged ordinary generator. Incoming c50 is identical; earlier 7d adapter is superseded. Add stable private complete-query shuffle and 1..4 prefix support with strict allowlist public views; default remains four queries. Current evidence resides in evidence/repeat-fourth-union. Private native acceptance and root publication are separate.
