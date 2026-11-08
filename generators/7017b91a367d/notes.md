# Working notes: 7017b91a367d

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `8f48fb04488be1f42a863fb60eb4587aaa433a5c4c560345cedd251ec3c700dc`.

# Decisions for `7017b91a367d`

## D1 — Keep the selected Racket authority unchanged

**Input choice.** Treat the canonical per-coordinate occupancy-count rule as authoritative:
for each local coordinate across three aligned 5×5 panels, map occupancy counts 0/1/2/3 to
0/2/4/8.

**Original rationale.** The packet's selected rule already matches all five canonical
pairs. The baseline defects were in sampling, validation, metadata, and teaching support,
not demonstrated rule execution.

**Alternatives considered.** Editing the Racket source; replacing it with a Python oracle;
using the archival bank copy as authority.

**Probe.** Rule smoke and authority synchronization in `checks/after-final/result.json`,
plus exact `arcpuzzles apply` in `checks/shortcut-witness/racket.json`.

**Decision.** No Racket change. Pin `RULE_HASH = "aa994ed25e88"` and retain the selected
catalog authority. The authority-sync report notes an archival textual divergence but
selected execution parity passes.

**Failure mode/limit.** This does not certify every possible 5×17 input as meaningful; the
generator still needs a declared lawful domain.

## D2 — Replace independent random cells with canonical-derived occupancy motifs

**Input choice.** Represent a local cell by a three-bit panel-occupancy mask. Start from five
3×3 abstract patterns whose count histograms occur in canonical examples, then apply all
legal dihedral transforms and panel permutations.

**Original rationale.** The old generator produced roughly 11 components against roughly
3 canonically and often omitted structures that create output color 8. The earlier random
cell approach also made connected-object validation impossible without frequent rejection.

**Alternatives considered.** Random walks in each panel; arbitrary independent Bernoulli
cells; literal replay of canonical inputs; unrestricted random mask matrices.

**Probe.** Import-time variant-collision assertion, 720 generated draws in
`test_generated_panels_are_three_connected_objects_and_teach_all_counts`, grammar and
diversity battery stages, and the 300-lesson census.

**Decision.** Use a small canonical-derived mask family. It creates connected objects,
retains meaningful geometric variety, and guarantees count levels 1, 2, and 3.

**Failure mode/limit.** Combined motifs always have a 3×3 bounding box. This is narrower
than the mathematical rule and may support undeclared morphology shortcuts; broadening it
requires new probes rather than arbitrary shape noise.

## D3 — Advertise only two exact, pixel-observable axes

**Input choice.** `profile` controls the exact count histogram; `palette_kind` controls one
of four exact panel-color tuples.

**Original rationale.** The baseline exposed variant, texture, density, position, palette
size, and distinct-color controls that were inert, singleton, unprobed, or silently ignored.
The original rationale for all of those axes is unknown; their metadata suggests an attempt
to describe diversity rather than controls the code actually honored.

**Alternatives considered.** Keep all old axes and implement each; mark them diagnostic;
remove all overrides; expose transform and placement as additional axes.

**Probe.** `observe_overrides()`, 80 exact combinations across four difficulty bands in
`checks/qualify-final.json`, the shared override gate, and invalid-value tests.

**Decision.** Remove unsupported controls. Keep exactly the two controls that can be
recovered unambiguously from returned pixels. Placement remains curriculum scheduling,
not an independently random user override.

**Failure mode/limit.** Difficulty changes sampling weights, not the legal support. There
is no promise that each band has a disjoint morphology family.

## D4 — Use four fixed distinct palettes, but make color non-semantic

**Input choice.** Render each panel in one distinct color from a named exact tuple:
`default`, `warm`, `cool`, or `varied`.

**Original rationale.** Canonical examples use distinct panel colors, while the authority
only checks nonzero occupancy. Fixed tuples make the override observable and avoid a
supposed palette name mapping to many unrecoverable random choices.

**Alternatives considered.** Fully random distinct colors; fixed canonical palette only;
color permutations tied to panel identity.

**Probe.** Exact override recovery, canonical support, panel-color distinctness tests, and
Racket rule smoke.

**Decision.** Use four exact tuples and permit panel permutations independently of color
semantics.

**Failure mode/limit.** The finite palette set does not exhaust all lawful color roles. It
is meant as controlled diversity, not proof of total color invariance.

## D5 — Schedule center and border placements deterministically

**Input choice.** Cycle `center`, `top_left`, `bottom_right` by `sample_index mod 3`.

**Original rationale.** All canonical occupied coordinates lie in the central 3×3. Thus a
wrong rule that ignores the 5×5 border fits every canonical pair. Purely random placement
could create lessons with no refuting demonstration.

**Alternatives considered.** Uniform random origin per pair; always use border; rejection
sampling at lesson assembly; make placement an exact override.

**Probe.** The exact witness in `checks/shortcut-witness/`, all 192 cyclic rotations in
`checks/qualify-final.json`, the required-rotation semantic gate, and the 1,200-rotation
lesson census.

**Decision.** Deterministic three-position curriculum. Three consecutive demonstrations
always contain center and both border branches, and any held-out pair from a four-pair
window leaves at least one border refutation among the demonstrations.

**Failure mode/limit.** The schedule is predictable. Predictability is accepted here because
its purpose is guaranteed teaching coverage, not cryptographic randomness.

## D6 — Make `self_check` describe the actual training domain

**Input choice.** Require a 5×17 rectangular integer grid, zero separators, three nonempty
monochrome 4-connected panels with distinct colors, and one recognized profile in one of
the three supported windows.

**Original rationale.** Baseline `self_check` rejected 0/60 destructive mutations and
accepted all-background/minimal impostors, so passing it conveyed no semantic evidence.

**Alternatives considered.** Validate dimensions only; accept any three nonempty panels;
recompute only that the Racket output is nonblank.

**Probe.** Malformed-grid and destructive-mutation tests; shared self-check and defect-lint
gates; canonical acceptance tests.

**Decision.** Validate the exact declared manifold and reject booleans as ARC colors.

**Failure mode/limit.** A strict validator can exclude lawful but unsupported rule inputs.
That is intentional: generation support and mathematical authority are distinct claims.

## D7 — Declare the strongest observed rival and lesson contract

**Input choice.** Declare `central_3x3_only` in `CANONICAL_SHORTCUTS`,
`SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`; declare border occupancy and all-count-level
witnesses; require three demonstrations.

**Original rationale.** The rival fits all 5 canonical pairs and is simpler than the full
5×5 rule given those examples. Raw pair correctness is insufficient when a generated
lesson leaves this rival query-equivalent on demonstrations but not the query.

**Alternatives considered.** No semantic contract; only assert all colors appear; add many
speculative rivals; increase demonstrations without controlling their content.

**Probe.** Canonical rival-fit check, Racket-backed border witness, exhaustive 12-start
rotation probe, required semantic gate, and larger production census.

**Decision.** Encode the concrete rival and make `lesson_identifiable()` reject a lesson
when it fits every demo but changes the query.

**Failure mode/limit.** The rival set is finite. Passing it does not prove universal ARC
identifiability; unknown rivals remain unknown.

## D8 — Add portable tests and reusable reviewer probes

**Input choice.** Add task-local pytest regressions plus `reference_probe.py` and
`qualify.py` under the task workspace.

**Original rationale.** The shared battery did not discover task tests automatically, and
future reviewers need a fast source-bound way to replay exact controls, canonical shortcut
fit, the concrete witness, and cyclic query rotations.

**Alternatives considered.** Put checks only in prose; import private runner functions;
make the Python mirror the authority.

**Probe.** Portable wrapper receipt `checks/task-tests-final/result.json`; direct repository
pytest; exact Racket application retained separately from the independent mirror.

**Decision.** Keep Python probes independent and explicitly subordinate to Racket-backed
checks. Use `reviewer_support.find_root()`/`canonical_pairs()` so tests survive portable
runtime layouts.

**Failure mode/limit.** The qualifier's mirror can detect internal inconsistencies but
cannot establish authority by itself; its report says so explicitly.

## D9 — Preserve failed/interrupted evidence without calling it a pass

The first aggregate baseline battery and one aggregate after run stopped after checkpointed
stages. I retained the baseline partial result and stage receipts, then used the documented
source-bound resume path to complete the final after battery. The final report distinguishes
stage-only checks, partial aggregates, and the completed 12-stage battery.

## D10 — Add a native count-map connectivity family

**Canonical default.** Preserve the exact selected occupancy-count Racket program byte-for-byte as `overlap_policy=count_map`.

**Alternate.** `overlap_policy=flood_from_triples` first produces the 0/2/4/8 count map, then floods from triple-overlap cells through four-neighbor double/triple connectivity and promotes reached doubles to 8. The sampler keeps all three panels connected and deliberately includes reachable doubles, unreachable doubles, singles, and triples in every scene.

**Causal check.** `flood-through-singles.rkt` corrupts the intermediate graph by allowing value-2 cells. Protected Racket replay changes the final output, demonstrating that the second stage consumes the count map rather than merely following it cosmetically.

**Teaching and limits.** Two demonstrations distinguish the two settings and four finite shortcuts on seeds 0, 17, and 97. The lawful grammar remains exactly three aligned 5×5 panels in a 5×17 input with a 5×5 output; no artificial 30×30 padding was introduced. The reusable `workspace/parametric/audit.py` retains the bounded self-review. Owner exact-source review and fresh native qualification/acceptance remain external.
