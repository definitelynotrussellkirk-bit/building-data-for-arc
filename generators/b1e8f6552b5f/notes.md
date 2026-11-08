# Working notes: b1e8f6552b5f

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `dd6e83a8125e0ed57482908f7eccf57a1142fce6dbaa59af99f7588aa3a060fe`.

# DECISIONS — b1e8f6552b5f

## D1 — Keep the canonical transformation and Racket authority unchanged

**Decision.** Preserve the rule: every isolated interior nonzero marker becomes an empty-centered hollow 3×3 ring in its own color on a fresh zero background. Keep `RULE_HASH=94525d5f470a` and do not edit canonical/base Racket source.

**Rationale.** All five canonical pairs pass the Python mirror; before and after rule-smoke and authority-sync stages are green. The reproduced defect was in generated input scheduling, not label authority.

**Rejected alternative.** Editing Racket to accommodate override artifacts would change correct labels to hide a distribution bug.

**Failure mode / future check.** Any later canonical source edit must update the hash and rerun rule smoke, canonical parity, and authority synchronization.

## D2 — Preserve all four scheduled teaching profiles under compatible overrides

The schedule remains:

1. `aligned_same_pair`: two same-color markers with aligned/touching geometry;
2. `canonical_distinct_pair`: two distinct, fully interior markers;
3. `mixed_triple`: three markers with repeated color and both border-touching/interior evidence;
4. `distinct_quad`: four distinct, fully interior markers.

**Decision.** A dimension override does not, by itself, turn off these predicates. Strict profile search is used whenever `n_markers` equals that profile's required cardinality.

**Rationale.** The schedule exists to make four-demo lessons falsify fixed-count, unique-color-only, and border-selection shortcuts. v3.0.0 silently discarded it under any override: 4,933/7,200 compatible draws violated their profile. v3.0.1 records 0/7,200.

**Rejected alternatives.**

- Preserve profiles only when there are no overrides: this is the defect.
- Preserve profiles only when dimensions equal one preferred size: unnecessary and would make exact size controls semantically inconsistent.
- Infer strictness from whether an override value equals an ordinary draw: unstable because ordinary dimensions are randomized.

**Known limitation.** The profile/cardinality table is task-specific. A future profile addition must add its cardinality and a focused regression.

## D3 — Relax only profile extras when marker cardinality is incompatible

**Decision.** If an explicit `n_markers` changes the scheduled profile's cardinality, honor the exact marker count and enforce the core grammar, but do not claim the original profile geometry. If strict geometry is impossible at requested dimensions, use the existing non-strict placement fallback while retaining exact dimensions and marker count.

**Rationale.** Exact controls are API promises. A two-marker request cannot honestly satisfy a triple profile, while a small legal canvas may not realize every schedule-only relation even though it can still contain lawful nonoverlapping markers.

**Rejected alternative.** Reject every profile/cardinality mismatch. The public axis contract advertises all 2..4 marker values and the generic override matrix expects constructible boundary tuples.

**Failure mode / future check.** Shared tooling should distinguish “explicitly incompatible” from “silently relaxed”; see F1 in `FEEDBACK_TO_CODEX.md`.

## D4 — Keep dimensions 7..13 and marker count 2..4

**Decision.** Preserve the existing `grid_h`, `grid_w`, and `n_markers` domains and difficulty-aware defaults.

**Original rationale.** The imported review broadened canonical support while retaining room for nonoverlapping 3×3 footprints and enough objects to demonstrate repeated colors and count-sensitive rivals.

**Probe.** Exact boundary cases pass in all bands; the final profile probe covered height-only, width-only, and combined dimensions with at least 125 unique grids per 200-draw slice.

**Rejected alternatives.** Shrinking dimensions to canonical-only sizes would reduce nuisance variation; expanding below 7 or above 13 lacks task evidence and would change the advertised grammar.

## D5 — Keep collision, clipping, and border-marker exclusions

**Decision.** Continue requiring marker centers to be interior and 3×3 footprints to be pairwise nonoverlapping. Rings may touch the output border because a center one cell from a border is lawful; clipped rings and overwrite-order interactions remain outside the generated domain.

**Rationale.** Canonical examples teach independent marker expansion, not collision resolution or clipping. The imported associated note `GNOTE-002336` identified this as a deliberate manifold boundary. This review found no evidence justifying a broader interaction rule.

**Rejected alternative.** Adding overlapping centers for “difficulty” would introduce color precedence semantics not fixed by the canonical pairs.

## D6 — Keep color relations as semantic evidence, not color meaning

**Decision.** Retain opaque ARC colors, including one repeated-color pair in the aligned/mixed profiles and distinct colors in the canonical-pair/quad profiles.

**Rationale.** The `unique_color_only` rival fits all canonical pairs because official markers have unique colors. Repeated-color lessons are necessary to establish that every marker location expands independently.

**Probe.** The final 2,400-lesson census gives every declared witness 400/400 support in each band/mode row and leaves zero named rivals alive.

## D7 — Add source-bound probes, not production-only assertions

Two reusable tools were added under the selected task workspace:

- `profile_override_probe.py`: compares semantic-profile retention under compatible exact controls and supports `--generator` for immutable-source A/B runs.
- `lesson_census.py`: evaluates all cyclic four-demo windows against the generator's own competitor/witness declarations.

They are intentionally outside production generation. This keeps training code small while giving future reviewers deterministic, hash-bound checks.

## D8 — Make canonical test lookup portable

**Decision.** The focused test locates `shared/data/canonical/puzzles.jsonl` by walking ancestors instead of assuming `parents[1]`.

**Rationale.** The task-test runner intentionally copies tests into two supported layouts. The prior hard-coded depth failed in the portable snapshot and obscured the intended regression failure.

**Rejected alternative.** Hard-code a second parent index. That would merely trade one layout assumption for another; a shared environment variable/helper is the better long-term fix (F2).
