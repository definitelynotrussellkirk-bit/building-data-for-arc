# Current decisions: c4f6a0585dbf

## Canonical domain repair

The canonical `training:7df24a62` rule finds the color-1 source bounding box,
extracts its shape and color-4 ports, checks all D4 transforms and clipped
placements, and requires at least two visible ports. Every in-bounds port must
match 4; in-bounds shape cells must cover 0 or 1. Only original zeros become 1.
The authority remains byte-identical: rule hash `d401b3cd92ff`, program SHA-256
`34aea00434c1a498289ad35c068b9cca102078c262cc65b41c7b71871a563975`.

The existing source-bound audit `review-0697b52e64b4b855:v0001` showed that warm
palette overrides turn a planted stamp into an unintended identity example.
The retained seed-13/index-5 witness changes 0 cells under Racket, while the
same canonical geometry changes 10. Fix the input domain: keep port color 4,
reject every non-None `palette_kind` explicitly, remove palette texture aliases
and advertising, and reject noncanonical colors before degenerate early exits.
Legitimate `no_targets` and `full_grid` cases remain supported.

Keep VERSION `3.1.0` because it participates in the sampling seed namespace;
18 retained seeded layouts remain identical. Source SHA-256 moves from
`7a5a972f9b4d467461824bfef6840c59c0b278d96a1a7919c08010f7c5d0d68c` to
`0464aa6870b04b31a0bd705a2d6cd87c3bc21942a8a80fa39938904e31bc5f97`.
Imported review evidence and its baseline source identity remain untouched;
this repair does not itself resolve the owner's audit or grant approval.

## Proposed parameter: minimum visible ports

`workspace/parametric/port_threshold.py` exposes one setting per episode:
`min_visible_ports` in {2,3}. Setting 2 materializes the exact canonical program;
3 changes only the visible-port comparison. It never relaxes matching of an
in-bounds port. Both use three-port sources, positive full copies and clipped
two-port witnesses so the difference is taught visibly without removing the
original template-matching reasoning.

Independent train/test counts are 1..16; default 2/4. Seeds are exact integers
0..2**64-1, and attempts are bounded at 1..4096 (default 128). Exhaustion raises
rather than returning a short episode. Inputs are pairwise distinct within each
episode. Both matching programs execute in Racket on every retained scene;
the Python mirror only screens candidates and is checked against those labels.

The finite-family certificate selects compatible settings using demonstrations
only, then checks query prediction agreement. This proves identifiability within
{2,3}, not universal rule uniqueness. Public files use the shared exact visible
byte projection and SHA-256 identifiers, sorted by public ID. Private settings,
seeds, programs, certificates and query answers are separate. Duplicate visible
payloads fail before output creation. The writer projects generated episodes;
it is not an independent verifier for arbitrary caller-supplied private labels.

The retained seed-17 export has two demonstrations and four distinct queries per
setting, six unique inputs per episode, and query disagreement counts 8/8/13/6.
A separate seed-583 probe uses one demonstration and four queries per setting.
The deliberate teaching distribution and count bounds do not establish success
for all seeds or arbitrary canonical inputs. This is a proposed task-local
prototype, outside the production API and training admission.

## Reusable low-space packaging

`workspace/low_space/` supplies an explicit archive-backed read context plus a
CLI for the unchanged supplied return builder. The original ZIP digest, manifest
and each virtual byte are checked. Omission paths must be recorded before edits;
selected sources and frozen baselines cannot be virtual. Physical corruption,
symlinks, writes and deletion remain visible. The context is single-use,
thread-scoped, and restores Path methods on failure. It is not a full extraction
or a general filesystem monitor; no concurrent omitted-source mutation is allowed.
The helper README and its 17 tests document these limits.

## Verification and next action

The combined authored suite passes 40 tests: 10 canonical-domain, 13 parameter/
Racket/public-export, and 17 archive-overlay tests. Exact commands, source hashes,
old-code failures, matching Racket results, generated episodes and bounded
adversarial evidence are in the returned `checks/` tree and `RESULTS.json`.
The original return validator and fresh runtime-closure replay provide packaging
verification; see the final REVIEW and replay receipts for the observed outcome.
No full production battery or broad stochastic census is claimed.

Maintainer next action: review this source-bound canonical fix for disposition
of the existing palette finding, and assess the proposed threshold family before
any production API integration or training admission. Unrelated same-source peer
findings belong to the supplementary ticket records, not this task's approval.

<!-- arcpuzzles-current-conflict-reconciliation:start -->
## Current proposal reconciliation

Retained current literal-color-4 repair, VERSION=3.1.0, exact seed draws, port_threshold prototype and low-space tooling. Ported only missing template validation: required color-4 ports, 2..3 ports even in no_targets, strictly interior placement and no non-port holes. The candidate VERSION bump and duplicate threshold prototype were not selected.

Current source-bound disposition and focused checks: [evidence/conflict-reconciliation.json](evidence/conflict-reconciliation.json). All proposed variants remain unapproved and training_admitted=false. Existing audits/failures are preserved; this reconciliation does not resolve an audit or refresh an exact-source safety approval.
<!-- arcpuzzles-current-conflict-reconciliation:end -->
