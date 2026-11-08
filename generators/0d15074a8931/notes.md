# Working notes: 0d15074a8931

## 2026-10-04 review `review-8867716a91fd0793`

The pinned 2.0.0 baseline passed the 12-stage battery, but its repeated-color
rectangles were always far apart. Consequently, the plausible rule “form
8-connected components per color, then keep one bounding-box center” matched all
5 canonical pairs and all 600 sampled baseline draws. The exact lawful witness is
two same-color 3x3 rectangles at `(rows 0..2, cols 0..2)` and `(rows 3..5,
cols 3..5)`: the intended 4-connected rule keeps centers `(1,1)` and `(4,4)`,
while the shortcut merges the corner contact and keeps `(2,2)`.

Version 2.2.0 preserves the canonical Racket rule and exact override behavior.
Default `repeated_color` schedule slots now use a 3x3 placement search whose first
same-color pair touches diagonally, while explicit override requests retain the
prior quadrant layout. The schedule remains deterministic and all cyclic
four-demo starts retain every required witness. A second repair replaced the
nonportable task-test canonical-data lookup with public `reviewer_support`
helpers; the baseline task-test stage had failed 1 of 20 in its copied runtime.

Prior-return lead: `local-random-3a0dd6e1bf02` suggested checking per-color
shortcuts and exhaustive four-demo windows. Its claims were treated as leads,
not as measurements of this pinned source; all counts in this return were rerun.

See `workspace/connectivity_probe.py` for the reusable declaration-driven probe
and packet-level `checks/diagonal-rival-*` for before/after evidence.

## Rotation-census follow-up

The first 100-per-band census had 0/300 native ambiguous lessons but 226/1500
ambiguous query rotations. In 225 cases the unique diagonal-contact witness had
been rotated out of the demonstrations; one additional hard-band rotation lost
the only non-square witness. Version 2.2.0 makes both `repeated_color` and
`multi_object` slots carry the repeated-color diagonal witness, and makes both
`nonsquare` and `large` slots carry a viable non-square dimension-at-least-five
rectangle. The placement loop now searches profile-valid sizes for a legal
position before considering fallbacks, fixing the silent 3x3 collapse that the
new rotation regression exposed.
## Current reviewer considerations

Source SHA-256: `e2ef68262c67d991b3874aa6bb8fa6dda80c08ab1000e00249766c8766f69c3c`.

# Decisions for `0d15074a8931`

Final generator: version `2.2.0`, SHA-256
`e2ef68262c67d991b3874aa6bb8fa6dda80c08ab1000e00249766c8766f69c3c`.
The canonical Racket rule and rule hash `4600d000ebae` are unchanged.

## G1 — model 4-connectivity explicitly

**Choice.** Add the wrong rule “8-connected components per color, then one
bounding-box center” to every semantic rival declaration, and add an executable
`same_color_diagonal_contact` witness.

**Rationale.** The canonical examples contain one object per color, and the 2.0.0
generator kept repeated-color rectangles far apart. Therefore both the intended
4-connected rule and the rival agreed on all 5 canonical pairs and 600/600 sampled
baseline draws. A same-color corner contact is the minimal lawful case that makes
the connectivity convention observable without changing the reference rule.

**Exact probe.** Two color-4 3×3 rectangles at `(0..2,0..2)` and `(3..5,3..5)`.
The intended output centers are `(1,1)` and `(4,4)`; the rival gives `(2,2)`.
Evidence: `checks/diagonal-rival-final/`.

**Rejected alternatives.** I did not alter the Racket authority, prohibit repeated
colors, or merely document the convention. Those options would respectively
change the task, remove an important per-object witness, or leave the shortcut
teachable. I also rejected cardinal contact because it would merge the rectangles
under the intended 4-connectivity and cease to be lawful.

## G1/G3 — use a constrained contact layout only for ordinary repeated-color slots

**Choice.** On default, unoverridden `repeated_color` and `multi_object` draws,
place 3×3 rectangles so the first same-color pair touches at exactly one corner.
Additional rectangles are placed by backtracking with cardinal separation.

**Rationale.** A fixed 3×3 contact pair is feasible across the declared 9–16 grid
range, makes the witness obvious, and avoids coupling the connectivity witness to
large-shape placement. Using two profile slots means any five consecutive pairs
retain the witness even when either one becomes the query.

**Why only ordinary draws.** Explicit overrides promise exact grid size, object
count, color pattern, and edge profile. They retain the pre-existing quadrant
layout so user-requested axes remain observable and the full override cross-product
continues to pass. The original source did not document why quadrants were chosen;
the most defensible inferred rationale is reliable non-overlap/cardinal separation
and straightforward exact-axis control.

**Rejected alternatives.** One witness slot per cycle passed native lessons but
failed 225 rotated-query cases. Applying the contact layout to all override calls
risked violating exact controls. Replacing the entire layout engine globally was
unnecessary and would have expanded the regression surface.

## G3 — duplicate every required lesson witness

**Choice.** Make both `repeated_color` and `multi_object` carry the repeated-color
and diagonal-contact witnesses. Make both `nonsquare` and `large` carry a
non-square rectangle whose maximum dimension is at least five.

**Rationale.** Four demonstrations are selected from a five-pair lesson when each
possible pair is rotated into the query. A witness that appears only once can be
removed entirely. Two copies are the minimal schedule multiplicity that survives
all single holdouts.

**Evidence.** The intermediate census on SHA `800be1f…b27206a` had 0/300 native
ambiguities but 226/1500 ambiguous rotations. The final census has 0/1500. Full
compressed reports and compact hash-bound summaries are under `checks/lesson-census*`.

**Rejected alternative.** I did not weaken `lesson_identifiable` or exclude query
rotation from evaluation. Both would hide a teaching defect rather than repair it.

## G4 — search viable sizes before fallback

**Choice.** `_size_options_for_slot` returns shuffled preferred sizes followed by
fallback sizes, and placement tries them in order until a legal position exists.

**Rationale.** The first schedule repair could choose a preferred non-square size
that did not fit the edge/interior constraint in its selected slot, then silently
collapse to 3×3. The failure was not the profile choice itself but testing only one
size. Searching all legal preferred sizes preserves randomness while honoring the
profile whenever the slot admits it.

**Rejected alternatives.** Increasing every grid or hard-coding one orientation
would narrow distribution diversity and interact poorly with overrides. Retrying
entire episodes would make behavior less transparent and harder to reproduce.

## G2 — use public portable canonical-data helpers

**Choice.** Task tests now import `canonical_pairs`, `canonical_path`, and
`find_root` from `reviewer_support`.

**Rationale.** The baseline test guessed a repository-relative data path from the
test file and failed in the source-bound copied runtime. The public helper is the
supported layout-independent API. No fixture contents were changed.

## Reusable tool

`workspace/connectivity_probe.py` is intentionally declaration-driven. It:

1. verifies every `CANONICAL_SHORTCUTS` entry against all usable canonical pairs;
2. samples every band and counts all declared witnesses and rival matches;
3. checks all 24 cyclic starts and all five query positions per start in each band;
4. retains the exact 4-vs-8-connectivity fixture; and
5. prepares its own isolated runtime when invoked from a source packet.

The first execution failed because a source-checkout script imported the
per-puzzle runtime package directly. That failure is retained in
`checks/connectivity-probe.console.log`; the final tool uses the same portable
runtime boundary as reviewer checks.

## Determinism, axes, and domain

- Generator randomness still comes only from `gen_ctx`; tests verify no mutation
  of Python's global random state.
- Advertised overrides remain exact; unknown keys fail loudly.
- Ordinary inputs remain 9–16 rows/columns, 2–4 solid odd-by-odd rectangles,
  ARC colors 1–9, and cardinally separated foreground objects.
- Same-color corner contact is lawful because objects are defined by
  4-connectivity.

## Self-review for newly introduced shortcuts

The final schedule is deliberately regular: each of the four semantic profile
classes appears about half the time when paired by witness category. A learner
might infer the curriculum residue, but residue does not determine a different
output; the output still requires finding each rectangle center. I checked all 24
cyclic starts, every query holdout, all declared rivals, and 100 production lessons
per band; no rival survived a final demonstration set.

The contact branch currently uses 3×3 rectangles for the touched pair. That could
encourage “diagonal contact implies 3×3,” but other ordinary profiles include
non-square and dimension-five/seven objects, and every complete lesson retains
those witnesses. A future grammar expansion could add 3×5/5×3 diagonal-contact
pairs, but it is not required to distinguish the present strongest rival.

## Remaining limits

The rival set is finite and hand-specified. Passing it is evidence against known
shortcuts, not a proof of unique program induction. The exhaustive rotation check
covers the deterministic 24-start probe and the production census covers 100
lessons per band; neither enumerates every seed or every lawful rectangle layout.
