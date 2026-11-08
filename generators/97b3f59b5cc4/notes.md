# Review 2026-10-25 — native connectivity family

Added a task-local native parametric family without changing production `generator.py` or the selected canonical authority. The exact default is `connectivity=four`; the alternate `connectivity=eight` changes only same-color component segmentation. Each generated scene contains a frame component and a same-color interior block joined only diagonally, plus a second repeated color with opposite border fates. This forces the two-step rule: (A) derive the component partition and border-contact flags, then (B) paint complete border-contact components.

The adapter supports 2–6 demonstrations and 1–4 private queries with stable count prefixes and matched inputs across settings. The four-query profile is 11×13, 17×19, 24×27 and 30×30; the largest scene has substantial foreground rather than padding. A finite demonstration-only audit covers the declared alternate plus global-border-color, edge-only, identity and erase-all shortcuts.

Evidence: 39/39 task-local tests pass; native qualification covered both settings at seeds 0 and 17 with 32 protected-Racket evaluations; the source-bound `wrong_intermediate` witness was constructed and replayed through protected Racket. The witness shows that an incorrect four-neighbor partition changes which diagonal interior cells inherit frame contact. This is bounded reviewer evidence only: owner acceptance and training admission remain pending.

# Working notes: 97b3f59b5cc4

## Intended rule

Treat each nonzero, same-color **4-connected component** independently. Keep the
entire component unchanged when any cell touches the outer frame; erase the
entire component when it is wholly interior. Grid dimensions and surviving
colors/coordinates are preserved. The selected canonical authority is pinned by
`RULE_HASH = e3401b50999e`; no Racket change was needed in this review.

## Review 2026-10-23 — conflict reconciliation against current source

The two retained audit returns were compared with generator version 3.0.0 at
SHA-256 `57900b879408118f4f95513cc2defc9a65b43e043725b12d618732417c5870ca`.
Both useful changes are already present: the public control surface is limited to
four exact axes with retired controls rejected, and ordinary lessons contain
repeated-color components with opposite border fates. Reapplying either historical
patch would regress or duplicate the current design, so production `generator.py`
and the canonical Racket authority remain unchanged.

`workspace/reconcile_prior_returns.py` now emits a source-bound manifest and
reports `conflict_detected` rather than reconciliation when any source binding or
semantic check fails. The retained manifest records 3 canonical pairs, 16,384
exact-axis cases, 480 ordinary samples, 400 contiguous three-example windows,
two rejected retired controls, and exact replay of the retained discriminator,
all without failures. A tampered counterexample hash is covered by a red/green
regression test; an existing-output probe confirms the CLI refuses to overwrite
evidence. Sixteen focused tests pass.

Representative selected-Racket execution covers the retained repeated-color
witness, lower and upper exact boundaries, and a fresh ordinary lesson. All four
outputs match `rule_mirror`; the executed rule hash is `e3401b50999e`. This is a
finite regression check, not new training approval or a proof against unenumerated
programs. The next useful action is to run this verifier whenever either prior
return is reconsidered or the current generator hash changes.

## Review 2026-10-11 — current design

The selected 2.1.0 generator was replaced by version 3.0.0 after the following
baseline problems were reproduced:

- `self_check` demanded at least two interior objects and therefore rejected all
  three canonical pairs, each of which has two border components and one interior
  component.
- Ten advertised axes included dead or silently ignored controls. Exact overrides
  could be accepted without changing the sampled grid.
- Ordinary draws assigned a distinct color to every component. This made the
  simpler rule “keep every cell whose color appears on the border” fit the
  generated lessons, even though the authority acts on connected components.
- The generator did not pin the selected rule hash and exposed no executable
  lesson-level semantic rivals/witnesses.

The current sampler uses a four-slot deterministic profile schedule. The first
three slots cover the canonical `5x7`, `6x7`, and `6x8` size profiles; the fourth
adds a larger `7x9` profile. Slots 1 and 3 deliberately place the same color on
one border component and one disconnected interior component. Consequently every
contiguous three-example window contains a direct counterexample to the global-
color shortcut. The first ordinary border component extends into the interior,
so an “edge cells only” rule is also refuted.

Ordinary scenes use bounded candidate enumeration/backtracking over transformed
small shapes. Exact overrides use a separate deterministic singleton placement
path, avoiding combinatorial search while realizing every joint boundary case.
The only public exact axes are now `grid_h` (5..12), `grid_w` (7..14),
`n_border` (1..4), and `n_interior` (1..4). Unknown keys, booleans, floats,
numeric strings, invalid seeds, and invalid sample indices fail loudly. Degenerate
textures remain private mutation fixtures and cannot be combined with ordinary
exact controls.

`self_check` accepts the canonical task domain and requires at least one component
of each fate for ordinary lessons. `strict_canonical_like`, `observe_overrides`,
`rule_mirror`, five semantic rivals, and four executable witnesses provide the
battery contract. The retained counterexample
`counterexamples/shared-color-opposite-fates.json` is an ordinary generated
sample (`seed=0`, `sample_index=1`, `difficulty=easy`) whose selected Racket output
erases the interior color-8 component while preserving the disconnected border
color-8 component.

## Evidence and limits

- Focused task and workspace-tool tests: 13/13 pass, including all canonical pairs, exact Cartesian
  boundary cases, strict scalar types, bounded override placement, cyclic
  three-profile teaching windows, and the retained counterexample.
- Final source-bound battery: 12/12 stages green for generator SHA-256
  `57900b879408118f4f95513cc2defc9a65b43e043725b12d618732417c5870ca` and
  authority-set SHA-256
  `a73e77188b182d289578afd462011b4721b6e4ed5a21469a1b3af9dd427c486d`.
- Lesson census: 300 production lessons (100 per band), 1,200 rotated queries,
  1,179 unique inputs, zero declared-rival ambiguity, zero scoring errors.
- `workspace/receipt_manifest.py` verifies source-bound stage receipts, logs, markers,
  and subjects for interrupted reviews; it deliberately does not synthesize an official
  battery verdict.

These checks establish support against the declared finite rival set, not unique
identifiability against every possible program. Components are intentionally
8-neighborhood separated so same-color diagonal contact cannot blur the 4-connected
object boundary. Difficulty bands vary random morphology and palette but share the
same four semantic schedule slots; the task does not require a separate harder
rule by band.

## Prior-return leads used

- `review-abe8247bc7f3032c:v0001`: canonical-validator mismatch and need for a
  repeated-color discriminator.
- `review-30f42b66093700f5:v0001`: ignored exact controls and the global-color
  shortcut. This was the primary implementation lead.

The retained claims were treated as hypotheses and remeasured against the pinned
selected baseline before repair.
## Current reviewer considerations

Source SHA-256: `57900b879408118f4f95513cc2defc9a65b43e043725b12d618732417c5870ca`.

# Decisions for 97b3f59b5cc4

## D1 — Keep the selected authority unchanged

**Decision.** Preserve the canonical Racket rule and pin the generator to `RULE_HASH = e3401b50999e`.

**Rationale.** The canonical examples and selected execution consistently implement a component-local rule: keep an entire nonzero same-color 4-connected component when any cell touches the outer frame; erase it otherwise. The defects were in generation, validation, controls, and teaching—not the authority.

**Probe.** The final battery's rule-smoke, Racket lint, and authority-sync stages pass; the retained same-color counterexample also matches the selected Racket output.

**Rejected alternative.** Editing an archival bank copy merely to eliminate textual divergence would add unrelated authority churn. The battery reports selected synchronization and execution parity, so this review leaves the archive alone.

## D2 — Replace the 2.1.0 rejection sampler rather than patching its symptoms

**Prior choice.** The baseline sampled objects with a broad control surface and then rejected scenes through `self_check`.

**New choice.** Version 3.0.0 constructs valid scenes directly using bounded transformed-shape placement for ordinary samples and deterministic singleton placement for exact overrides.

**Reason.** The old path simultaneously rejected canonical pairs, made termination/control realization difficult to reason about, and hid dead controls. A constructive split gives ordinary morphological variety while making exact-axis requests total and auditable.

**Failure mode considered.** A single general backtracking engine for every 12×14 / 4+4 boundary combination could become needlessly expensive. The deterministic exact path avoids that search without weakening the ordinary distribution.

## D3 — Narrow the public exact contract to four truthful axes

**Decision.** Advertise only `grid_h`, `grid_w`, `n_border`, and `n_interior`, with explicit integer ranges. Treat seed and sample index as strict non-boolean integers, reject numeric strings/floats, and reject unknown override keys.

**Rationale.** A small exact surface is more valuable than ten nominal knobs whose effects cannot be observed. The final override gate exercises the Cartesian boundaries and reports no ignored-control categories.

**Rejected alternative.** Keeping compatibility aliases for the dead axes would preserve silent behavior and encourage downstream callers to depend on fiction. This is a generator authoring contract, so loud rejection is preferable.

## D4 — Teach object identity with repeated colors

**Decision.** Use a stable four-profile cycle. Profiles 1 and 3 place the same color on a frame-connected component and on a disconnected interior component; every contiguous three-example teaching window includes one such discriminator.

**Rationale.** Distinct colors accidentally make component membership equivalent to global color membership. The repeated-color witness forces the learner to segment 4-connected components and apply the frame predicate to each component separately.

**Additional discriminator.** The first border component extends inward, so “keep only cells physically on the edge” cannot fit the lesson.

**Rejected alternative.** Randomly hoping for repeated colors is not a teaching guarantee. Deterministic profile placement keeps the witness present while randomizing shape transforms, locations, and palettes within each profile.

## D5 — Separate canonical coverage from exact-override coverage

**Decision.** The ordinary schedule deliberately visits canonical-like 5×7, 6×7, and 6×8 profiles plus 7×9. The exact path realizes the entire declared grid/count range independently.

**Rationale.** Canonical envelope coverage and control completeness are different goals. Conflating them either makes normal training samples unnaturally uniform or makes exact boundary requests unreliable.

**Probe.** `strict_canonical_like` and profile-floor evidence establish ordinary linkage; the override stage establishes exact realization.

## D6 — Add executable rivals and retain a concrete authority-labelled witness

**Decision.** Declare identity, erase-all, top-border-only, edge-cells-only, and keep-border-colors-globally rivals, plus executable witnesses. Retain `counterexamples/shared-color-opposite-fates.json` and test it against the selected Racket authority.

**Rationale.** Correct labels do not make a lesson teachable. Named rivals turn likely shortcuts into regression contracts, while a frozen Racket-labelled counterexample prevents the most important baseline defect from returning.

**Limit.** This is finite mutation testing, not a proof against every possible program. The two adversarial audits demonstrate why a broader shared mutation gate would still help.

## D7 — Treat three demonstrations followed by one query as the production policy, but test rotations

**Decision.** Export ordered three-demo lessons and run a larger required-rotation census as a stress test.

**Rationale.** Production ordering is part of the generator's teaching design, while query rotations reveal whether a profile is only useful in one position. The final census materialized 300 ordered lessons and 1,200 rotations with no declared-rival ambiguity.

**Limit.** Passing rotations against declared rivals does not establish universal query-position invariance or unique identification.

## D8 — Build a receipt verifier, but never let it manufacture a battery verdict

**Decision.** Add `workspace/receipt_manifest.py` for future agents. It requires every expected stage receipt, successful exit, matching subject marker, present log, and hash-bound files. It emits a manifest only.

**Rationale.** The aggregate controller was twice interrupted after completed child stages. A compact receipt inventory makes reconciliation mistakes visible and preserves evidence across short command windows.

**Boundary.** The tool intentionally does not claim `all_green`; only the packet's official battery `--resume`/`--status` logic may produce that verdict. Tests cover complete and mismatched manifests.

## D9 — Preserve failed and interrupted evidence

**Decision.** Keep the baseline failures, red regression receipts, and interrupted aggregate attempts rather than replacing them with a clean narrative.

**Rationale.** They establish that tests failed for the intended reasons before the repair and explain why the final aggregate was reconciled from source-bound stage receipts. The final report distinguishes measured failures, interruptions, and successful reruns.
