# Working notes: 2b7bcfbf942b

## Baseline reproduced

The selected baseline SHA-256 was
`113e6aace3f1542fe6da60a07a5fd66afa699c8ff8c64702b1b44bf4fa146c88`.
It always emitted two fixed `3x4` templates at fixed corners, despite the
canonical set containing one- and two-object inputs with `5x5`, `6x4`, `6x6`,
and `6x7` bounding boxes.  Several advertised controls were inert, malformed
canonical inputs were rejected, semantic hooks were absent, and the two active
Racket authority copies differed by one comment.  The before battery reported
5 green, 1 advisory, and 6 failed stages; see
`checks/before-full/checks/2b7bcfbf942b_before_battery_summary.json`.

The prior return `review-2c6a6bb78f6b9f5d:v0001` in
`evidence/review_index.json` was used only as a lead.  All claims above were
remeasured against the pinned source in this packet.

## Selected design

Version `3.0.0` treats each same-color 4-connected component as a bounding-box
cue.  It emits one to three distinct-color, nonoverlapping objects on canvases
from `8x9` through `16x18`.  Objects use one shared visible style per input:
complete frame, one-side-open frame, or cross.  The style is tied to
`sample_index mod 3`; therefore any three consecutive default samples contain
all three styles.  Bounding-box size and placement are drawn independently
inside horizontal or vertical slots.

Five canonical canvas/object-count profiles recur in a six-step cycle, while
the sixth draw and all exact overrides exercise the full domains.  The
canonical prior does not clamp exact overrides.  Unknown axes, booleans for
integer axes, out-of-range values, and invalid style tokens are rejected
explicitly.

## Semantic contract

Two executable rivals fit every usable canonical pair:

1. `complete_frames_only`: leave open frames and crosses unchanged.
2. `canonical_bbox_sizes_only`: transform only bounding-box dimensions seen in
   the canonical set.

The witnesses `non_frame_object` and `novel_bbox_size`, together with
`lesson_identifiable`, make those rivals testable.  The final source-bound
census materialized 300 lessons (100 per band, 3 demos plus 1 query), covering
1,200 inputs and 1,164 distinct inputs across bands.  Both rivals were refuted
by the demos in all 300 lessons; there were zero generation, validator,
override-observation, hook, or Racket execution errors.  This is a finite
census, not a universal induction claim.  Evidence:
`checks/lesson-probe.json`.

## Verification state

Final generator SHA-256:
`80347e1ab7738e138903f5174669b89b973e342a3b4574e963cd419ccf70ac3c`.
The after battery is 12/12 green; see
`checks/after/checks/2b7bcfbf942b_after_battery_summary.json`.  The selected
Racket behavior was not changed.  One nonsemantic comment was removed from the
bank copy so the active authority texts are byte-for-byte synchronized, and
`RULE_HASH = de72b7a33ad3` pins the canonical rule.

## Tooling and retained failure

`workspace/reference_probe.py` supplies an independent component parser,
geometry oracle, two shortcut implementations, exact witnesses, distribution
summaries, and optional real-Racket parity.  `workspace/lesson_probe.py`
stages the portable runtime and performs a source-bound lesson census through
one persistent Racket bridge.

The first lesson-probe report is deliberately retained at
`checks/lesson-probe-failed-v1.json`: its canonical-fit precheck forgot that
some canonical rows use compact strings.  A regression test was first observed
failing (`checks/lesson-probe-tdd-red.log`), then the decoder was corrected.

## Remaining limitations

The admitted grammar intentionally remains finite: one to three objects,
three cue styles, distinct colors, nonoverlapping bounding boxes, and one style
per input.  The selected Racket rule can execute on a broader set of connected
components than this validator admits.  The masked post-repair query remains
unscored in reviewer-visible feedback; only the three visible examples were
confirmed.
## Current reviewer considerations

Source SHA-256: `80347e1ab7738e138903f5174669b89b973e342a3b4574e963cd419ccf70ac3c`.

# Decisions for `2b7bcfbf942b`

## D1 — Treat the canonical rule as per-component bounding-box completion

**Choice.** Parse same-color 4-connected components and let each component's
bounding box define the completed border and local checker interior.

**Rationale.** This matches all five canonical input/output pairs and the
selected Racket authority.  The baseline instead encoded two particular
hexomino templates.

**Alternatives rejected.** Keeping the two fixed templates, or merely
randomizing their locations, would preserve the same shortcut.  Treating all
nonzero cells as one object would fail multi-color canonical cases.

**Probe/failure modes.** `workspace/reference_probe.py` uses an independently
written component parser and geometry oracle.  Same-color touching components
would merge by rule semantics; the generator avoids that ambiguity with
nonoverlapping boxes and distinct object colors.

## D2 — Use a canonical-profile prior without clipping the declared domain

**Choice.** Cycle five canonical canvas/object-count profiles in the first five
positions of a six-step schedule, then use a broad draw; exact overrides always
select from the full domains.

**Rationale.** Regular canonical morphology is needed for profile-floor checks,
but the generator must also cover `8..16` rows, `9..18` columns, and one to
three objects.

**Alternatives rejected.** Pure broad random sampling made profile hits
probabilistic.  Hard-coded canonical-only dimensions would teach a size table
rather than the rule.

**Probe/failure modes.** Final profile-floor and override stages are green.  The
300-lesson census records every observed dimension and object count by band.
The prior is deterministic, so consumers should not treat frequency as a
natural-world distribution.

## D3 — Partition the canvas before drawing independently sized boxes

**Choice.** Select horizontal or vertical contiguous slots and draw each
object's box independently inside its slot.

**Rationale.** Slotting guarantees nonoverlap and fit while retaining variation
in box size, margin, position, and layout direction.

**Alternatives rejected.** Rejection-sampling arbitrary boxes complicated exact
`n_objects=3` support on small canvases.  Fixed corners reproduced the baseline
collapse.

**Probe/failure modes.** The validator independently checks nonoverlap and
minimum `3x3` boxes.  The finite grammar does not cover overlapping or nested
objects even though the Racket rule may execute on some such inputs.

## D4 — Add open frames and crosses as semantic teaching cases

**Choice.** Cycle `frame`, `open`, and `cross` by `sample_index mod 3`; all
objects in one grid share the style.

**Rationale.** Every canonical object is a complete frame, so the strongest
plausible shortcut is “only complete frames transform.”  Open frames and
crosses have the same observable bounding-box cue but directly separate that
shortcut from the intended rule.  A three-example default lesson necessarily
contains non-frame evidence.

**Alternatives rejected.** Random style choice could produce whole lessons of
frames.  Arbitrary random connected shapes would broaden the validator faster
than the teaching evidence could be audited.

**Probe/failure modes.** `complete_frames_only` is executable and fits all five
canonical pairs.  In the final 300-lesson census it was refuted by the demos in
300/300 lessons.  Sharing one style per input makes the cue obvious but is a
stated distribution restriction.

## D5 — Vary bounding-box dimensions beyond the canonical set

**Choice.** Draw each box from all sizes that fit its slot and declare
`canonical_bbox_sizes_only` as a second rival.

**Rationale.** A learner could otherwise memorize the four canonical box-size
classes.  Novel-size inputs distinguish general bounding-box completion from
that lookup table.

**Alternatives rejected.** Emitting only the canonical sizes would optimize
profile resemblance at the cost of rule generality.  Forcing every input to be
novel would lose useful canonical anchoring.

**Probe/failure modes.** `novel_bbox_size` hit the demos in all 300 sampled
lessons; the rival was refuted in all 300.  This is measured support, not proof
against every size-based program.

## D6 — Advertise only exact controls that are observable and enforceable

**Choice.** Keep four exact axes (`grid_h`, `grid_w`, `n_objects`,
`object_style`), validate exact types and domains before generation, reject
unknown keys, and recover all four through `observe_overrides`.

**Rationale.** The baseline advertised controls that did not change output.
The smaller contract is falsifiable and useful.

**Alternatives rejected.** Retaining decorative axes such as palette labels or
position bias would require distinct observable semantics not justified by the
task.  Silently accepting unknown keys hides caller mistakes.

**Probe/failure modes.** The final exhaustive override matrix is green.  Colors,
box sizes, placement, and layout still vary through keyed internal draws but
are intentionally not exact public axes.

## D7 — Make semantic claims executable

**Choice.** Declare `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`,
`SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `strict_canonical_like`, and
`lesson_identifiable` in the selected generator.

**Rationale.** Distribution diversity alone cannot show that demonstrations
teach the rule.  Executable rivals and witnesses let the battery and larger
probe test the actual claim.

**Alternatives rejected.** Prose-only assertions and raw witness frequencies do
not establish that each complete lesson refutes a shortcut.

**Probe/failure modes.** The task-local lesson probe reads the declarations
dynamically and tests complete lessons.  It cannot enumerate all possible
programs and says so in its report.

## D8 — Keep the executable Racket rule unchanged

**Choice.** Pin `RULE_HASH = de72b7a33ad3` and remove one nonsemantic comment
from the duplicate bank copy so all active texts synchronize exactly.

**Rationale.** Canonical outputs and the selected authority already agreed; the
defect was the generator, not rule behavior.

**Alternatives rejected.** Rewriting the rule would add unnecessary authority
risk.  Ignoring the comment-only divergence would leave authority-sync red.

**Probe/failure modes.** Rule smoke, Racket lint, authority sync, and execution
parity are green.  The byte-level authority-set hash changed only because the
comment was removed.

## D9 — Add independent probes and preserve a failed iteration

**Choice.** Build `reference_probe.py`, `lesson_probe.py`, and task-local tests;
retain the initial lesson-probe failure and its red regression run.

**Rationale.** Future agents need reproducible geometry, Racket parity, and
lesson-level semantic checks rather than another prose audit.

**Alternatives rejected.** Calling generator-private helpers alone would make
qualification circular.  A small battery sample alone was insufficient for a
lesson-identifiability claim.

**Probe/failure modes.** The first lesson probe forgot to decode compact string
rows in canonical data.  `checks/lesson-probe-failed-v1.json` and
`checks/lesson-probe-tdd-red.log` preserve that failure; the final 300-lesson
run is green.  The independent oracle intentionally duplicates some geometry
logic, so both Python and real-Racket parity are checked.

## Native parametric review — 2026-10-25

**Decision.** Add one episode-fixed semantic axis, `checker_phase`, while
preserving the exact canonical default. `colored_first` uses the catalog program
byte-for-byte; `zero_first` flips only the strict-interior checker phase relative
to each component's own derived bounding-box origin.

**Teaching construction.** Inputs are identical across settings. The first two
examples jointly include complete frames, open frames, crosses, several colors,
odd global offsets, and even box widths. They distinguish the phase and reject
the retained global-parity, top-right-anchor, frame-only, largest-only,
fixed-color, incomplete-border, canonical-size, border-only, and solid-fill
shortcuts at the two-demo minimum. This remains a finite rival set rather than a
universal identifiability claim.

**Controller contract.** The adapter supports independent stable prefixes for
2–6 demonstrations and 1–4 queries. Four distinct controller-side queries are
revealed one at a time without settings, programs, answers, future inputs, or a
total-count hint. Their shapes are 12×15, 18×20, 24×27, and 30×30. The largest
contains five separated objects, five colors, 125 source cells, and contact on
all four grid boundaries.

**Sequential dependency.** Step A extracts same-color four-connected components
and derives each input-dependent bounding box and local interior origin. Step B
consumes those records to complete borders and fill checker interiors. Shifting
the derived row origin by one changes 274 protected-Racket output cells in the
retained counterfactual witness.

**Evidence.** The final changed-target suite passes 198/198 tests. An earlier
run was interrupted by the packet's default command window after 45 tests; the
same exact suite was rerun with `--timeout 600` and completed green. The reusable
self-audit passes 42 protected-Racket executions plus 256 deterministic Python
stress episodes. Native qualification passes four setting/seed jobs with 40
protected-Racket labels, and the source-bound witness is independently marked
`reviewer_replayed`. Sixteen saved public views pass both projection verification
and the independent public-only conformance checker. Production `generator.py`
remains at SHA-256
`80347e1ab7738e138903f5174669b89b973e342a3b4574e963cd419ccf70ac3c`;
the canonical program remains at
`98e504de0fa43587bd343eea5c0cea3eb76ba5ec3dbd9963f979102dab09ddc2`.
Owner exact-source acceptance remains pending and no training admission is
claimed.
