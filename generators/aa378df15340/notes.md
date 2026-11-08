# Current notes: aa378df15340

## Intended rule and authority

The selected authority is unchanged (`RULE_HASH = ba8b31fe9030`). For every
nonzero input cell at `(row, col)`, preserve the source and copy the same color
to `(col, row)`. The generator owns the collision-free part of that task domain:
square 5–12 grids, 3–9 off-diagonal sources, 1–4 nonzero colors, and at most one
occupied member of each unordered transpose orbit.

## Repair made in review-8df2423d06ca931e

The prior generator sampled oriented coordinates independently. The retained
audit from `review-ff4974d5d3ec96f1:v0001` identified seed 0 / sample 2 with
both `(3,5)=7` and `(5,3)=1`, even though no canonical example establishes what
an already occupied transpose destination means. That baseline source was
`f3e1afa7ebd2320fe2efc03286631fb3c46a763f22ecc84bc6629f85ac36da99`.

Version 2.0.0 now samples unordered transpose orbits and chooses one orientation
from each orbit. Every ordinary draw includes at least one upper-triangle and
one lower-triangle source, spans multiple rows and columns, and leaves all
transpose destinations empty. This both removes unsupported overwrite semantics
and makes the canonical-fitting “copy upper-triangle sources only” shortcut
answer-changing in every generated pair.

## Validation and controls

`strict_canonical_like` and `self_check` reject malformed shapes, booleans and
non-ARC colors, diagonal sources, occupied transpose targets, insufficient
source count/span, and unsupported palette sizes. `grid_n`, `n_seeds`, and
`n_colors` are exact observable controls in every difficulty band. The only
structured incompatibility is `n_colors > n_seeds`.

The first repaired battery exposed one omitted support point: four nonzero
colors occur canonically but the initial repaired default sampler reached only
1–3. The final sampler and exact axis therefore cover 1–4 colors. The failed
intermediate evidence is retained under `checks/after/`.

## Teaching contract

Three demonstrations are requested. The declared rival is
`upper_triangle_only`; each ordinary pair independently refutes it because every
input has a lower-triangle source. A 300-lesson census materialized 1,200 unique
pairs and checked 1,200 query rotations with zero declared-rival ambiguities.
This is finite evidence against the declared rival, not a proof against all
possible hypotheses.

## Known limits and open findings

- Occupied transpose-pair overwrite semantics are deliberately outside generated
  support; the Racket authority was not changed to teach them.
- Diagonal sources are excluded because copying them is a semantic no-op.
- The finite rival contract covers the strongest canonical-fitting directional
  shortcut identified here, not every conceivable program.
- No repair blocker remains. Final generator SHA-256:
  `bdedc4f48802f30a376134b9b8777c328023e5e2878262103396f45b98d096b7`.
## Current reviewer considerations

Source SHA-256: `bdedc4f48802f30a376134b9b8777c328023e5e2878262103396f45b98d096b7`.

# Decisions for aa378df15340

## D1 — Treat the prior occupied-pair finding as a domain defect

**Prior choice:** independently sample off-diagonal coordinates, which could
select both members of a transpose pair. **New choice:** generated inputs contain
at most one member of each unordered transpose orbit. The canonical pairs never
exercise occupied targets, so preserving such inputs would silently teach an
unsupported overwrite convention. Alternative rejected: add collision examples
and keep replacement semantics; that would require authority/canonical evidence
rather than a generator-only repair. Reproducer:
`repo/generators/aa378df15340/counterexamples/occupied_transpose_pair.json`.

## D2 — Construct lawful placements rather than filter after generation

The sampler selects distinct unordered orbits, assigns orientations, and retries
only for two-dimensional row/column span. This makes collision freedom true by
construction and prevents order-dependent overwrites. Post-hoc deletion or
collision rejection was rejected because it would distort requested source and
palette counts.

## D3 — Put both directional orientations in every ordinary pair

All canonical sources are above the main diagonal, so “copy only upper sources”
fits every canonical pair. Every generated input now contains at least one source
above and below the diagonal. This is stronger than relying on aggregate lesson
coverage: one correctly labelled generated pair already refutes the rival.
Evidence: `checks/question-shortcut/` and `checks/lesson-census-final.json`.

## D4 — Advertise only exact, observable axes

The retained axes are `grid_n=5..12`, `n_seeds=3..9`, and `n_colors=1..4`.
Textures and aliases from the baseline were removed because they were not real
controls. `n_colors > n_seeds` is declared and rejected as a structured
incompatibility. The first repaired distribution used only 1–3 colors; the
`dist_gate` correctly rejected that because a canonical input has four nonzero
colors. Four-color support was added before final verification.

## D5 — Use a strict task-domain validator

The baseline validator accepted essentially any rectangular grid and rejected
0/58 destructive mutations in the before self-check. The new validator checks
shape, ARC cell types, supported dimensions/counts, diagonal sources, occupied
transpose targets, spatial span, palette count, and background presence.
Malformed inputs return diagnostics rather than raising; generation requests
reject unknown and ill-typed overrides loudly.

## D6 — Pin and preserve the selected Racket authority

`RULE_HASH = ba8b31fe9030` was added. The Racket program and canonical row were
left unchanged because canonical parity and authority sync pass, and the defect
was unsupported input support rather than an incorrect oracle.

## D7 — Make the semantic contract executable

The generator declares the lower-triangle witness and the
`upper_triangle_only` rival through `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`,
`CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`. `lesson_identifiable` verifies
labelled demonstrations against the mirror rule and rejects surviving declared
competitors. Three demos remain sufficient because each ordinary demo contains
the witness.

## D8 — Retain failure evidence and reusable probes

Test-first evidence records 29 failures / 13 passes before the repair, then
42/42, and finally 48/48 after palette and counterexample coverage. The reusable
`workspace/reference_probe.py` supplies an independent coordinate oracle;
`workspace/stress_probe.py` exercises determinism, domain constraints, shortcut
refutation, and the complete legal override matrix. Final stress result:
4,000/4,000 ordinary draws and 864/864 exact override cases passed.

## Limitations

The finite tests and census do not prove universal induction. Generated support
intentionally excludes diagonal no-ops and occupied transpose pairs. Training
promotion remains a maintainer decision even though this review has no remaining
repair failure.

## 2026-10-25 native parametric family review

- Kept the canonical additive-transpose program and base generator unchanged.
- Added `workspace/parametric/` with exact `copy_only` default and sequential `copy_then_bridge` setting.
- Fixed the observed seed-228 midpoint-only teaching hole by forcing a bridge span of at least four in every scene.
- Final evidence: 74 task tests; 256-seed/5,120-pair audit with no declared rival survivor; protected authoring preflight; skip-A causal replay; 16 verified public views.
- Current status is reviewer `prototype / ready`. Owner source review, fresh qualification/acceptance, and training admission are still required.

