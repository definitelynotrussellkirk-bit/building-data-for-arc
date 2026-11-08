# Working notes: dcfb4c64c914

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `9c665258ec35ed487f525a5ad8a66434b19146776ac6d877e13d72102ec10e47`.

# Decisions for dcfb4c64c914

## D1 — Treat panel contents as independent connected objects

**Choice.** Analyze one monochrome 4-connected object in each panel and count
cells in rows relative to that object's own bounding box.

**Original rationale.** Unknown. The frozen `2.2.0` source described
left-justified bars anchored to each panel edge, but that description conflicts
with all three canonical inputs and the selected Racket implementation.

**Alternatives considered.**

- Patch only `self_check` to accept translated bars. Rejected because generation,
  summary text, and the output mirror would still teach absolute canvas-row
  alignment.
- Preserve panel-edge bars but translate both objects together. Rejected because
  it would continue to hide the strongest canonical-fitting shortcut.
- Add multiple objects and rely immediately on the Racket largest-object
  tie-break. Deferred because it adds object-selection inference before the
  profile rule is securely taught.

**Probe.** The independent analyzer in
`generators/dcfb4c64c914/workspace/reference_probe.py` matches all three
canonical outputs and twelve direct Racket evaluations in the task tests.

**Failure mode / limitation.** Current generated panels contain exactly one
object, so the Racket largest-object tie-break is supported by the probe but not
part of the teaching distribution.

## D2 — Use object-local alignment, not absolute canvas rows

**Choice.** At least two of the four schedule slots vertically stagger object
bounding-box tops. Profile index 0 always means the first row of each object's
own bounding box.

**Rationale.** Every canonical demonstration happens to align object tops, so
absolute canvas-row subtraction produces the same labels and is the strongest
plausible shortcut.

**Rejected alternative.** Leave placement random and hope staggered examples
appear. Rejected because a three-example lesson could omit the necessary witness.
The deterministic schedule gives redundant support even after any one pair is
held out as the query.

**Probe.** `checks/shortcut/dcfb4c64c914/case.json` retains an exact 8×15 input
where the Racket output has five rows but the canvas-aligned rival has six.

**Failure mode / limitation.** The schedule guarantees aligned and staggered
modes, but does not explore every legal vertical offset.

## D3 — Distinguish row cell count from occupied span

**Choice.** `geometry_mode="gapped"` creates a connected object with a row whose
occupied columns are `{0, 2}` under a wider bridging row. Its profile value is 2,
while its horizontal span is 3.

**Rationale.** Contiguous bar rows make cell count and horizontal span
observationally identical.

**Alternative considered.** Add disconnected cells. Rejected because the task's
selected objects are 4-connected and disconnected noise would introduce an
object-selection question.

**Probe.** The `internal_gap_cell_counting` witness maps to
`bbox_span_profile`; the final semantic gate reports 60/60 checked witness cases
disagreeing with that rival.

**Failure mode / limitation.** Gaps are small and horizontal; more elaborate
shapes are unnecessary for this distinction and could obscure the arithmetic.

## D4 — Make five axes exact and observable

**Choice.** Replace the baseline's dimensions, palette aliases, density, and
texture controls with:

1. `layout` — exact grid dimensions;
2. `profile_case` — exact zero-padded relation between profiles;
3. `geometry_mode` — contiguous or internally gapped rows;
4. `placement_mode` — aligned or staggered object tops; and
5. `color_pair` — exact ordered left/right colors.

Unknown keys, wrong types, and values outside a domain fail loudly.

**Rationale.** The old API advertised controls it did not consume or could not
honor under every difficulty. Exact axes make replay, audit, and joint override
coverage meaningful.

**Alternatives considered.** Keep `grid_h`, `grid_w`, `maxw`, and palette aliases
with compatibility rules. Rejected because many combinations are structurally
coupled and would need a large incompatibility matrix; the observable semantic
axes are smaller and more useful.

**Probe.** The focused test enumerates all
`4 × 5 × 2 × 2 × 4 = 320` combinations and round-trips each grid through
`observe_overrides`. The battery override stage is green.

**Failure mode / limitation.** Layout values are four named profiles rather than
arbitrary dimensions. This is intentional: every advertised value is lawful and
canonical-size support is guaranteed in each band.

## D5 — Use a four-slot deterministic teaching schedule

**Choice.** Four consecutive pairs are:

1. canonical 8×15, left taller mixed, gapped, staggered, colors 2/4;
2. canonical 9×15, equal left-dominant, contiguous, aligned, colors 4/2;
3. canonical 9×17, equal right-dominant, gapped, staggered, colors 1/7; and
4. wide 10×19, right taller mixed, contiguous, aligned, colors 3/9.

`EXAMPLES_NEEDED = 3`; any one slot may be the query.

**Rationale.** Every three-pair holdout retains a staggered case, a gapped case,
an unequal-height case, and evidence for both directions before absolute value.
This gives deterministic teaching support instead of probabilistic witness
frequency.

**Alternatives considered.**

- Three total schedule slots. Rejected because holding one out could remove the
  only witness for a rival.
- Fully random lessons with rejection sampling. Rejected because replay and
  exact override behavior become harder to inspect, and rare ambiguous windows
  remain possible.
- More demonstrations. Rejected as unnecessary after all four rotations passed.

**Probes.** The task test checks all four holdouts at every difficulty. The large
census checks 300 production lessons and 1,200 rotations.

**Failure mode / limitation.** The schedule is intentionally periodic by
`sample_index % 4`; numerical profiles remain seed-dependent, but the five
observable axis tuples repeat every four pairs.

## D6 — Generate profiles constructively, with difficulty only in latent complexity

**Choice.** Draw profile lengths and values from constraints that guarantee each
named relation. Easy uses shorter/smaller profiles, hard uses the maximum
five-row extent and wider counts, while all declared axes remain unchanged.

**Rationale.** A small fixed bank would pass structural checks but collapse
output diversity. Letting difficulty alter declared axes would make exact
controls unreliable.

**Alternative considered.** Store a curated profile bank. Rejected after defect
lint showed that identical difficulty outputs and small banks are observable
quality defects.

**Probe.** The final regression sample has at least 60 unique medium outputs in
160 draws; direct measurement produced 91, 140, and 152 unique outputs for easy,
medium, and hard respectively. Difficulty tests require at least two distinct
grids for each schedule slot while observed axes remain identical.

**Failure mode / limitation.** Counts are capped at 5 to fit all named layouts;
this is a bounded curriculum, not exhaustive row-profile arithmetic.

## D7 — Declare executable rivals and witnesses

**Choice.** Retain six competitors:

- `canvas_row_alignment`;
- `bbox_span_profile`;
- `left_minus_clamped`;
- `right_minus_clamped`;
- `truncate_shorter`; and
- `sum_profiles`.

Map them to five semantic witnesses and implement `lesson_identifiable` over the
actual labelled demonstrations/query.

**Rationale.** Correct labels do not guarantee that demonstrations teach the
intended rule. Executable competitors make the claim falsifiable.

**Alternative considered.** Rely on prose explanations or a single solve. Rejected
because neither measures generated lesson ambiguity.

**Probe.** The final semantic gate and 300-lesson census report no survivor among
these rivals in production or any single-pair query rotation.

**Failure mode / limitation.** The rival set is finite. It covers the main
canonical shortcuts but cannot establish universal program identification.

## D8 — Keep the selected Racket authority unchanged

**Choice.** No canonical or archival rule source was edited.

**Rationale.** Rule smoke and direct probes showed that the selected authority
was internally consistent and matched retained canonical labels. The defect was
in generator-domain modeling and validation.

**Probe.** Final rule hash is `53fe6f709bdc`; `rule_smoke`, `racket_lint`, and
`authority_sync` are green. Direct Racket parity is also covered by task tests.

**Failure mode / limitation.** An archival source remains divergent, as already
reported by `authority_sync`; selected execution parity is green and this repair
does not attempt archival cleanup.

## D9 — Preserve independent solve evidence honestly

**Choice.** The blind task was completed before opening repair material. The
post-repair solve records earlier exposure as `yes` and reference consultation
during solve as `no`.

**Rationale.** Visible-only solve evidence is useful only when its exposure state
is explicit.

**Probe.** `solve-blind/summary.json` and `solve/summary.json` are frozen by their
respective `FINISHED_NOTES.md` hashes.

**Failure mode / limitation.** Passing visible examples does not reveal private
query correctness; no such claim is made.
