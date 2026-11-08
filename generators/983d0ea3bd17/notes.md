# Working notes: 983d0ea3bd17

## 2026-09-29 first review

- Kept the canonical Racket authority unchanged and pinned `RULE_HASH = "fd605125c9f8"`.
- Replaced the former nominal eight-axis schema with four generated, observed, and override-tested axes.
- Expanded source count from `1..2` to the canonical `2..3`; all four canonical inputs now pass both validators.
- Anchored ordinary draws to canonical dimensions while preserving bounded size exploration.
- Added a first blocker profile to refute the public-fitting “paint through obstacles” shortcut.
- Added rule parity, strict-canonical, override-observer, semantic-rival, lesson, mutation, and regression-test hooks.

## 2026-09-29 adversarial second review

The first repair passed the generic battery but a deeper rival search found two unmodeled shortcuts:

1. **Stop only at color 8.** This rule fit all four canonical pairs and all `1,800/1,800` sampled first-round draws because every generated blocker was color `8`.
2. **Deduplicate aligned sources.** A greedy solver that retained only the first source from each used row/column fit all canonical pairs and survived some three-demo windows, then changed aligned-source queries.

The repair now uses one color-`8` blocker plus a second blocker drawn from `{1,3,4,5,6,9}`. Both blockers are independently observable. The same probe also contains an edge source and an aligned source pair, so it refutes color-specific stopping, non-red emitters, edge omission, and axis deduplication in one controlled scene.

The default schedule is now `canonical_pair → two_color_blocker_probe → canonical_triple`. Both anchors are scattered canonical-like scenes; the probe alternates between two and three sources by cycle. The six-slot source-count sequence is `2,2,3,2,3,3`.

`workspace/deep_audit.py` was added for future reviews. It verifies declared canonical shortcuts against all canonical pairs, scans sliding three-demo windows for surviving competitors, checks every probe’s two-color/independent-observability contract, and emits replayable JSON.

Fresh second-round evidence:

- focused tests: `26 passed`;
- task-local deep audit: `216/216` windows, 12 competitors, zero survivors; `216/216` blocker probes clean;
- semantic gate: strict support `325/600`, canonical acceptance `4/4`, witnesses `10/10`, rival claims `10/10`, lessons `12/12`;
- Racket smoke: `120/120` mirror parity, zero crashes, 104 distinct outputs;
- full battery: all 12 stages green;
- exact two-color witness: Racket equals the mirror and refutes all four declared canonical shortcuts.

Remaining nonblocking limitation: the canonical Racket source still has style-only `style-not-eq` and `style-eq-zero` notices. Execution parity and authority synchronization are clean, so it remains unchanged.
## Current reviewer considerations

Source SHA-256: `46118d5bc35659688a189e90a8e481adb11404d932d3fa0d45401641857746f1`.

# Design decisions — 983d0ea3bd17

## Decision standard

Each decision below is tied to canonical evidence, the selected Racket authority, or a measured shortcut. Unknown original rationale is not reconstructed as fact.

## Current design choices

| Choice | Evidence / alternatives | Selected design | Failure modes and limits |
|---|---|---|---|
| Rule authority | The existing Racket program already emits four cardinal rays and stops at every nonzero cell. Rewriting it would invalidate a synchronized authority merely to remove two style notices. | Keep the authority unchanged; pin `RULE_HASH = fd605125c9f8`; maintain a Python mirror and broad parity tests. | Two style-only notices remain. Any future authority edit must re-establish canonical, generated-input, and synchronization evidence. |
| Semantic colors | Canonical fixes source `2` and output `7`; palette variation would create a different task. | Keep red `2` as the only emitter and orange `7` as the ray color. | Does not teach color-role abstraction, intentionally. |
| Source count | Original `1..2` rejected two canonical triples. Allowing singleton scenes weakens evidence that every source emits. | Lawful/default range is exactly `2..3`. Six scheduled samples use counts `2,2,3,2,3,3`. | Raw Racket would accept one source, but singleton inputs are absent from canonical and excluded from this curriculum. |
| Dimensions | Original `4..6 × 6..8` missed canonical sizes; exact-only shapes risk a size lookup shortcut. | Mostly use canonical shapes `(7,8),(8,9),(6,10),(9,9)`, with bounded `6..10 × 8..12` difficulty-aware exploration. | Exact profile support is deliberately not 100%; measured second-round support is `35/60`. |
| Public-like anchors | First round rotated edge/aligned ordinary scenes through schedule slots. That let an aligned-source shortcut survive windows before an aligned query. | Both non-probe slots are scattered, distinct-row/distinct-column, canonical-like anchors: two sources then three sources. | Edge/alignment behavior is concentrated in the probe and explicit overrides rather than every ordinary window. |
| Blocker count | One blocker refuted full pass-through but did not test generalization over obstacle identity. | A probe has exactly two blockers, each on a separate source-ray lane. | Two blockers add more structure than public inputs; this is deliberate semantic instrumentation. |
| Blocker colors | A fixed color `8` let “stop only at 8” match all `1,800/1,800` sampled first-round draws. Alternatives were random single color, all colors as explicit axis, or a fixed+variable pair. | Use one anchor `8` and one distinct secondary color from `{1,3,4,5,6,9}`. Keep color internal rather than exposing another override axis. | A learner could still memorize the finite lawful set, though every nonzero ARC color except `2` and `7` can appear across draws. |
| Independent blocker observability | Two blockers are useless if one is masked by another source or already-painted path. | Each blocker owns a lane with a zero before and beyond it; making only that blocker transparent must change the output. `self_check` enforces this per blocker. | This is stricter than raw rule lawfulness, but it is necessary for a teaching probe. |
| Aligned sources | Canonical sources occupy distinct rows/columns. A deduplication rival survived `360/2,160` first-round lesson windows. | Every blocker probe includes at least one aligned source pair, and `dedupe_shared_axis` must disagree on the probe. | Aligned sources introduce source-to-source occlusion, but the separate blocker lanes preserve a clean witness. |
| Edge source | Canonical contains an edge source, but some generated windows did not. | Every blocker probe includes an edge source; an `interior_sources_only` rival and witness make this executable. | Edge support is guaranteed in probes, not in every canonical anchor. |
| Red-only emitters | With blockers introduced, “all nonzero cells emit” becomes a plausible extension. | Blocker placement guarantees that emitting from either blocker creates extra cells. `all_nonzero_cells_emit` is a canonical shortcut and lesson competitor. | The rival is one plausible emitter mistake, not every possible color-role error. |
| Blocker preservation | The selected rule copies the input before painting, so obstacles remain their original colors. | Declare `erase_blockers` and `recolor_blockers_orange` rivals and a blocker-preservation witness. | Preservation is shown only in blocker slots because ordinary inputs have no obstacles. |
| Teaching schedule | Pure random sampling cannot promise semantic coverage in a finite lesson. First-round rotation also leaked aligned-source shortcuts. | Deterministic period three: `canonical_pair → two_color_blocker_probe → canonical_triple`. Every sliding three-example window has all profiles. | The schedule is predictable by index, but the rule evidence—not profile identity—determines the answer. Layout, size, orientation, secondary color, and optional third source still vary. |
| Difficulty | Rule complexity does not change with size. | Difficulty controls bounded morphology only; all bands retain canonical anchors and blocker probes. | Difficulty is not a semantic hierarchy. |
| Override schema | Original nominal axes were dead; unknown keys were silently accepted. | Expose only `grid_h`, `grid_w`, `seed_count`, and `scene_kind`; verify each requested value with `observe_overrides`; reject unknown keys. | No compatibility alias for old fake texture/palette axes. Explicit failure is preferred to silent non-operation. |
| Scene-kind overrides | Default lessons need a strict curriculum, but reviewers still need direct construction coverage. | Support `scattered`, `edge_anchored`, `row_aligned`, `col_aligned`, and `blocked` as explicit scene values. | Ordinary aligned/edge overrides are lawful but not strict-canonical. |
| General validator | Equating raw Racket lawfulness with useful teaching would admit invisible obstacles and weak probes. | `self_check` validates dimensions, ARC colors, 2–3 sources, zero or exactly two valid blockers, distinct blocker colors, anchor `8`, edge/aligned source structure, independent observability, and four shortcut disagreements. | This intentionally defines a stronger generator grammar than the bare Racket function domain. |
| Strict canonical predicate | Semantic probes should not be mislabeled canonical. | `strict_canonical_like` additionally requires a canonical shape, no blockers, and distinct source rows/columns. It accepts all `4/4` canonical inputs. | Strict support is `325/600`, not the whole curriculum. |
| Canonical shortcut set | First round declared only full pass-through, missing color-specific stopping and aligned-source deduplication. | Declare four public-fitting rules: pass-through, stop only at color 8, every nonzero emits, and dedupe shared axes. | This set is evidence-driven but not logically complete. Future rivals belong in the task-local audit. |
| Broader lesson rivals | Common partial rules can fit subsets even if they do not fit all public pairs. | Score 12 rules: the four shortcuts plus horizontal-only, vertical-only, first-source-only, first-two-sources-only, interior-only, source recoloring, blocker erasure, and blocker recoloring. | Named competitors are a maintained threat model, not a proof of unique program induction over all computable rules. |
| Lesson identifiability | A query-only check can hide a competitor that fits all examples and happens to agree on one query. | The deep audit requires zero surviving competitors across every demo window; `lesson_identifiable` also rejects any survivor that changes the next query. | Generic gate semantics still distinguish query-equivalent survivors, so the stronger zero-survivor condition is enforced by task tests/tooling. |
| Mutation fixtures | First round fixtures modeled “too many blockers,” but the lawful grammar now requires exactly two of distinct colors. | Include one-blocker and same-color-blocker fixtures, plus missing/excess sources, input color `7`, invisible blockers, and a no-edge probe. | Fixtures cover independent validator branches, not every malformed grid. |
| Future-agent tooling | Generic gates passed version `3.0.0` because the missing rivals were undeclared. | Add `workspace/deep_audit.py` to verify canonical shortcut fit, sliding-window survivor counts, blocker structure, and hook agreement with replay tuples. | It only audits declared rivals; reviewers must still invent new hypotheses. |
| Testing strategy | Battery-only evidence did not expose the two second-round holes. | Use TDD for the repair, 26 focused tests, the task-local deep audit, an exact canonical-Racket witness, and the full battery. | Unit tests use the mirror; Racket-backed evidence remains necessary and is supplied separately. |

## Rejected approaches

### Keep one color-8 blocker

Rejected after direct measurement: `stop_only_color8` fit every canonical pair, every sampled first-round draw in all three bands, and every tested three-demo window. More seeds cannot repair a grammar that never varies obstacle identity.

### Choose one random blocker color per scene

Rejected because a lesson-local learner could still infer “stop only at the demonstrated obstacle color.” Two distinct colors in the same probe establish within-example evidence for color-independent nonzero stopping.

### Use two blockers without independent lanes

Rejected because one blocker can be semantically redundant if another source already paints the would-be witness cell or if the first obstacle masks the second. Independent transparency tests are enforced instead of assumed from appearance.

### Rely on later row/column-aligned queries

Rejected because demonstrations must identify the query rule before the query is seen. The first schedule let `dedupe_shared_axis` fit the demos and fail only on the query in 360 measured windows. Alignment now appears in every probe demonstration.

### Add blocker color as a public override axis

Rejected. It would enlarge the external contract without helping the default curriculum. Secondary color variation is deterministic from the layout RNG, while all declared axes remain directly observable and causally tested.

### Rewrite the Racket authority

Rejected. The authority is correct, synchronized, and matches the Python mirror on `120/120` fresh generated inputs. The remaining findings are style-only.
