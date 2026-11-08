# Working notes: 67504673cd7c

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review repair — 2026-10-24

Baseline generator SHA-256 `c49446ccf63985c01f747d3d865f5f3535569779dd072265a55f59418272d39a`
accepted exact controls but drew all semantic values from a separate RNG. A
request for two or five anchors could return the same three-anchor scene; the
fallback could also return a partially placed scene. It lacked the selected
rule hash and semantic teaching contract, and its hard/medium defaults rarely
reached a canonical `(height, width, palette-size)` profile.

Version 2.1.0 pins `RULE_HASH = 35ef1014dd1e`. The retained exact axes are now
only `grid_h`, `grid_w`, `num_anchors`, and `template_size`; every one is strict,
keyed and recovered from returned pixels by `observe_overrides`. Compact
connected templates use a constructive disjoint lattice placement, so all
boundary combinations complete exactly or fail loudly instead of truncating.
A periodic source-independent prior anchors all difficulty bands to public
profiles while leaving alternate draws broad. `self_check` validates one
4-connected template, singleton/distinct markers, in-bounds disjoint stamps,
and template separation.

The Python rule mirror and `anchors_only` rival give an executable semantic
contract: the multi-cell-template witness fired in all 600 strict census draws,
and all 60 checked witness/rival comparisons disagreed under Racket. No
canonical Racket source or selected base authority changed. Final generator
SHA-256: `b8c7073679cf308e863e70db5b363b3b31187a30f7c8168ab760e46ae234fec2`.
Focused evidence is under `WORK/checks/67504673cd7c-*` in the return.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-e7912a4265cfdbc9:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `c49446ccf63985c01f747d3d865f5f3535569779dd072265a55f59418272d39a`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted sourceb8c7073679cf308e863e70db5b363b3b31187a30f7c8168ab760e46ae234fec2 consumes exact axes and uses constructive placement that cannot silently underfill anchors.29tests, strict semantic and46,980override draws are reviewer-reported, not owner-reexecuted.

### Assessment or prior finding

## 67504673cd7c

**Reproduced defect — exact anchor-count override is ignored.** Generator
SHA-256:
`c49446ccf63985c01f747d3d865f5f3535569779dd072265a55f59418272d39a`.
At seed `0`, sample index `0`, difficulty `medium`, both `num_anchors=2` and
`num_anchors=5` are accepted, pass `self_check`, and produce the identical
three-anchor grid SHA-256
`321b117989376169cf30a3b17ba5bf20d8bcf4799e1b7688086d33452b278796`.
The exact grids, anchor coordinates/colors, and invocation metadata are in
`checks/audit/67504673cd7c/override_noop.json`.

This input belongs to the documented generator domain and directly contradicts
the advertised exact axis. The linter separately reported a missing `RULE_HASH`;
the profile floor found only 1/60 exact canonical profiles, with zero medium- and
hard-band support; and the semantic-contract stage found no required contract.
Evidence is under `checks/audit/67504673cd7c/`. No fix was made.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-e7912a4265cfdbc9-v0001/audit_assets.json), manifest SHA-256 `fba00b56055f762a9937cfd898bb926ac8635f73c68f5a78df43bfad4d8eec31`.
<!-- arcpuzzles-current-audit-assessment:end -->
