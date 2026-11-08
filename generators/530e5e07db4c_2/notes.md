# Working notes: 530e5e07db4c_2

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `0d5a119606da8985f536434281b75b67c69eff76f37f6ac105cadf0e1698f416`.

# Decisions for `530e5e07db4c_2`

## 1. Bind the generator to the selected authority

**Decision.** Pin `RULE_HASH = "646a78ec371e"` and replace the canonical row's `program_solution` with the selected base `target_code` exactly. The selected text adds two comments but does not change executable semantics.

**Evidence.** `checks/after/checks/530e5e07db4c_2_after_authority_sync.json` reports exact agreement between the active canonical program and selected `target_code`, and execution parity on all 3 train plus 1 held-out canonical pairs for both selected and archival texts.

**Alternative rejected.** Pinning the archival `raw_code` hash (`f97778fc4cf2`) would preserve the pre-review state but leave the two active authorities textually divergent. Rewriting the Racket algorithm was also rejected because no semantic defect was found.

**Limitation.** The archival raw source remains textually different. Its role is explicit and its comment-stripped semantics and execution are equivalent.

## 2. Replace fake controls with two exact axes

**Decision.** Declare only `grid_h` (`7..14`) and `grid_w` (`8..14`). Reject unknown keys and non-integer, Boolean, string, float, or out-of-range overrides before constructing `GenCtx`. Recover both controls directly from returned pixels with `observe_overrides`.

**Rationale.** The baseline advertised path orientation, seed positions, palette, isolated-stub count, corner anchoring, and negative textures that were ignored, clamped, or invalid. That made its API unfalsifiable and produced 17,119 findings in the baseline override audit.

**Alternative rejected.** Retaining orientation/profile as caller overrides would expose internal curriculum choices as promises and create many infeasible joint combinations. They remain deterministic keyed layout choices instead.

**Probe.** The final override report checks 6,480 draws and returns `PASS`; task tests exercise boundary dimensions in every band and reject unknown/invalid keys.

## 3. Use a four-profile deterministic lesson schedule

**Decision.** Cycle by `sample_index % 4` through:

1. `endpoint` — green at the endpoint of a canonical-scale branched component.
2. `green_interior` — green is the sole bridge to a large tail.
3. `branch` — a long spur is selected but lies off every single shortest route.
4. `cycle_tail` — two routes meet at green and a tail continues beyond it.

Set `EXAMPLES_NEEDED = 3`.

**Rationale.** Every consecutive three-profile window contains evidence against all four declared shortcuts. The schedule is transparent, reproducible, and compatible with the actual lesson materializer's consecutive sample indices.

**Alternative rejected.** Randomly choosing profiles would make some three-example windows ambiguous even if pooled coverage looked strong. A longer schedule was unnecessary: period four is sufficient to cover the required topology distinctions.

**Probe.** `tests/test_generator.py::test_every_three_demo_window_refutes_every_declared_competitor` checks all cyclic starts across three bands and three seeds. `workspace/curriculum_probe.py` retained 144 inspected windows with zero failures.

## 4. Always include a disconnected two-cell gray decoy

**Decision.** Constructively place one gray domino that is neither part of nor cardinally adjacent to the red component.

**Rationale.** A singleton decoy only refutes “recolor all gray”; a two-cell decoy also refutes the plausible rule “recolor every non-isolated gray cell.” Constructive placement prevents rejection-loop truncation and guarantees visibility.

**Alternative rejected.** Zero-to-four random isolated stubs were removed. They created identity/weak examples, did not reliably distinguish non-isolated-gray rules, and made exact control claims difficult to honor.

**Failure mode guarded.** `self_check` rejects missing decoys and singleton disconnected components. Targeted mutation tests retain both failures.

## 5. Match canonical object scale, not only semantics

**Decision.** Enlarge each profile so its largest connected gray object has 11–15 cells, near the canonical median of 12, while retaining the topology witness.

**Rationale.** The first semantic repair passed 53 focused tests but the generic defect linter correctly reported that canonical `max_obj` median 12 lay outside generated range `[3, 7]`. A new failing regression was added before enlarging the templates.

**Alternative rejected.** Suppressing the soft coverage warning would have left a real distribution mismatch: tiny toy graphs can teach the right rule but still underprepare a model for canonical-scale components.

**Evidence.** The retained RED run is `checks/tdd-scale-red/`; the fixed task suite is 54/54, `checks/scale-defect/` passes, and the final twelve-stage battery is all green. The workspace probe reports largest gray objects from 11 through 15.

## 6. Generate by D4-transformed templates plus constructive placement

**Decision.** Enumerate unique rotations/reflections of each colored topology, choose one with a keyed RNG, translate it into the requested canvas, and then choose a feasible decoy domino.

**Rationale.** This gives orientation/placement diversity without changing the semantic profile or adding brittle ad hoc path code. Feasibility is proven before drawing a placement, so requested dimensions are never silently changed.

**Alternative rejected.** A free random walk can self-touch, collapse profile distinctions, fail to reach green, or make post-hoc decoy placement impossible. Capped retries would bias the distribution and can return shortened examples.

**Probe.** Task tests require D4 equivariance of the validator and rule mirror and classify all scheduled profiles after generation.

## 7. Keep canonical dimensions dense but preserve the full domain in every band

**Decision.** Use weighted `draw_choice` lists that always contain every legal dimension. Height 7 and widths 8–10 are frequent enough for the pinned canonical-profile floor; larger dimensions remain common, with modest difficulty-dependent weighting.

**Rationale.** Exact overrides must remain legal in every band, while training still needs regular canonical-size support.

**Alternative rejected.** Band-specific hard bounds caused valid advertised overrides to fail. Always returning 7×8–10 would pass the floor but eliminate size generalization.

**Evidence.** The final profile floor records 15/20 exact hits for easy, 11/20 for medium, and 6/20 for hard, with zero crashes; the distribution test observes at least four shapes in 96 samples per band.

## 8. Declare executable rivals and witnesses

**Decision.** Implement and score four wrong rules:

- `recolor_all_gray`
- `recolor_nonisolated_gray`
- `shortest_path_only`
- `stop_at_green`

Map four named witnesses to these rivals and implement `lesson_identifiable` against the actual demonstrations and query.

**Rationale.** Structural feature presence alone does not prove that a lesson distinguishes a wrong rule. A witness is useful only when the named rival demonstrably disagrees with the selected answer on that grid.

**Canonical ambiguity.** `stop_at_green` matches all four canonical pairs, so it is declared in `CANONICAL_SHORTCUTS`; generated `beyond_green` examples are required to falsify it. The other three rivals are already refuted by canonical pairs but remain lesson competitors.

**Evidence.** The final semantic census has 600/600 hits for the disconnected-gray, connected-decoy, and off-shortest-path witnesses; `beyond_green` fires 278/600 across all bands. Every checked rival claim held. The larger census reports 300/300 identifiable production lessons and 1,200/1,200 unambiguous query rotations.

## 9. Exclude negative/no-op textures from ordinary training

**Decision.** Do not generate missing seeds, disconnected red/green, full-gray, or identity/no-op scenes in the ordinary domain.

**Rationale.** The selected curriculum's goal is to teach the positive connected-component transformation and disambiguate plausible positive shortcuts. The baseline negative texture controls returned malformed or semantically weak examples and were not honestly represented in `AXES`.

**Alternative considered.** A separately named hidden evaluation branch for disconnected red/green could test conditional behavior. It was not added to the three-example training schedule because it would consume teaching capacity and is not needed to distinguish the four measured rivals.

## 10. Validation scope and known limits

`self_check` validates palette, shape, seed uniqueness, red-to-green reachability, visible main gray mass, disconnected multi-cell decoys, and background. `strict_canonical_like` additionally requires canonical dimensions and exact palette.

The generator still uses a finite four-topology vocabulary and tests four declared rivals, not every possible hypothesis. The 300-lesson census and 1,200 rotations are finite evidence, not a proof of universal induction. The exported curriculum currently supports arbitrary query rotation within each four-pair lesson; a future exporter with a different assembly policy should rerun the source-bound census.
