# Working notes: 2376352117fc

## Review review-d348b5aca78b1513

The imported v2.1.0 accepted only full, input-disjoint translations, although the
canonical Racket rule clips per cell and starts from an empty output. The old
summary incorrectly retained source cells. Its validator rejected canonical
train example 1 (zero visible translated cells). `motif_size` and several declared
axes were not realized; the old coincident-marker/zero-vector option erased blue.

Version 3.0.0 keeps the Racket rule unchanged and expands lawful inputs instead.
It implements five observable axes, connected motif growth, bounded constructive
placement, canonical-dimension weighting, strict overrides, and semantic witnesses.
The Python rule mirror is an audit helper, never a source of training labels.

### Failed iteration worth retaining

The first eight-profile schedule could provide three demos without any target
landing on an input cell. The semantic gate found easy seed 227465423747153,
start index 22: `background_only` survived the demos and disagreed on the query.
Changing the first cycle slot from `full_clear` to `full_overlap` closes that
window. Tests now cover every cyclic start and the exact failing lesson. Do not
replace the schedule with untested independent texture draws without checking
lesson identifiability. A finite rival check is not a universal identifiability
claim.

### Evidence and limits

Packet-level reports contain baseline, intermediate, and final source hashes;
3072 default draws per probe use seeds 0–127, indices 0–7, and three difficulties.
Final Racket parity checks cover those draws plus four canonical pairs. Keep
unique-input counts separate from draw counts and overlapping lesson windows.
Difficulty distributions overlap deliberately; the same aligned seed/index can
produce the same grid in different bands. Empty outputs are capped at one of
eight default profiles, not removed, because canonical evidence requires them.

See `workspace/README.md` for repeatable probes and `tests/` for regressions.
Imported associated evidence remains untouched under `evidence/`.
## Current reviewer considerations

Source SHA-256: `3ce804dbd66c74ca79c075ee6e0e506f534445cdae6618deb8b7f6e193644bc8`.

# Decisions — review-d348b5aca78b1513

Final selected generator: `3ce804dbd66c74ca79c075ee6e0e506f534445cdae6618deb8b7f6e193644bc8`.
Unchanged Racket rule: `6dc047f6d5665a74ecdc862875ecc605e91210827d6803d542bea74c0360183d`.
Baseline generator: `c8629ccb6c7fe742a19b9621782d6a4eeb0d7d57cd97e85c7913e13bd4050352`.
Intermediate candidate: `c58f6e830a6b8441ec07a75c2fe0f800301ddd1cca36269e0cdb30f87264f6ae`.


The old author's intentions are not known beyond the supplied comments and code.
The following separates observed restrictions from inferred motivations. Full
commands and source-bound counts are in `RESULTS.json` and `REVIEW.md`.

## D1 / G1: Keep the Racket rule; fix the input distribution and documentation

Observed baseline: targets were forced in bounds and away from all input cells;
the summary said the input remained. Possible original rationale was making the
translated motif easy to see, but that is an inference, not an attributed intent.
Canonical train index 1 is completely clipped and the Racket output starts blank.
Changing Racket to preserve the input or reject clipping would contradict this
authority. I kept it byte-identical, corrected both summaries, and accepted the
canonical input in self-check. All four canonical outputs match Racket.

## D2 / G3: Full, partial, and empty visibility are separate profiles

Independent random placement would increase variety cheaply, but can produce
almost entirely blank lessons and leave meaningful boundary cases rare. Keeping
only full visibility would leave an all-or-nothing object-clipping rival intact.
I chose explicit full/partial/empty profiles and a default cycle with one empty
case per eight slots. Empty is a lawful canonical edge case, not a negative
fixture. Default partial rate is 3/8; default full rate is 4/8. These exact rates
apply to complete cycle blocks, not arbitrary finite randomly sampled cohorts.
An explicit profile override has exact observed behavior. Racket comparisons and
complete witnesses verify per-cell clipping rather than an output-count proxy.
No empty-output rate is claimed to be optimal for learning without training runs.

## D3 / G3: Input/target overlap is a required distinction

The baseline's collision restriction was unnecessary because output is a fresh
canvas. A background-only painter fits all four canonical pairs and every one
of the 3,072 baseline draws. I allowed overlap with a green source cell or the
blue marker and required overlap profiles. A translated cell cannot coincide with
red while blue remains separate from the source: target = source + (red − blue)
equals red only when source = blue. I therefore did not advertise an impossible
independent red-overlap axis. For non-self-contact overlap, blue is placed in a
visible target; all marker/source constraints remain enforced.

## D4 / G4: Use a coverage schedule, and test windows rather than only counts

The first candidate covered all five profiles in the population but had a
three-demo window with no input/target contact. The semantic gate identified the
actual ambiguous episode, so aggregate witness rates were insufficient. I changed
one cycle slot to make every consecutive three-demo default window include full,
partial, and overlapping outputs. I rejected simply increasing demo count because
three informative examples are already available with a better schedule. I also
rejected suppressing the rival hook: that would conceal, not solve, the ambiguity.
Tests retain the exact bad episode and all eight cycle-start positions. This is
a finite declared-competitor diagnostic, not uniqueness over all algorithms.
Users forcing a texture must assemble their own informative lesson mix.

## D5 / G2: Remove fake controls rather than preserve silent compatibility

Observed baseline: declared color/position/texture controls were constant or
ignored, `motif_size` was swallowed, and unknown keys were accepted. I cannot
establish why the original template declared them. Keeping diagnostic-only names
would avoid breaking callers but preserve a misleading interface. I instead
expose five realized axes and reject unknown names. This intentionally breaks
callers relying on old cosmetic or invalid knobs; they must migrate. Axis values
are validated strictly, including rejecting booleans and numeric strings for
integer controls. `observe_overrides` measures realized geometry so tests do not
merely trust returned metadata. Numeric boundaries and full profile/direction
cross-products are tested in every supported difficulty setting.

## D6: Preserve fixed semantic colors and connected 3–8-cell motifs

Color 1 is the vector origin, 2 its destination, 3 the translated source, and 8
the output. Unrestricted palette permutations would change those roles without
changing Racket, creating bad labels. Motif frontier growth explores connected
polyominoes while respecting the imported 3–8-cell family. Contact profiles start
from a small direction-compatible connected fragment; diagonal contacts get a
bridging cell to preserve 4-connectivity. I did not broaden to multiple motifs or
new colors, since that would confound this repair with another task family.
The final cohort contains 801 motif classes up to translation and 313 up to
rotation/reflection, but this is not an exhaustive enumeration of all polyominoes.

## D7 / G1: Restore compact dimensions without making the family tiny

The baseline profile-floor check found zero exact canonical shapes in 60 draws.
I weighted canonical row sizes 7–9 and column sizes 10–12, while keeping all
heights 7–18 and widths 7–19 accessible. Difficulty changes these weights and
motif-size weights rather than making medium/hard canonical support impossible.
This avoids an opt-out declaration that would simply waive the missing support.
The cost is intentional cross-band overlap: 3,072 draws yield 2,525 unique inputs,
although each 1,024-draw band is internally unique. I considered adding another
band-specific random salt solely to raise that aggregate count and rejected it:
that changes replay and does not itself improve the semantic support. Dataset
splits should deduplicate actual input/episode identities, not rely on different
seed tuples or difficulty labels to guarantee separation.

## D8: Bounded constructive geometry rather than retries with hidden fallbacks

Vectors, motif origins, and valid marker sites are searched in randomized finite
orders. There are at most 32 motif constructions before a clear ValueError. No
silent fallback switches requested profile, size, direction, or grid dimensions.
The local endpoint matrix covers 1,280 combinations. The 3,072 default-draw probe
has no generation failures. These are finite tests, not a proof every possible
seed and parameter tuple succeeds. The measured generation timings were taken
while other checks ran and are not a hardware throughput benchmark.

## D9: Keep label authority independent from diagnostics

The Python mirror supports geometric assertions, counterexample searches, and
finite-rival lesson checks; it does not label the returned training dataset.
The probe compares every selected draw with the unchanged Racket rule and checks
four canonical outputs. Before and after can both have perfect mirror parity
while only the latter provides useful boundary evidence. This is why parity,
coverage, identifiability, uniqueness, and learned performance are separate claims.
`--racket` must be used for authoritative parity claims from the probe.

## D10: Build reusable local tools and preserve development failures

The parity probe stages the public runtime instead of relying on accidental
source-layout imports. The read-only audit tool handles row-string grids and both
singleton/list test formats; two regression tests cover those formats. The
relocation tool defaults to a fail-closed Landlock check, with an explicitly named
weaker `--guard none` option when the host returns ENOSYS. Source-hash equality,
Python `-I`, and a different directory do not mean source reads were denied.
No copied runtime or duplicate repository is part of the return; logs/manifests
are retained. Failed invocations are reported instead of erased.

## D11: Stop at assignment scope; do not imply learning gains

Both audits produced concrete issues, but their generators are deliberately left
unchanged. The shared tiny-packet pytest failure is preserved and escalated in
feedback, not repaired outside scope. The fresh solve is honestly prior-exposed
and receives visible-only feedback. Acceptance should require independent source
review, replay of the recorded probes and battery, and maintainer query scoring.
A useful next experiment is a controlled learner comparison on a deduplicated,
Racket-labeled corpus with clipping/overlap held-out evaluations; none was run here.

## Native parametric review — 2026-10-25

**Decision.** Add one episode-fixed semantic axis, `vector_direction`, while
preserving the exact canonical default. `blue_to_red` uses the catalog program
byte-for-byte; `red_to_blue` derives the same marker displacement and reverses
its sign before translating the complete green component.

**Teaching construction.** Inputs are identical across settings. The first two
examples deliberately combine source/target overlap with bilateral per-cell
clipping, so they distinguish the direction and reject the retained
all-or-nothing, background-only, preserve-input, unit-vector, same-color, and
swapped-axis shortcuts without increasing the two-demo minimum. This is a
finite declared-rival check, not a universal uniqueness proof.

**Controller contract.** The adapter supports independent stable prefixes for
2–6 demonstrations and 1–4 queries. It stores four distinct controller-side
queries, revealed one at a time with no future-query or total-count field. Query
shapes are 12×15, 18×20, 24×27, and 30×30; the largest contains a connected
90-cell green motif and 92 nonzero input cells.

**Sequential dependency.** Step A derives the ordered marker coordinates and
input-specific signed vector. Step B consumes that vector to translate each
green cell, clip per cell, recolor visible targets cyan, and render on a fresh
zero grid. Reversing the intermediate vector changes 92 protected-Racket output
cells in the retained witness.

**Evidence.** The changed-target suite passes 119/119 tests. The reusable
self-audit passes 42 protected-Racket executions plus 256 deterministic Python
stress episodes. Native qualification passes four setting/seed jobs with 40
protected-Racket labels, and the source-bound witness is independently marked
`reviewer_replayed`. Sixteen saved public views pass both packet projection
verification and the independent public-only conformance checker. Production
`generator.py` remains at SHA-256
`3ce804dbd66c74ca79c075ee6e0e506f534445cdae6618deb8b7f6e193644bc8`;
the canonical program remains at
`6dc047f6d5665a74ecdc862875ecc605e91210827d6803d542bea74c0360183d`.
Owner exact-source acceptance remains pending and no training admission is
claimed.

Owner reconciliation: Three exact disjoint Racket rules share matched clipping scenes. The first two demonstrations now use opposite diagonal vectors and reject both axis-only shortcuts; queries mix axial/diagonal vectors and fragment sizes. The retained earlier witness and fresh protected-Racket repair checks are in evidence/owner-variant-reconciliation/. All prior programs/default remain intact. Current exact-source acceptance: `evidence/owner-variant-reconciliation/current.json`.
