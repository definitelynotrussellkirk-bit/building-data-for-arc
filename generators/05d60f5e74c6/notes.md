# Selected-task review notes

Review assignment: review-cc2c4e70c983e6b2. Baseline3.0.1 to selected4.0.0.
Final source: `fee35f721520c535929f77201658ac3ad0c01f7a4a89014a89c2ea8149f058e7`; Racket pin a74660ace2a2 unchanged.

Root cause was mandatory texture placement after optional rectangle packing;
failed appends were ignored. Paired seed0..99,index0,easy probes found 7/100 blob,
14/100 thin-line,64/100 L-merge omissions before, zero after. All baseline thin
samples also lacked singletons. The new bounded joint packer has an8x9
constructive fallback and input-derived axis checks. Four-sample scheduling
provides complete default demo coverage rather than a marginal-frequency claim.

The intermediate rewrite failed canonical-profile support; adding plain-phase
source morphology anchors restored support across difficulty bands. Positions,
colors and labels are not copied. The resulting plain cross-band duplication is
explicit: 2,400 draws ->2,000 unique in the final source-bound census.

Default census: seeds0..99,indices0..7,three bands;1,200 overlapping four-demo+
query windows, all refuting declared competitors. This is finite evidence over
seven explicit rivals. Explicit overrides, three-demo truncation and arbitrary
shuffling do not inherit the guarantee. No actual model-training gain is measured.

Runtime/test artifacts and failed iterations are in the assignment return ZIP;
root REVIEW.md,DECISIONS.md,QUESTION_ANSWER.md,AUDIT.md,RESULTS.json index them.
The single fresh solve is bound to final bytes, earlier exposure=yes,
reference consulted during solve=no; visible4/4, hidden labels not inspected.
Audit generators 24d677c76640 and e99db35d533d were not changed.

Next work: maintainer independent intake and dedup-aware training admission;
separate repairs for audit findings. Keep the shared Racket authority and frozen
root fixture unchanged unless a new source-grounded reason warrants otherwise.
## Current reviewer considerations

Source SHA-256: `fee35f721520c535929f77201658ac3ad0c01f7a4a89014a89c2ea8149f058e7`.

# Decisions — review-cc2c4e70c983e6b2

Final selected source: `fee35f721520c535929f77201658ac3ad0c01f7a4a89014a89c2ea8149f058e7`. R1–R5 refer to `REVIEW.md`.

## 1. Keep the Racket authority, not just its canonical outputs (R1, R3)
The canonical five pairs all contain fat solid rectangles. The earlier summary
already intended irregular objects to disappear and thin shapes to collapse to
endpoints/singletons, but the older sampler did not reliably expose them. The
Racket program implements these branches; changing it to fit a weak sampler
would erase intended semantics. Direct Racket execution checked all five source
pairs and all retained synthetic tests. No authority change was warranted.

The written canonical description that objects are already solid rectangles
alone does **not** demonstrate the irregular or thin branches. This is an
explicit authority-backed curriculum extension, not a claim that those branches
were visible in the canonical examples. The final validator is a helpful
teaching-domain validator, not the universal domain of the Racket function.

## 2. Guarantee required geometry rather than retrying optional appendages (R1)
Original code places ordinary rectangles before trying to append the requested
texture. Its likely rationale was simple placement with separated objects; the
original author's full intent is unknown. Observed omissions make draw intent
unreliable as evidence. We rejected larger arbitrary retry counts: they reduce
but do not eliminate silent missing witnesses.

The new packer jointly considers all mandatory groups, first reserving large or
decisive shapes. Ten bounded layout attempts shrink incidental sizes after the
fourth failure. A constructive minimum 8x9 template then realizes every allowed
count/texture combination. Postconditions independently derive dimensions,
rectangle count and texture from the output grid. A failure now raises, not
quietly returns an easier input. Reflection and larger-grid offsets diversify
the fallback, but frequent fallback at dense extremes could still create a
recognizable layout. Fallback frequency has not been instrumented as a metric.

## 3. Teach a complete rule family in each default lesson (R3)
Unscheduled random textures were rejected because high marginal witness
frequency does not establish lesson-level identifiability. The deterministic
four-profile cycle uses `(seed + sample_index) % 4` and sets EXAMPLES_NEEDED=4.
Every four consecutive default demonstrations include plain, blob, thin, and
L-merge profiles. Blob/L profiles use the first rectangle's color, separating
component identity from color grouping. L-merge profiles with the default
count>=2 also include diagonally touching same-color rectangles. Thin profiles
contain both a length>=3 bar and a singleton. Every scene includes a rectangle
whose noncorner cells actually disappear, refuting identity.

The exact cyclic census is in `checks/final_census.json`: seeds 0..99, indices
0..7, three bands, 1,200 overlapping windows. Dynamic rival declarations, not a
copied rival-name list, are consulted. This guarantees neither all conceivable
rivals nor learning by an arbitrary model. Nonconsecutive/shuffled collection,
three-demo truncation, or forcing one texture for every demo does not inherit
the guarantee. Explicit rectangles=1 remains lawful but cannot include a
same-color diagonal rectangle pair; this exception is not hidden.

## 4. Keep difficulty variation without losing canonical scale (R4)
The first rewrite scaled all profiles with difficulty. Native profile-floor
correctly rejected this: only 1/60 exact-profile samples and no medium/hard
support. The retained red test precedes the correction. We rejected lowering the
gate or claiming its failure was merely conservative.

Plain profiles now draw one of five source (height,width,fat-count) triples in
all bands. Positions, colors and dimensions of individual rectangles remain
sampled; no canonical grid or output is embedded. Explicit grid/count overrides
still cover the full declared range. Nonplain profiles keep difficulty-aware
sampling. This yields 16/60 exact-profile samples in the final gate. The tradeoff
is deliberate plain input reuse across bands: 2,400 default draws give 2,000
unique grids, not 2,400. Future dataset splitting should deduplicate by content,
not treat difficulty as an independent split identity.

## 5. Honest axes and helpful-versus-diagnostic domains (R2)
Final helpful axes are height8..20, width9..22, fat rectangle count1..6, and four
textures. Count means the number of solid 4-components with both dimensions>=2;
bars, singletons, and irregular groups do not count. This definition is observable.
Unknown axes, bad types, unknown texture/difficulty and infeasible bounds are
errors. Integer-like floats and bool are not silently accepted. Fixed background
0 is semantic; object colors vary within1..9. Different colors may touch as they
do in source examples; same-color 4-touching groups are prevented unless their
merged shape is the explicit irregular witness.

Legacy no_rects/all_2x2/single_cell_rects calls remain available as named negative
fixtures, not advertised helpful inputs. Their label behavior is legal, but the
teaching validator rejects these identity-only scenes. An all-2x2 scene is not
invalid ARC; it is noninformative for the intended corner-removal lesson.
Unrestricted noise, arbitrary backgrounds, many unrelated textures and silently
clipping requested sizes were rejected as off-task or misleading variation.

## 6. Independent observations and finite evidence (R5)
`expected_output` is a local semantic/test mirror; production labels still come
from canonical Racket. Task tests and the review probe use separate component
traversals, and the census compares the mirror with actual Racket. This reduces
shared-implementation risk but is not a formal equivalence proof.

`workspace/review_probe.py` discovers rivals from the generator, counts unique
inputs separately from overlapping windows, binds source/rule/prelude identities,
and retains exact failure inputs. Its geometry checks for blob/thin/l_merge are
task-family specific; its native runtime and declared-rival machinery are reusable.
`workspace/audit_targets.py` is intentionally a two-target reproducer, not a
universal audit engine. `workspace/counterexamples.py` reexecutes four small cases
against Racket and emits self-contained JSON suitable for separate repair tickets.
A regression prevents the audit tool from treating an axis test's mere presence
as a finding; the underlying verified audit findings remain unchanged.

## 7. Preserve failed iterations; do not overclaim a fresh solve
The initial task regression run failed 15 tests and passed one against the old
source; tests subsequently grew. Intermediate battery failures and source bytes
are retained. The final generator bytes were frozen before solve preparation.
The new solve reads only its public challenge and uses its own Python; prior
rule exposure is explicitly yes. One genuine attempted solution passed visible
checks. Private correctness is unknown, and no token-level trace was recorded.

## 8. Respect assignment boundaries
Only selected task source/docs/workspace/tests were edited. Audit targets remain
byte-identical to their assignment. Their findings are concrete follow-up repair
candidates, not fixes claimed by this return. No repository-wide gate, fixture,
canonical ledger, prelude, base solution or audit generator was modified.
