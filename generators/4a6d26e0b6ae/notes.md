# Cumulative review handoff — 4a6d26e0b6ae

Assignment review-e15551ffde646c62; round 2. Final source SHA256:
`43f8d2353976e27ec57066f7c5c1c41993a00eee2e56515ced74f55e08bfa262`. Sampler VERSION remains 3.0.0; source hash identifies validator revisions.

Round one repaired overwritten centers, missing moats, underfilled counts and
inert controls. Round two leaves that sampler unchanged, strengthens negative
fixture/metadata validation, and makes the independent integrity probe fail
closed on all reported failures. No Racket, catalog, shared code or audit target
is changed. Original associated notes remain untouched.

Final task-local tests: 124 passing. Source-bound checks: 14,700 override requests
match round one exactly (12,564 outputs and 2,136 expected structured refusals),
8,832 direct fallback cases pass, 600 invalid mutations are rejected and 800
valid transforms pass. The 8,000-draw census is valid/unique; 273 Racket comparisons
match and the 12-stage battery passes. Root REVIEW.md/RESULTS.json give exact
schedules, independent-check limits, actual paths and failed iterations.

The shared suite still has its fixture import failure. A task-local replay tool
verifies a five-line fixture proposal in a copied repository: 166 tests pass
there. It must be promoted separately, not mixed into this generator patch.

The cumulative patch replaces round one against the original packet. A source-only
incremental patch for already-applied round-one checkouts is retained under
checks/round2/. Current solve: one exposed, reviewer-authored revision; 3/3 visible
examples; masked queries unscored. Earlier episodes and all failed iterations
are archived. No model training, independent blind solve or admission is claimed.

Next: replay release evidence, independently score the current hidden queries,
route the shared fixture proposal to its owner and the inherited audits to their
separate assignments. Avoid unrelated normal-domain expansion without evidence.
## Current reviewer considerations

Source SHA-256: `43f8d2353976e27ec57066f7c5c1c41993a00eee2e56515ced74f55e08bfa262`.

# Round-two decisions — 4a6d26e0b6ae

Final generator SHA256: `43f8d2353976e27ec57066f7c5c1c41993a00eee2e56515ced74f55e08bfa262`. Sampling version remains 3.0.0.
The unchanged distribution choices and first repair rationale are preserved in
`checks/round1-metadata/DECISIONS.md`; the cumulative source patch includes them.

## G4: make the explicit validation contract complete

Normal motifs already had a complete-color/span check after round one. The
negative path was explicitly weaker, and blank mode returned before size/count
checks. Those shortcuts were unnecessary: a malformed fixture can hide a later
regression even when it is not ordinary training data. Shared metadata checks now
run for blank mode too. Explicit palettes are compared as sets: palette order is
not observable as a general input invariant. Falsey invalid values are not
silently treated as omitted.

Different-colored endpoints cannot be paired by color. For at most four motifs,
use a bounded search for a complete geometric pairing with zero centers and a
one-cell moat. Do not demand degree one in the candidate graph: endpoints at
columns 0,2,4,6 have an extra 2-to-4 candidate but still form two valid motifs.
A greedy pairing could reject valid fixtures, so the test includes this positive
counterexample. The validator does not borrow the sampler's masks or candidates.

Do not expand the normal domain to clutter, repeated colors or nine motifs.
Counts remain the declared 1..8, and mismatched negatives remain 1..4. Racket is
unchanged. These are validation repairs, not new examples or label behavior.

## G5: independently enforce requests and combine all failure signals

A self-check rejection and an independent pixel failure are each sufficient to
fail a draw. The old tool required a pixel failure before recording either,
creating a false green for a broken self-check. Explicit caller counts must take
precedence over internally recorded draws, or an ignored override can certify
itself. Independently inspect shape, palette and helpful texture constraints too.

Probe evidence paths must be new. Overwriting a prior run or silently discarding
a repeated override key is rejected instead of losing an input request or a
failure artifact. Keep this probe task-specific: it is not a global ARC validator.

## V2: separate sample equality, geometry and mutation coverage

The finite domain admits a complete shape/texture/count cross-product. Three
seeds are enough to exercise that contract grid cheaply; they are not enough to
prove behavior for every seed. Test the direct fallback separately to avoid
assuming it was reached by random dense requests. Retain positive controls as
well as deliberate invalid mutations so rejecting everything cannot pass.

The requested inputs/exceptions match round one on all 14,700 scheduled calls.
The AST comparison also preserves the sampler's functions, imports and constants.
Changing VERSION merely for validator edits would change keyed random draws, so
retain it and use source SHA256 as the actual revision identity.

## T2: fix the synthetic fixture's own source layout

An installed global package can hide the missing CLI in a minimal packet. Do not
weaken subprocess isolation or use the failed package-install attempt as a reason
to skip the issue. Copy the current CLI into the test's synthetic library before
packing. Exercise the proposal in an independent temporary repository, with
copied CLI imports checked explicitly. Leave the real shared file unchanged
because this review's allowed source scope is the selected generator.

The original failure, proposal diff, copied source identities and full 166-test
pass are retained. This is a verified proposal awaiting owner integration, not
a claim that the original repository is all green.

## Evidence and stopping boundary

All red iterations and both earlier solve episodes are retained, with their
source hashes and path mappings. Final generator checks use release-* evidence.
Prior rule exposure is disclosed in the current solve, and hidden accuracy remains
withheld. No model training, external review or task admission is claimed.
Stop after a verified cumulative/incremental application and source-bound replay;
do not turn another validation round into an unrelated distribution rewrite.
