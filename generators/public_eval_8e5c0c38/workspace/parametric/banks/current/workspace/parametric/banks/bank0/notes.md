# Public parent 8e5c0c38 — current authoring notes

Unapproved evaluation-origin source. No owner registration, acceptance or training admission.

## Design and implementation plan

The original examples preserve the modal background and remove each foreground
color's pixels that lack a counterpart across its inferred vertical symmetry
axis. Infer the doubled axis coordinate maximizing retained same-color pixels;
use the smallest coordinate on ties. This explicit tie convention matches the
supplied gold, including the small green shape in test 0; finite labels do not
prove it is the only plausible tie convention.

The episode-fixed `symmetry_action` is `trim` (canonical) or `complete` (retain
all pixels and fill missing reflected background pixels). Both first infer the
axis from the original input; completion does not iterate inference on its output.
This keeps the original per-color shape recognition rather than substituting a
fixed canvas/bounding-box axis. A competing orientation change was considered,
but completion keeps the public parent's vertical-symmetry reasoning intact.

- [x] Author and execute the general default on all supplied train/test gold.
- [x] Build a keyed, bounded multicolor sampler, exact default and alternative,
      native adapter and contract; independently support 2–6 demos and 1–4 queries.
- [x] Add tests before code for original labels, boundary/typing/prefix behavior,
      minimum teaching contexts, source-independent public views and 30x30 stress.
- [x] Self-review finite executable rivals, run protected authoring preflight,
      and retain a source-bound wrong-axis causal witness and privacy checks.

Work is in a newly extracted isolated packet. No git repository was supplied;
the packet's source-hash baseline and delta packager provide the change boundary.

## Verification and current limits

All four official labelled pairs (two demonstrations and both test gold grids)
pass the general protected-Racket reference. 22 target tests passed; the same
22 also passed from relocated test files (44 executions, not 44 distinct tests).
The relocation check first failed and was repaired with reviewer_support root
and canonical-pair resolution.

Final source-bound preflight: `checks/public_eval_8e5c0c38/preflight-final/`.
Final reusable audit: `checks/public_eval_8e5c0c38/audit-final/`. It covers 64
seeds, both settings and each demo count 2..6: 640 nested lesson views and
5,120 pair exposures. All seven finite rivals had no query-changing survivor.
The ordinary grammar has unique maximum-overlap axes: the rightmost-tie rival
is equivalent inside that grammar, not globally rejected. Original test 0
separately exercises the canonical leftmost tie.

Maximum six-demo/four-query labels passed protected Racket for both settings at
seed 109. An authoring-preflight 30x30 completion query changes 152 cells when each axis
is replaced by its noisy bounding-box midpoint. Its labels and independent
process replay passed (24 evaluations in the reusable audit, including replay).
Sixteen single-query public files passed structural/hash/privacy checks.

General grouping is by color rather than connectivity. The synthetic input
grammar has 2..4 separated colored silhouettes, random modal backgrounds, odd
and even axes, variable cores/noise and a substantive four-silhouette 30x30
case. Completion fills only reflected background pixels; it never overwrites
another foreground color. Counts, palettes and geometry are finite/synthetic;
this is not universal learnability or a measured training gain.

Author self-review only (no independent reviewer process available). No remaining
Critical or Important finding in the reviewed scope. Owner registration, review,
exact-source native qualification/acceptance and any training admission remain
pending. Public-parent provenance and shared authorities remain unchanged.
