# Working notes: 3031e2ee53d1

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current native parametric proposal — reflected continuation

`workspace/parametric/` now contains a native adapter for `edge=linear|bounce`.
The default is the exact canonical Racket program; the alternative reflects the
whole repeating motif at horizontal boundaries with preserved orientation and
overshoot. The input-derived period, drift and union envelope determine when
reflection occurs. A protected wrong-intermediate witness replaces the union
with first-row bounds and changes 23 output cells. Canonical generator bytes
remain `204b0367fff79875dab758229d75d18820f274fbf20bf8cd79bc9d5329e1c4ed`.

Ordinary episodes contain three demonstrations and four novel queries; the
adapter supports 2–6 demonstrations and 1–4 queries with matched input streams
across settings and count-independent query identities. The separate grammar
includes substantive 30×30 outputs, not padded small examples. The public
projection reveals one query and hashes only visible bytes. No controller or
training activation is added.

Self-review found a real phase-reset ambiguity at seed 12: the original first
two demos had heights 4 and 6 (complete periods), so a prefix-preserving rule
that resets phase fit both but failed query 2. The first demo now has height 5;
the regression went from two failing cases to passing. Preserve the original
lesson in `workspace/parametric/evidence/current/phase-reset-before.json` and
its separate alternative-answer candidate; do not substitute repaired demos.

Verified: 109 task tests; 24/24 bounded sampler draws; native protected boundary
checks at six demos and the maximum seed; six two-demo lessons against nine
named rivals (54 combinations, all refuted); native qualification for both
settings on seeds 0 and 17; and protected causal replay. Reports and source
inventory are in `workspace/parametric/evidence/`. Return receipts are
`checks/3031e2ee53d1/qualification/` and `checks/3031e2ee53d1/causal/`.
This is reviewer **ready**, with owner exact-source qualification/acceptance
after integration still pending. Finite rival checks are not universal
identifiability or measured learning benefit. Training admission stays false.

## Current review decision — strict public scalar boundary

The selected defect was reproduced on source SHA-256 `ffd0c42beafdd7e53ec20514b897929940d59190fe80ba853f1841326ad31fdf`: `generate` and `schedule_profile` accepted coercible public scalars (`True`, floats, strings) and accepted a negative `sample_index`, creating schedule aliases. The repair adds one exact public-call validator used by both entry points: `seed` and `sample_index` must have exact type `int`, and `sample_index` must be nonnegative. Valid integer behavior is otherwise unchanged; the repaired source is SHA-256 `204b0367fff79875dab758229d75d18820f274fbf20bf8cd79bc9d5329e1c4ed`.

The task test was also made portable by resolving canonical data through `reviewer_support.find_root` and `canonical_pairs`; the prior relative `Path.parents` lookup failed in the staged copied runtime. TDD evidence is retained at `checks/scalar-red/` (14 expected failures before the production edit) and `checks/scalar-green/` / `checks/task-tests/` (23/23 passing). The source-bound adversarial probe compared 23 valid calls byte-for-byte against the immutable baseline, rejected all 14 invalid calls across both public entry points, and matched the unchanged Racket authority on four representative grids (`checks/main-scalar-validation/report.json`). Focused lint and self-check passed. The optional broad `rule_smoke` wrapper was interrupted by the outer command boundary; it is not reported as passing, and the narrower live-Racket parity probe is the retained rule evidence. `RULE_HASH` and the reference rule were not changed.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-7c254afacd57078d:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `ffd0c42beafdd7e53ec20514b897929940d59190fe80ba853f1841326ad31fdf`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source-bound repair explicitly addresses this finding; focused checks and Racket parity are reviewer-reported, not a new owner battery. Current task notes and retained integration record specify scope and finite limitations.

### Assessment or prior finding

## 3031e2ee53d1

**Reproduced defect: coercive public call scalars.**  Current audited source
SHA-256 is
`ffd0c42beafdd7e53ec20514b897929940d59190fe80ba853f1841326ad31fdf` and
rule hash is `e9b80003c95f`; no audit-target source was modified.

The generator accepted all seven invalid calls tested: `seed=True`, `1.0`, and
`"1"`; `sample_index=True`, `1.0`, `"1"`, and `-1`.  Every call returned a grid
accepted by the target's `self_check`.  Its `schedule_profile` also coerces
sample index via `int()`, making boolean, float, string, and integer `1` aliases
of the same curriculum position.

The exact accepted calls, grid hashes/shapes, schedule aliases, source hash, and
limits are in `checks/audit/3031e2ee53d1/report.json`; the runnable probe is
`checks/audit/3031e2ee53d1/probe.py` and the final log is
`checks/audit/3031e2ee53d1/probe.log`.

**Limit.** This audit covers scalar call validation only.  It does not challenge
the Racket transformation or make a claim about output semantics.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-7c254afacd57078d-v0001/audit_assets.json), manifest SHA-256 `15a8600a51b8b2adf09296b4a10c4cff08b7e4046b82302ed9f7f716a909d4ca`.
<!-- arcpuzzles-current-audit-assessment:end -->
