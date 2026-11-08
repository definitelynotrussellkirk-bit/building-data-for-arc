# Working notes: b8d6fabb411e

## Review review-b459c1d5bf86ccc3 — 2026-09-28

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`. Baseline 3.0.0 passed the entire 12-stage battery
and its seven retained tests before editing. Candidate 3.1.0 changes input
selection and validation, not canonical rules or approval receipts.

### Finding and repair

The inherited `interior_span_alignment` witness pooled axes. The first marker
was forced to an interior position, but default larger-square side lists always
started horizontally. A vertical-boundary-only rival therefore agreed with all
960 default review draws. Side-four offset 1 was also never represented.

Placement now forces an interior marker on each represented axis; the two-ray
profile supplies both in every four consecutive default indices. Interior
offsets are sampled uniformly among valid interior positions. Shuffling side
order decouples the two-and-two color pairing from fixed directions. Existing
layout/profile overrides, counts, palette roles and canonical anchors remain.
Horizontal/vertical interior witnesses and executable wrong rules are registered
in the semantic, lesson and canonical-shortcut interfaces.

The checker also rejects conflicting different-color half-rays, oversized grids,
and unobservable or contradictory requested overrides. It still accepts safe
same-color collinearity and valid rule inputs outside the generated profile
counts when no such profile was requested.

### Retained executable material

The mapped test file has 16 tests: the original seven plus nine regression cases.
Eight new cases failed against the baseline; the same-color acceptance control
already passed. `workspace/alignment_gate.py` uses independent wrong rules and
actual Racket output, supports frozen before/after execution trees, and exports
fully materialized review-only counterexamples. Its five tests are invoked
explicitly; new workspace files are not in the inherited runtime mapping.

The return packet contains the exact before/after checks, the baseline and final
960-draw gates, an override stress probe, full-repository test results and two
findings-only audits. Every reported draw count is a workload count, not a count
of independent samples. The 960-draw default sweep contains 640 distinct inputs
because canonical-size profiles are repeated across difficulty bands.

### Scope and limitations

There was no model training, benchmark-score experiment, reference-rule rewrite,
shared-tool change or training-admission upgrade. The geometric symmetries are
valid for this task, not a corpus-wide augmentation policy. Default lesson
coverage does not apply to arbitrary four-example subsets or forced 2×2 layouts.
Other untested shortcuts may remain; profile/count/size correlations were not
all removed. Full decisions and evidence are in the review return's
`DECISIONS.md`, `REVIEW.md`, `QUESTION_ANSWER.md` and `checks/`.
## Current reviewer considerations

Source SHA-256: `163223f3a00fcc859611b64df8b7d89c41cfa8dd29375b013db65e4b467e811d`.

# Decisions — review-c6237723b7a5b3a1

Task: `b8d6fabb411e`; original family: `training:d43fd935`.
Canonical rule pin: `e88f12aefcff`.

## D1. Keep the canonical transformation and valid distribution unchanged

The existing v3.1.0 generator already has strong canonical support and explicit
interior-span teaching witnesses. I did not change object roles, layouts,
profiles, palette, schedule, placement, rule text, or outputs for any lawful
call. The only production change is input validation at the public call
boundary. This is narrower than refreshing the distribution merely because a
new authoring assignment was issued.

Alternative: bump `VERSION` and resample all draws. Rejected because the repair
does not alter valid generation. Keeping `VERSION=3.1.0` preserves exact replay
for every previously lawful `(seed, sample_index, difficulty, overrides)` call.

## D2. Reject invalid scalar calls before hashing and scheduling

The before defect lint found 33 accepted invalid scalars across difficulty
bands: Boolean/float/string seeds, Boolean/float/string sample indices, and
negative sample indices. `gen_ctx` intentionally remains compatibility-oriented,
so this task now validates literal Python integers locally. `generate` and
`schedule_profile` share the validator; invalid difficulties are also rejected
consistently.

Alternatives: coerce values with `int(...)`, or change shared runtime behavior.
Rejected. Coercion aliases semantically different calls, and a shared tightening
could break unrelated legacy generators. New regressions are in
`tests/test_strict_call_contract.py`.

## D3. Use `alignment_scope` as the one small rule parameter

The proposed parameter is `alignment_scope ∈ {span, boundary}`. `span` is the
original/default and is byte-identical to the canonical Racket source.
`boundary` changes only whether alignment accepts the entire square span or
only its outer rows/columns. Both settings still require finding the same solid
color-3 square, classifying the same singleton markers and decoys, preserving
all objects, and drawing the same nearest-edge colored rays.

Alternatives considered: change marker color, ray direction, or square color.
Those are either cosmetic or disturb fixed semantic roles more than necessary.
The boundary rule is especially useful because it is a real canonical-fitting
shortcut already declared by the generator, not an arbitrary program mutation.

## D4. Make larger squares a declared dependent input constraint

Side-2 canonical examples cannot distinguish the settings. Prototype episodes
therefore use lawful side-4 generator draws with at least one interior-aligned
marker and at least one boundary-aligned firing marker. Both rules are
nontrivial, and they disagree on every retained pair. The input sampler is
independent of the hidden setting.

Alternative: accept ambiguous side-2 episodes or reveal the parameter in the
query. Rejected. The intended authoring problem is to infer one fixed episode
rule from demonstrations; ambiguity, not hidden semantics, is the failure mode.

## D5. Choose the hidden setting once per episode

`choose_parameters(seed)` deterministically selects one setting, used for all
three demonstrations and the query. The evidence contains one complete episode
for each setting. Every retained demonstration set refutes the other setting,
and every retained query also differs between settings.

Alternative: resample per pair. Rejected because it destroys a coherent task
rule and violates `PARAMETRIC-RULES.md`.

## D6. Keep canonical and proposed execution paths separate

The production generator and `RULE_HASH` remain fixed. Exact Racket variants,
private labels, public challenges, and reports live under
`workspace/parametric/` and `checks/parametric/`. Public JSON removes parameter
names/values, seed, source, hashes, rival metadata, and query outputs. The
prototype is labeled unapproved throughout.

Alternative: add a production parametric API or refresh approval hashes.
Rejected by the runtime boundary and because this finite review does not grant
variant approval or training admission.

## D7. Preserve the inherited test fixture; add separate portable tests

`tests/test_generator_b8d6fabb411e.py` is frozen by the packet. I restored its
exact baseline bytes after an initial portability experiment exposed its known
legacy import/fixed-root preflight defect. New strict-call and prototype tests
are separate files. The inherited stage blocker is reported honestly rather
than hidden by modifying the fixture.

## D8. Treat all evidence as finite

The Racket-backed bundle verifies both settings, all eight canonical labels,
Python parity, one complete episode per setting, and deterministic replay. It
does not prove universal identifiability, eliminate undeclared rivals, approve
the alternative, or establish model-performance gains. The second materialized
run matches the first semantic SHA-256, excluding output-path differences.
