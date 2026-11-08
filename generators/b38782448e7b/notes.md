# Working notes: b38782448e7b

## Intended rule

Use the unique modal color as background. A non-background cell in row 0 is an
active marker only when it differs from row 1 in the same column. For each active
column, preserve row 0 and sweep rows 1 downward: marker-colored cells become
background; every other color, including third colors, becomes the marker.
Non-active columns and row-0/row-1-equal top decoys are preserved.

The canonical Racket behavior did not change in review `review-0bdef3bb637751b2`.
The two selected base-solution copies were text-synchronized to the exact canonical
program because `authority_sync` found semantically equivalent but divergent text.

## Review 0bdef3bb637751b2 decisions

The former `2.0.1` sampler generated colored body content only in active marker
columns. Consequently, the wrong rule “erase every unmarked body cell” matched
24/24 sampled generated inputs while failing all three unique canonical examples.
It also exposed no strict observable controls or executable rival contract.

Version `3.0.0` uses canonical-scale 20–30 grids and 3–7 colors, with exact controls
for height, width, background, palette size, active-marker count, and inert-decoy
count. Every default sample includes all four teaching witnesses: an inert top
decoy, preserved colored body content outside active columns, a third-color
overwrite inside an active column, and a marker-equal XOR-off cell. A reserved
54–108-cell same-color component closes the component-scale gap found by
`defect_lint`.

Two intermediate placement choices were reversed during final self-review. First,
the large component was fixed to one side and controls were kept outside it; this
failed to reproduce canonical right-edge controls and never showed a sweep cutting
through a substantial object. The final component position varies across the full
width and one active marker is anchored inside it (`checks/prior-solve-position-
restriction/` retains the superseded solve). Second, scattered random rectangles
and bottom palette swatches produced a median 16 connected objects versus five in
the canonical records. The final sampler attaches every extra color in a compact
two-row mosaic below the large block and keeps each top control connected through
rows 0–2. The exact battery sample is now median 6, maximum 9, inside the canonical
3–10 envelope; the failing run is retained under `checks/after-final/` and the
regression is `test_default_morphology_does_not_fragment_beyond_canonical_object_counts`.

Declared rivals are `all_top_non_background`, `erase_unmarked_body`,
`binary_toggle_only`, and `solid_paint_columns`. `lesson_identifiable` rejects any
lesson whose demonstrations fail to refute one of them. The independently spelled
probe is `workspace/reference_probe.py`; the exact canonical-fitting decoy shortcut
is retained under `counterexamples/review-0bdef3bb637751b2-v0001/` and covered by
focused tests.

## Assumptions and limits

- Background is the unique modal color and grids are rectangular literal ARC grids.
- Heights and widths are 20–30; palette size is 3–7; active markers are 2–6;
  inert decoys are 0–3. An explicit `n_decoys=0` override lawfully removes the
  decoy witness, but production profiles all request at least one.
- The fixed four-rival contract is finite evidence, not a proof against every
  possible induction shortcut.
- The curriculum is contextually gated by row 1. It is a single simultaneous
  column operation; no sequential-state claim is made.
- The authoritative rule remains canonical Racket hash `06479b7ecc39`.
## Current reviewer considerations

Source SHA-256: `3ede0c405c7ba8f04ac45be8236845a7b1cece0899fcaeed56d958ad866840f2`.

# Decisions for `b38782448e7b`

## D1 — Preserve canonical rule behavior

**Choice.** Keep canonical Racket behavior unchanged and pin normalized rule hash
`06479b7ecc39`.

**Rationale.** The rule reproduces all labeled records and the defects were in the
teaching distribution and selected-copy text drift, not the transformation.

**Alternative rejected.** Changing Racket to make every non-background top cell
fire would simplify the canonical examples but would erase the meaningful row-1
gate and contradict accepted counterexamples.

**Probe/failure mode.** Independent Python oracle, canonical labeled pairs, rule
smoke, authority execution parity, and `checks/shortcut-final/racket-final2.json`.
Exact base copies were synchronized only after byte-level authority drift was
observed.

## D2 — Unique modal background

**Choice.** Infer background as the unique modal color and reject tied modes.

**Rationale.** Canonical backgrounds vary (4, 7, 8), while modal occupancy is
stable and directly observable.

**Alternatives rejected.** Fixed color 0 and top-left color both fail canonical
records. Treating a tied mode arbitrarily would make marker classification
ambiguous.

**Limit.** Lawful inputs require a unique mode; this is explicit in `self_check`.

## D3 — Six exact, observable axes

**Choice.** Advertise only `grid_h` 20–30, `grid_w` 20–30, `bg_color` 0–9,
`palette_size` 3–7, `n_markers` 2–6, and `n_decoys` 0–3.

**Rationale.** Each value is exactly recoverable from pixels through
`observe_overrides`; the ranges cover canonical dimensions/palettes and useful
lesson variation.

**Alternatives rejected.** Hidden family/style flags and probabilistic controls
were removed because a caller could not verify them. Unknown keys, booleans,
floats, strings, and out-of-range values now fail loudly.

**Probe/failure mode.** Joint override matrix, strict task tests, and the public
override-contract gate. Exact overrides supersede difficulty/profile defaults.

## D4 — Deterministic canonical profile schedule

**Choice.** Cycle through exact 20×20/palette-3, 30×30/palette-6,
30×30/palette-7, and one broad profile.

**Rationale.** A small deterministic schedule guarantees every canonical
height/width/palette profile in every lesson window while retaining diversity.

**Alternative rejected.** Pure random draws can miss a canonical profile in a
20-draw band and make profile-floor evidence seed-sensitive.

**Limit.** The schedule guarantees these linked marginals; it does not claim the
three canonical examples exhaust all natural morphology.

## D5 — Every default sample carries four semantic witnesses

**Choice.** Include at least one inert top decoy, preserved non-firing body cell,
third-color firing-column cell, and marker-equal XOR-off cell.

**Rationale.** These directly refute `all_top_non_background`,
`erase_unmarked_body`, `binary_toggle_only`, and `solid_paint_columns`.

**Alternative rejected.** Relying on witness frequency across different examples
lets a three-demo lesson omit one discriminator. The final schedule makes each
individual default example sufficient against all four rivals.

**Limit.** Exact `n_decoys=0` is intentionally lawful and omits the first witness;
production defaults never request it.

## D6 — Variable-position large component, sliced by an active marker

**Choice.** Paint a 9-column block with height 6/9/12, vary its horizontal
position across the whole grid, and force one active marker through it.

**Original choice reversed.** An intermediate repair reserved a fixed side for a
large object and kept controls outside it. That made controls positionally narrow
and never demonstrated a sweep through substantial content.

**Evidence for reversal.** Canonical controls reach columns 27–28; the red test
`test_default_controls_span_full_width_and_cut_through_large_components` failed
against the fixed-side draft. The superseded solve is retained under
`checks/prior-solve-position-restriction/`.

**Limit.** The block is rectangular by design. Other attached colors add a small
mosaic, not the full range of canonical multi-rectangle layouts.

## D7 — One attached body mosaic instead of scattered decorations

**Choice.** Put every extra palette color in a contiguous two-row band attached
below the large block, and connect each top control through rows 0–2.

**Original choice reversed.** Random body rectangles plus detached bottom
swatches preserved semantics but produced median 16 / maximum 23 connected
objects; canonical records contain 3, 5, or 10.

**Evidence for reversal.** `checks/after-final/` failed `dist_gate` at generated
median 16 versus canonical median 5. The new red→green morphology test constrains
the same 60-input sample to the canonical envelope. Final counts are median 6,
maximum 9.

**Alternative rejected.** Weakening the distribution gate or accepting its
“diagnostic” label would ship an avoidable teaching mismatch.

## D8 — Finite executable rival contract

**Choice.** Publish executable `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`,
`WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, and `lesson_identifiable`.

**Rationale.** Named prose claims are insufficient; the sampler can now reject a
lesson whose demonstrations fail to refute a declared competitor.

**Probe.** Exhaustive four-pair cyclic windows in focused tests and 300 lessons /
1,200 rotations in the source-bound census.

**Limit.** Passing a finite competitor set is not a proof of unique induction.

## D9 — Retain exact shortcut witness

**Choice.** Keep a minimal lawful 20×20 decoy case under
`counterexamples/review-0bdef3bb637751b2-v0001/`.

**Rationale.** The strongest plausible shortcut fits all six usable labeled
canonical records, so a permanent Racket-bound counterexample is more durable
than a frequency statistic.

**Failure mode.** Removing default decoys would revive the shortcut even if all
individual labels remained correct.

## D10 — No edits to audit targets

The two random audits were adversarial reviews only. Their concrete findings are
recorded in `AUDIT.md` and `checks/audit/`; source for `3194379886a5` and
`48bda9528e71` was left unchanged.

## D11 — Proposed episode-fixed gated-XOR parameters

**Choice.** Keep production and the canonical rule unchanged, and retain a
separate task-local prototype with two bounded parameters chosen once per
episode: `gate_mode` (`different` canonical or `same`) and
`third_color_mode` (`overwrite` canonical or `preserve`). The exact
`different/overwrite` program is byte-for-byte canonical.

**Rationale.** Both parameters alter a single local decision while preserving the
family's reasoning pattern: infer the modal background, classify a top control
against row 1, then apply a vertical marker/background sweep. Inputs deliberately
carry equal and unequal controls plus third-color body witnesses, so all four
settings remain executable and distinguishable rather than becoming decorative
metadata.

**Evidence.** `workspace/parametric/prototype.py` emits one fixed setting per
episode with independently configurable demonstration/query counts. The retained
batch has four settings, three demonstrations, four distinct queries, protected-
Racket labels and rival predictions, content-derived public IDs, separate private
answers/programs, and a verifier that reexecutes labels and rejects public or rule
byte tampering. The verifier additionally binds the manifest to the exact public/
private episode inventory and private metadata, rejecting dropped, duplicated,
redirected, or relabeled rows before replay. Focused tests are in
`tests/test_parametric_gated_xor.py`; retained
receipts are under `checks/parametric/` in review `review-2437a32484ba25e8`.

**Implementation ruling.** Evidence writers and verifiers accept an optional
caller-owned `RacketBridge`. Reusing one protected bridge keeps the full focused
suite bounded while the default CLI still owns and closes its bridge.

**Limits / next action.** This is finite evidence for four declared settings and
seeds 0–3, not variant approval or proof against arbitrary alternative rules.
Owner-side promotion still requires a separate adapter/identity decision and
fresh qualification; do not alter the production generator, canonical hash
`06479b7ecc39`, or training status merely because this prototype passes.

## D12 — Current native admission candidate: gated toggle then completed-column relay

**Choice.** Keep the production generator and canonical authority unchanged. Add
a native two-setting family under `workspace/parametric/`: `toggle_only` is exact
canonical source, while `toggle_then_relay` completes the gated vertical toggle,
counts marker-colored cells in each completed active column, chooses the unique
maximum, and copies that full processed column into the lane immediately left of
the visible bottom color-9 cue.

**Why this supersedes the older proposal.** The retained gate/third-color
prototype is useful provenance but does not meet the current round's required
sequential causal depth. The new Stage B consumes a completed Stage-A column; a
raw-column substitute produces a different relay pattern.

**Teaching and adversarial design.** Inputs are setting-neutral. The minimum two
demonstrations reject identity, first/last/minimum-column selectors, raw-source
relay, wrong-side cue placement, ungated controls, and canonical-only shortcuts.
Profiles support 2–6 demonstrations and 1–4 prefix-stable queries; the fourth
query is 30×30, dense, and touches all four boundaries.

**Evidence.** 64 task tests and 20 focused tests pass. A finite audit covers 48
episodes and 184 wrong-intermediate pair checks. Four native qualification jobs
(two settings × seeds 0 and 17) execute 32 protected-Racket labels. Qualification
and execution replay byte-identically. The protected causal witness relays the
raw source column instead of the completed column and changes 12 final cells.

**Limits / next action.** The rival audit is finite and does not prove uniqueness
against arbitrary rules. Owner exact-source integration, fresh qualification,
acceptance replay, and any training-admission decision remain pending. Keep the
older gated-XOR prototype as provenance, not as the current candidate.
