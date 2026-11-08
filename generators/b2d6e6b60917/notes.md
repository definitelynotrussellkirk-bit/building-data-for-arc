# Working notes: b2d6e6b60917

## Review diagnosis

The imported v2.1.0 sampler generated a centered five-cell plus and interpreted
each single-cell marker as one stamp center. The selected authority instead:

1. chooses the largest 8-connected object as an arbitrary source template;
2. derives each smaller object's direction from its bounding-box center;
3. uses per-dimension stride `source bbox dimension + 1`;
4. repeats the full source shape for ray steps 1 through 9; and
5. paints only background cells in the marker color.

The old `self_check` rejected all four canonical inputs. It also required
marker colors to be distinct, although the canonical data reuses a marker
color, and its declared controls were largely decorative.

## Reviewed distribution

- Canvas: exactly 21×21, background 0.
- Source: monochrome, sparse, unique largest, 5..8 cells.
- Source bbox schedule: `canonical_3x3`, `wide_2x4`, `tall_4x2`.
- Markers: exactly 2 or 3, each a connected proper subset of the first translated
  source copy and each in a unique direction.
- Palette: four or five total colors, matching the canonical coarse profiles.
- Public exact axis: `n_markers` only; it is recovered from returned pixels.

Marker fragments are constructed by enumerating proper connected source subsets.
This is intentional: on cardinal rays, an arbitrary edge fragment can shift its
bbox center and make the Racket authority decode a diagonal direction. The
enumeration retains only fragments whose bbox-center decoder returns the intended
ray.

## Semantic contract

`rule_mirror` is an input-pure Python reconstruction checked against all four
canonical pairs and by the central Racket mirror-parity stage. Declared rivals
cover identity, one-step stamping, fixed stride 4, bbox filling, fragment-only
propagation, source-color propagation, cardinal-only propagation, and processing
only the first marker.

`fixed_stride_4` is the one declared canonical shortcut: all canonical sources
have 3×3 bboxes, so bbox-plus-one happens to equal four. Every three consecutive
scheduled examples include both non-3×3 profiles and therefore refute it.

The retained `workspace/lesson_probe.py` iterates the generator's actual
witnesses, competitors, shortcuts, and schedule. It reports its sampler and
limits; it is sampled evidence, not a universal induction claim.

## Known limits

The generator deliberately stays on the canonical 21×21 canvas and supports
only three reviewed source-bbox families. It does not claim that other canvas
sizes, denser source templates, one-marker scenes, overlapping rays, or more
than three markers are invalid in the abstract. Those cases remain outside the
reviewed training domain.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `e550260117ba72e516b0829b0de282e818984cf001fc7d1a26d9c77b9c1e248f`.

# Decisions for `b2d6e6b60917`

## D1 — Rebuild from canonical semantics instead of patching the plus sampler

**Input evidence.** The baseline generated an exact centered plus and one stamp
per singleton marker, while the authority uses the unique largest 8-connected
object as a template and repeatedly propagates it. All four canonical inputs
were rejected by the old structural assumptions.

**Decision.** Replace the sampler and validation wholesale rather than extending
the centered-plus representation.

**Rejected alternative.** Keep the old plus task and only pin the rule hash. That
would make the metadata cleaner while preserving mislabeled training examples.

**Failure mode / limit.** The new generator is a deliberate domain model, not a
universal parser for every grid on which the authority might happen to return a
value.

## D2 — Keep the canonical 21×21 canvas and coarse palette profiles

**Input evidence.** Every canonical pair is 21×21, with four or five total
colors. There was no source evidence that varying canvas size was part of the
concept.

**Decision.** Fix the canvas at 21×21 and schedule total palettes of four or five
colors. This makes every generated sample coarse-profile compatible and keeps
capacity reasoning stable while the semantic axes vary.

**Rejected alternative.** Continue the baseline's 17–23 size range. That added
surface diversity without canonical support and made the old plus placement,
not the intended ray rule, the dominant variation.

**Failure mode / limit.** The training domain does not teach size transfer to
other canvas dimensions.

## D3 — Use a deterministic three-profile source schedule

**Input evidence.** Every canonical source bbox is 3×3, so the intended
bbox-plus-one stride happens to be 4 in both dimensions. An executable
`fixed_stride_4` rival fits all four canonical pairs.

**Decision.** Cycle `canonical_3x3`, `wide_2x4`, and `tall_4x2` by sample index,
set `EXAMPLES_NEEDED=3`, and require every three consecutive examples to contain
all three. The non-3×3 profiles make one active stride differ from four.

**Rejected alternatives.** Pure random profile sampling could produce complete
lessons containing only 3×3 sources. Removing 3×3 entirely would refute the
shortcut but lose literal canonical anchors.

**Probe.** `workspace/lesson_probe.py` checks all cyclic schedule starts through
100 disjoint lessons per band and iterates live competitor declarations.

## D4 — Use small explicit sparse shape libraries

**Input evidence.** The rule depends on template geometry, bbox dimensions, and
recoverable marker fragments. Arbitrary random walks made it harder to guarantee
bounded size, sparsity, source uniqueness, and a usable fragment in every ray.

**Decision.** Use reviewed connected sparse libraries for 3×3, 2×4, and 4×2
bboxes, with 5–8 occupied cells and more than one shape per profile.

**Rejected alternative.** Generate arbitrary polyominoes and repeatedly reject.
That offered nominal shape breadth but weaker guarantees and less transparent
lesson scheduling.

**Failure mode / limit.** Morphological support is finite and should not be
mistaken for exhaustive template diversity.

## D5 — Construct marker fragments by inverse-validating the authority decoder

**Input evidence.** An arbitrary connected subset placed in a cardinal first
copy can have an off-center bbox. The authority compares the marker bbox center
to the source bbox center, so such a fragment can be decoded as diagonal even
when placed on a cardinal translation.

**Decision.** Enumerate connected proper source subsets and retain only those
whose translated bbox center decodes to the intended direction. Require each
marker to be smaller than the source, monochrome, in a unique direction, and to
leave visible cells for a farther copy.

**Rejected alternative.** Choose any source subset and trust the placement
direction. That was the implementation bug caught during the GREEN cycle.

**Failure mode / limit.** Marker morphology is constrained by decodability; this
is necessary to match the selected authority, not an independent aesthetic
choice.

## D6 — Expose only one exact public axis

**Input evidence.** The baseline advertised many axes that were decorative,
aliased, or inconsistent with validation.

**Decision.** Keep only `n_markers` with exact values 2 or 3, derive it from
returned pixels in `observe_overrides`, and reject unknown controls.

**Rejected alternative.** Preserve compatibility with old keys. Silent or
non-observable controls would keep the override contract misleading.

## D7 — Make semantic claims executable

**Decision.** Add an input-pure `rule_mirror`, `strict_canonical_like`, seven
semantic witnesses, eight competitors, explicit witness/rival mappings,
`CANONICAL_SHORTCUTS`, and `lesson_identifiable`.

**Rationale.** A feature being present is not enough; each named witness must
actually separate the authority from a plausible rival, and the complete demo
set must identify the query transformation.

**Rejected alternative.** Rely only on self-check and aggregate diversity.
Those can pass even when a shortcut solves every lesson.

## D8 — Synchronize selected authority text without rewriting history

**Input evidence.** The canonical `program_solution` and selected base-record
`target_code` differed textually; the archival `raw_code` was a second,
behaviorally valid implementation.

**Decision.** Copy the existing canonical program into selected `target_code`,
leave canonical `program_solution` unchanged, and preserve archival `raw_code`.
Authority sync now reports one exact selected group; execution parity confirms
both distinct implementations solve all four canonical pairs.

**Rejected alternative.** Delete or overwrite `raw_code`. That would erase useful
provenance without improving selected execution.

## D9 — Retain a source-bound long probe

**Decision.** Add `workspace/lesson_probe.py`, importing the selected generator's
actual schedule, witnesses, rivals, shortcuts, and mirror. It reports the sampler,
domain limits, generator hash, unique inputs, disagreements, survivors, and
lesson failures.

**Rationale.** The central 12-lesson semantic check is a smoke test. The retained
100-lessons-per-band probe cheaply detects schedule regressions without copying
a rival-name list that can drift from source.

**Limit.** The probe is sampled evidence over the documented domain, not a proof
of universal induction.
## Current parametric proposal (review-077b48e1e9ac0062)

The canonical generator and selected authority were left unchanged. The new
task-local adapter proposes `template = full | fragment`. The default `full`
program is the selected canonical Racket source byte-for-byte. The alternate
keeps direction decoding, bbox-plus-one stride, marker color, clipping, and
occupied-cell preservation fixed, but propagates only the marker's recovered
source fragment instead of the complete template.

Inputs are generated independently of the private setting. Every supported
2–6-demo prefix leaves one finite survivor, and four distinct queries are
sampled independently; the fourth is a constructed 30×30, three-ray stress
case. Protected replay covered 18 jobs over both settings, seeds 0/17/91, and
demo counts 2/3/6. It verified 138 pair labels through 204 Racket evaluations,
including public/private projection checks. The portable changed-scope snapshot
passed 29 tests.

This evidence is source-bound and reviewer-reported, not owner qualification,
acceptance, production promotion, or training admission. The next useful action
is owner qualification of the finite family; broader competitors such as bbox
fill remain covered by the existing canonical-generator evidence rather than by
this two-setting proposal.
