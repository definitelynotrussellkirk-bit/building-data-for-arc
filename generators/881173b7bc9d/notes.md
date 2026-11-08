# Working notes: 881173b7bc9d

## Current rule and support

The unchanged Racket authority is pinned by `RULE_HASH = "b87fde7ab095"`.
Find monochromatic FOUR-connected nonzero components whose cells are exactly
the perimeter of a rectangle at least 3 by 3. Sort by left edge; extract each
complete interior rectangle; concatenate with one zero column, aligned at the
top and padded with zeros below. Zero accepted frames gives `[[0]]` under the
raw reference; one frame and blank interiors are also lawful reference cases.

The sampler's ordinary support has 2..5 intact frames. An explicit
`n_frames=1` is supported and passes `self_check`, but is outside the strict
ordinary training manifold. `self_check` rejects malformed grids, invalid
integer colors, no-frame impostors, and unexplained nonzero cells. It admits
recognized damaged-ring boxes because canonical train 2 and test 0 contain
overwritten borders and ignored interior patterns. This is a bounded input
grammar, not a claim to recognize every input on which the reference executes.

## Current distribution decisions

- Four core layouts preserve canonical size/palette anchors and vary vertical
  order, same-color diagonal contact, and overwritten-frame distractors.
  A deterministic seeded broad branch extends canvas height and frame count.
  Positions, colors and interior patterns vary; no saved canonical grid is replayed.
- Same-color frames are separate only when FOUR-connectivity keeps their
  borders separate. Different-color borders may touch. Additional right-hand
  frames start after a zero column even when the core touches the canvas edge.
- `grid_h=7..18` and `n_frames=1..5` are exact in every difficulty band.
  `observe_overrides` derives both values from the returned grid.
- `palette_kind` and its `texture` alias are effective: `default` uses four
  sampled nonzero colors; `varied` uses six; `warm` uses {2,4,6,8,9}; `cool`
  uses {1,3,5,7,8}. Every selected color occurs. Contradictory aliases reject.
  Sparse/dense interiors use distinct occupancy targets while preserving
  minimum content and full palette support. Unknown keys reject.
- The old canned `no_frames`, `single_frame`, and `empty_interiors` textures
  are retired. They bypassed advertised axes. Use `n_frames=1` for the supported
  one-frame boundary; raw no-frame/empty-interior authority examples remain
  independently tested in `counterexamples/frame_semantics.json`.

## Teaching policy and limits

Use four consecutive demonstrations followed by a query. The declarations
check seven rivals: global color grouping, eight-connectivity, accepting broken
frames, row-major order, uniform recoloring of nonzero interior cells, no
separator, and bottom alignment. The first, second and fifth fit all four
canonical labels and require generated counterexamples. Query rotations are
checked as a finite diagnostic against these declared rivals.

The core layouts cycle through four phases, but broader topology and palettes
depend on the full sample index. No finite semantic schedule period is claimed.
Arbitrary shorter lessons, override-defined curricula, untested starts/seeds,
all possible frame nesting/overlap, or undeclared rivals are not certified.
Border and interior palettes are deliberately disjoint; this restriction and
the fixed warm/cool sets are current support limits, not reference requirements.

## Resolved mechanisms and retained evidence

The current-source audit `review-fc99ea32bddfe9ee:v0001` identified the
acceptance-only validator, absent rule pin and dead density declaration. The
new validator and controls address those mechanisms; `tests/test_frame_contract.py`
retains the minimal impostors and exact controls. The immutable review index
still needs an explicit maintainer resolution after applying these bytes;
source changes alone do not silently clear its `needs_triage` status.

The first repair candidate appended a same-color frame directly against the
right edge of an existing frame (seed 10, index 10). It rejected that draw,
which also removed a damage witness from some materialized lessons. The
current placement keeps a zero column; the four-phase count regression covers
the failure. The return retains that failed candidate's input and complete
battery/census evidence, including five ambiguous rotations.

`tests/test_frame_semantics.py` checks independent literal Racket fixtures,
canonical data and precise perimeter semantics. From the repository, replay
all 13 authority cases with `python3 generators/881173b7bc9d/workspace/probe_frame_semantics.py`
under the packet's runtime wrapper. The probe checks exact authority hashes
before calling the public API. Labels remain Racket-derived; Python mirrors
are diagnostics. See the return's RESULTS/REVIEW for final source-bound counts.
## Current reviewer considerations

Source SHA-256: `a68e1912ecdae752ee5ba79a298789a3b49b14f163264009b82d19be22f471d9`.

# Decisions for 881173b7bc9d

## Authority and diagnosis

Keep the existing Racket rule, hash `b87fde7ab095`, unchanged. Its exact
four-connected monochromatic component rule already matches all four canonical
labels. Correct the sampler and validator around that rule. The previous
review `review-fc99ea32bddfe9ee:v0001` was a lead; its validator examples were
reproduced on the selected `e7e43c951271a6769ab9de941e07a068defdbd5e31b01977c7673a6a73b486d9`
source before repair. Earlier imported rationale is otherwise unknown.

The baseline battery failed lint, selfcheck, defect lint and overrides. It had
zero canonical exact-profile hits in 60 draws and no semantic contract. A
validator that merely accepts every grid cannot establish a lawful distribution.

## Distribution choices

| Choice | Reason and rejected alternative | Evidence/limit |
|---|---|---|
| Complete monochromatic four-connected borders | Foreground-union connectivity merges legitimate touching colors; global grouping merges separate same-color frames. | Four canonical pairs and independent Racket component counterexamples. |
| Permit recognized broken-ring boxes in validation | Requiring every pixel to lie in an intact frame would reject canonical overwritten-border examples. | Canonical train 2/test 0; validator is a bounded grammar, not the entire raw rule domain. |
| Four core layouts plus a seeded broad branch | Preserve canonical scale and teach diagonal separation and damaged-frame exclusion while varying height/count. | Anchors are geometry recipes with fresh palettes and contents, never saved input replay. |
| Exact grid height 7..18 and intact count 1..5 | The old difficulty-specific draw bounds contradicted advertised ranges. | Every band uses the entire override range; no post-draw clipping or silent shortening. |
| Real palette and texture aliases | The old helpful textures were inert. A mode must change returned pixels. | Four/five/six nonzero colors as documented; fixed warm/cool sets; conflicting aliases reject. |
| Sparse/dense content | Add meaningful occupancy variation without discarding a requested palette. | Minimum content/full palette can dominate tiny interiors; density is a distribution control. |
| Retire canned degenerate textures | Fixed early-return grids ignored dimensions and counts. | One-frame support is retained through n_frames=1; no-frame/blank-interior raw authority remains tested. |
| Four demonstrations | Repeated diagonal and damaged-frame witnesses supply evidence for the declared rivals. | Final census uses four consecutive demos plus one query, then all five possible query holdouts. |

The palette is permuted across roles, but border and interior colors are disjoint.
This is an explicit current support restriction, not a rule requirement. The
generator does not claim full support for arbitrary nesting, all frame overlaps,
or every hypothesized alternative program.

## Genuine failed iteration and reversal

Candidate v1 appended an extra border at the old canvas width. A core rectangle
can occupy its rightmost column, so the next same-color frame joined it
orthogonally. Seed 10/index 10 produced five planned frames but only three
accepted components and raised. `checks/accidental-frame-v1.json` retains that
input, planned rectangles, actual frames and source hash. The regression first
failed for phase 2; placement now inserts a zero column.

This also explains a teaching defect: the production sampler skipped rejected
phase-2 draws. In the v1 census, all 300 production queries passed the declared
rivals, but 5/1,500 query rotations became ambiguous against `include_broken`.
The saved accepted indices and rejection reasons make that causal link
reproducible. The full failed receipt is preserved, not relabeled as a pass.

An intermediate `LESSON_SCHEDULE_PERIOD=4` declaration was removed after review.
Only the core layout choice has that period; topology and palette variation
depend on the full sample index. Intermediate fixed-start results remain
measured examples, not exhaustive semantic coverage. Final claims use the
ordinary source-bound census and explicit seed/start denominators.

## Scope and current audit state

The existing audit mechanisms are addressed in the selected task. Its
`evidence/review_index.json` is outside the permitted patch surface, so the
maintainer must explicitly resolve `review-fc99ea32bddfe9ee:v0001` after
integration. Both newly drawn audit targets remain findings-only and unchanged.
No reference authority, shared runtime, assignment, safety label, or model
trajectory admission was modified. Query solve correctness is withheld for
independent maintainer scoring.
