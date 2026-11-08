# Working notes: 7f3446077e8e

## Review-d88b3128159c888d

Baseline measurements found seven failing battery stages.  The generator
rejected the lawful clipped canonical example, emitted four rather than five
colors, exposed dead/ignored controls and typo acceptance, lacked its rule pin
and semantic contract, and its selected active Racket text mirror differed
from the unchanged canonical/raw text.

The repaired generator uses a strict five-axis grammar, canonical-scale size
cycle, connected 3–9-cell shapes, one connected nuisance decoration, and
constructive full/clipped placement.  Axial and diagonal vectors alternate;
full and clipped visibility alternate in two-sample blocks.  This makes every
four consecutive examples contain two axial cases, including after any one
pair is held out as query.

Strongest known canonical shortcut: apply the translation only when both marker
vector components are nonzero.  It fits all five labeled canonical pairs, whose
vectors are diagonal.  An axial vector is the decisive witness.  The task-local
`workspace/shortcut_probe.py` independently checks canonical fit, all four
single-query holdouts in consecutive windows, and retains an exact witness.
The live-Racket `lesson-census` remains the stronger label-provenance check.

Final measured state: 12/12 after-battery stages green; 23/23 task tests pass;
300/300 source-bound lessons and 1,200/1,200 query rotations show zero ambiguity
against the declared rival.  These finite checks do not prove uniqueness
against undeclared hypotheses, and curriculum assemblers that skip indices must
re-run the schedule probe.
## Current reviewer considerations

Source SHA-256: `3146c22edbb65aa174c6396ec59afc65de53d152e4739c33d1160f251ff1865b`.

# Design and review decisions — 7f3446077e8e

## D1 — Preserve the rule; repair provenance only

**Choice.** Keep the canonical Racket program unchanged and pin its normalized
hash as `RULE_HASH = "5d4c6d9ec409"`.  Replace only the selected redundant
`racket_target.target_code` text with its already-identical `raw_code`/canonical
text.

**Why.** The baseline rule smoke test passed and direct inspection showed that
the active text difference was comments/formatting, not behavior.  Changing the
rule to accommodate the old generator would have altered a lawful clipped
canonical example.

**Rejected alternative.** Modify the Racket rule or weaken authority-sync.  That
would hide provenance drift and was unnecessary.  Final `rule_smoke`,
`racket_lint`, and `authority_sync` are green.

**Failure mode.** Downstream systems that key on the redundant text hash will
see a source-identity change even though behavior is unchanged.

## D2 — Own the complete lawful canonical grammar, including clipping

**Choice.** Validate 9–12 by 10–12 grids with exactly five colors, one connected
3–9-cell color-2 object, one 8, one 9, one connected 1–2-cell nuisance color,
a nonzero vector, a nonempty visible copy, and no destructive overlap.  Accept
both fully visible and partially clipped translations.

**Why.** One of five canonical inputs clips one source cell out of bounds.  The
baseline's “fully in bounds” assumption caused `selfcheck` and profile support
to fail despite the Racket rule explicitly clipping.

**Rejected alternative.** Treat the clipped canonical pair as an exception or
emit only full copies.  That would preserve a false domain restriction and make
training underrepresent an observed branch.

**Probe.** Canonical acceptance is 5/5; focused tests compare an independent
coordinate oracle with all five labels.  `copy_visibility` is observed from
pixels, not metadata.

**Failure mode.** The grammar deliberately excludes target overlap with source,
markers, or decorations; the broad Racket program can define such cases, but no
canonical pair requires them.  Expanding that domain needs separate witnesses.

## D3 — Replace misleading axes with five exact observable controls

**Choice.** Public axes are `grid_h` 9..12, `grid_w` 10..12, `shape_size` 3..9,
`decoration_size` 1..2, and `copy_visibility` full/clipped.  Unknown keys and
wrong Python types fail closed; integer axes use `draw_int_strict`.

**Why.** The baseline advertised palette, distinct-color, position, and texture
controls it did not honor; it silently accepted typos and generated four colors
against a five-color canonical distribution.

**Rejected alternative.** Keep compatibility aliases for dead controls.  That
would leave provenance dishonest and multiply the override matrix without a
semantic benefit.

**Probe.** Final override gate: 12,780/12,780 accepted draws over 142 cases,
three bands, zero findings.  Task tests cover valid exact controls in every band
and bool/float/out-of-range/unknown negatives.

**Failure mode.** Decoration color is intentionally varied internally rather
than exposed; callers cannot pin it.  It is semantically irrelevant and still
keeps the palette at exactly five colors.

## D4 — Construct layouts rather than retrying an invalid fallback

**Choice.** Grow compact connected polyominoes, enumerate candidate directed
vectors and legal placements, then place markers and decoration in remaining
cells.  Raise a diagnostic `RuntimeError` if construction is impossible; never
return the last invalid attempt.

**Why.** The baseline's rare `return g` fallback could return stale/invalid
state.  Constructive checks make exact overrides reliable, including the joint
maximum shape/decoration sizes and clipping.

**Rejected alternative.** Increase a random retry count.  That would reduce but
not remove an unverified fallback and make rare failures seed-dependent.

**Probe.** Focused tests exercise the contract; the official override matrix
covers 12,780 draws.  The final battery's self-check, diversity, and defect lint
all pass.

**Failure mode.** Shapes are compact (bounded within 4×4 during random growth,
with a 3×3 deterministic fallback).  This is a deliberate morphology limit,
not a claim that every connected 9-cell polyomino is sampled.

## D5 — Schedule the strongest canonical-fitting counterexample

**Choice.** Alternate vector mode by sample index: even indices are purely axial,
odd indices diagonal.  Alternate full/full/clipped/clipped visibility in a
four-sample cycle.  Every four consecutive pairs therefore contain exactly two
axial cases.

**Why.** All five canonical marker vectors are diagonal, so “translate only when
both components are nonzero” fits every canonical label.  Random witness
frequency does not ensure every lesson teaches against it.  With the period-two
vector schedule, any one-pair holdout from four leaves at least one axial demo.

**Rejected alternatives.** Pure random vectors could produce witness-free
lessons.  Making every sample axial would overcorrect and underrepresent the
canonical regime.  A fixed query position only would not support rotations.

**Probe.** The declared rival/witness passes the official semantic gate.  The
live-Racket census reports 300/300 lessons, 1,200 unique inputs and 1,200/1,200
single-query rotations with zero ambiguity.  The independent task-local probe
checks 432 overlapping windows and 1,728 rotations over all three bands with no
schedule failure.

**Failure mode.** The guarantee assumes consecutive sample indices.  An exporter
that skips indices or assembles fewer than three demonstrations must recheck.
Finite rival coverage is not a universal induction proof.

## D6 — Keep canonical-scale profiles visible in every band

**Choice.** Cycle through the five observed `(height,width)` profiles regardless
of difficulty, while difficulty changes the keyed layout randomness.  Shape
size and decoration size also cycle through their declared domains.

**Why.** The baseline missed exact canonical size/palette profiles entirely.
Band-exclusive dimensions would make exact controls inconsistent and could
remove canonical anchors from a band.

**Rejected alternative.** Use larger hard-only canvases.  The task's semantic
complexity comes from vector direction, clipping, and shape, not raw canvas
size; all bands should remain on the canonical manifold.

**Probe.** Profile floor passes in all bands.  A test checks canonical-profile
intersection across ordinary draws.  A separate red/green regression proves
that difficulty affects generated bytes; this fixed the intermediate dead-band
failure.

**Failure mode.** Difficulty is a nuisance-layout variation, not a calibrated
human difficulty model.

## D7 — Independent reusable probe plus live-Racket census

**Choice.** Add `workspace/shortcut_probe.py` with its own coordinate oracle,
canonical rival-fit check, schedule enumeration, rotated-query scoring, source
hash, and retained exact axial counterexample.  Use the shared live-Racket
census as the stronger label-provenance check.

**Why.** Calling only production helpers could repeat the same implementation
mistake, while a task-local Python probe alone cannot establish authority parity.
The two checks cover different failure modes.

**Rejected alternative.** A one-off notebook or prose-only claim.  Future agents
need a rerunnable, source-bound artifact.

**Failure mode.** Both checks cover the declared `diagonal_only` rival only.
Undeclared alternatives remain possible and should be added when discovered.

## D8 — Evidence and scope discipline

No prior returned patch was used as a lead; the selected pinned baseline and
fresh before battery were treated as ground truth.  The empty working notes and
associated evidence did not supply a repair.  The baseline completed with four
green, one advisory, and seven failed stages.  A second accidental launch then
recorded an active-writer exit; that collision log is not the baseline verdict.

The canonical rule did not change.  Two audit targets were findings-only and
left untouched.  Private query correctness for both solve episodes remains
withheld, so only visible-example results are reported.
