# Working notes: 056999828b88

## 2026-10-02 review-a484b45ff0084d8c — second pass

### Rule retained

Find each same-color nonzero 4-connected object, crop it, sort crops by exact occupied-cell count ascending, top-align them, and concatenate them with one zero separator column. The Racket authority and canonical data were not edited; `RULE_HASH` remains `d2d58f482c81`.

### Why another pass was needed

Version 5 fixed a closed finite-template inventory but did not fully identify the measured quantity. `boundary_cells_order` counts only cells touching exterior background. It fits all five canonical pairs and survived 298/591 four-demo windows from the archived version-5 generator. Related canonical-fitting features included bbox semiperimeter, boundary perimeter, adjacency edges, and crop spans.

### Version 6 curriculum

- Ordinary draws retain exact canonical linked profiles and compact free-polyomino morphology through size six.
- Slot 3 uses connected objects of sizes 7, 8, and 9 (plus size 1 for four-object requests).
- The size-8 object has two interior cells, so its boundary-cell count is 6; the three shapes jointly invert the intended order under eight canonical-fitting shortcuts.
- Eleven executable rivals and matching witnesses are declared.
- Minimum-width D4 orientations and a packed-width constraint keep generalized outputs aligned with the canonical shrink distribution.
- Unknown overrides remain hard errors; `self_check` accepts only sizes 1..9 and still enforces distinct sizes/colors, separation, background majority, and legal output dimensions.

### Retained evidence

- `workspace/shape_support_after.json`: final 600-draw census, 49 D4 classes, zero generation/self-check failures, zero declared-rival survivors over 591 lessons.
- `workspace/shortcut_counterexample.json`: exact generated 7/8/9 input and all eight canonical-shortcut outputs.
- `workspace/candidate_rival_sweep.json`: 64 canonical-fitting feature/tie programs, zero survivors over 864 lessons.
- Packet `checks/round2_stress_final2.json`: 6,144 default draws, 5,856 lesson windows, and 3,456 exact overrides without failure.
- Packet `checks/round2_after_final/checks/056999828b88_after_battery_summary.json`: final 12/12 all-green source-bound battery.

### Known bounds

The ordinary shape pool filters free pentominoes/hexominoes to maximum span four for reliable placement on minimum-size inputs. The larger 7/8/9 morphology is intentionally a small teaching set. The tested feature-program family is broad but finite, so the evidence supports “no survivor in the tested family,” not a universal uniqueness proof.

October 3 maintainer merge (v6.1.0): retain the existing size-7/8/9 geometry witnesses and compact-output safeguards from review-a484b45ff0084d8c; add disconnected repeated-color objects and color-union/global-frequency rivals from review-70e94a4832b0e4a7 in slot 2. Slot 3 retains the original distinct-color geometry counterexample. The witness tool now reports both generated cases separately. The combined focused portable suite passes 21 tests; the first merge attempt had two tool/coverage failures (19 passed), corrected by keeping the geometry slot independent and updating the probe registry. No full battery or masked-solve rerun on merged bytes, no training admission, Racket unchanged.
## Current reviewer considerations

Source SHA-256: `ae4cb2c1c9a0d8ce46fcffdbdc1b313883b16790d8e4eb2db345631c5f09d5cc`.

# Decisions — review-70e94a4832b0e4a7

Scope: task `056999828b88` only. Before `bc97919dda1eb819382f21e94631520bf5478d8974622b61eea2203b0ac3f863`; final `ba6b1b6bc193ff05dac03e2e4d08e21029f28feda07a17fcc7490180af209e30`. Full source identities and sample denominators are in REVIEW and the JSON probes. This is a bounded distribution repair, not a rule rewrite or a new training framework.

## D1 — Object identity is connectivity, not palette membership (G1)

**Original choice:** distinct colors for all objects, enforced by `self_check`. The old notes discuss morphology and competing orderings but give no explicit rationale for color uniqueness; its rationale is unknown, plausibly an aid to canonical resemblance rather than a semantic requirement. The unchanged Racket and exact counterexample establish that disconnected same-color components are lawful.

**Chosen change:** allow repeated colors while retaining distinct component counts and geometric separation. This removes a validator exclusion that protected an incorrect abstraction. Keep same-color four-connectivity, cell-preserving cropped objects, top alignment and zero gutters.

**Rejected alternatives:** merely add a warning or declare a rival without emitting witnesses; modify Racket to match the narrow distribution; randomize colors without guaranteeing duplicate colors; loosen size ties at the same time. The first two do not repair the task support, the third leaves many ambiguous lessons, and the last broadens semantics unnecessarily.

**Probe:** minimal 8x10 shared-color example, actual Racket, independent rival implementations, red-before-green regression. See `QUESTION_ANSWER.md`, `checks/connectivity-before.json`, `checks/connectivity-final.json`.

**Limit:** allowing repeated colors does not establish coverage for every repeated-color layout or tie behavior. Each emitted object is still monochromatic; arbitrary touching/interleaved components remain outside the intended generator support.

## D2 — Guarantee the witness in one curriculum slot (G1)

**Original choice:** four-slot schedule, with canonical linked profiles in slots 0/1 and an I4/cross5/rectangle6 morphology adversary in slot 3. The earlier notes explicitly justify preservation of canonical support and a deterministic template/bbox-area refutation.

**Chosen change:** repurpose generalized slot 2 to give minimum and maximum component-size ranks the same color, retaining at least one differently colored rank between them. This is not just duplicate color: the shared-color total exceeds every other individual object size, so frequency ordering necessarily moves the smallest object out of first place. A single crop per color cannot reproduce the A,B,A interleaving. Existing separation prevents same-color components from merging.

**Rejected alternatives:** duplicate adjacent ranks only (weaker ordering evidence); share color on arbitrary random ranks (not uniformly frequency-refuting); replace all slots (loses canonical mass); replace slot 3 (regresses prior defense).

**Probe:** 18 bounded slot-2 combinations across 3 bands, 2 object counts and 3 seeds, plus witness/nonmutation regression and the 600-draw actual-Racket census. For fixed seed/band, every consecutive four-index window has slot 2. All 591 measured overlapping windows refute both rivals. This is a property of the schedule, not an estimate of independent lesson success probability.

**Limit:** arbitrary independently sampled seeds/indices can omit slot 2. Four consecutive indices and the declared lesson sampler matter. A learner seeing metadata could exploit scheduling; this is not a universal impossibility-of-shortcuts proof.

## D3 — Keep morphology and dimensional support bounded

**Original choice:** 49 free-polyomino classes through size 6 with maximum span 4, 3–4 distinct-sized objects, zero-majority background, separated placement; documented to broaden the earlier small morphology catalogue while remaining placeable.

**Chosen change:** reuse the existing generalized shape sampler and all placement bounds. No new dependency, no larger canvas requirement, no hard-coded replacement of generalized objects with a single fixture. Canonical style still excludes duplicates; general validator now includes them.

**Alternative:** build a much larger scene generator, equal-sized objects, diagonal contacts or larger shapes simultaneously. Rejected as unnecessary scope growth and a source of untested rule ambiguities.

**Probe:** `checks/shape-support-final.json`, final hash above: 600 draws at seed246810 yield 46 observed classes; 96 overrides at seed246811 pass. The pool still has49 classes, but finite sampling did not observe all of them. Version-dependent RNG means this is not an identical-board ablation.

**Limit:** finite morphology support, 3–4 objects and distinct sizes remain potential future memorization boundaries. No claim of indefinite training value or measured model generalization is justified by these tests alone.

## D4 — Register rivals and verify against authority, not just helpers

The baseline battery can only reject declared/tested alternatives, so adding two executable rivals, corresponding witness predicates, canonical-shortcut declarations and lesson competitors is necessary. Both rivals fit the stored canonical examples. The new independent probe parses components separately and invokes the unchanged Racket rather than taking `_size_pack` as truth. It records per-source SHA256, exact request identities, deduplicated board hashes, overlapping-window denominators and concrete outputs.

A smaller Python-only probe would be faster but circular for an authority claim; using only the generator's predicates would risk self-confirming a bug. The independent parser plus actual Racket parity was selected. The authoring tool must never be imported during the visible-only solve. Its first import failure is retained; staging the supplied tools resolves the missing namespace without replacing parser semantics.

## D5 — Keep linter and infrastructure findings separate (T1, T2)

Renaming `objects` to `comps` resolves the linter's lexical resemblance warning without muting lint or changing behavior. Both intermediate and final results remain so an importer will not mistake a green semantic report for a wholly green intermediate battery.

Do not change the unrelated shared timeout test just to make the repository green. Its200ms budget is shorter than this environment's ordinary Python readiness. The focused task tests and full generator battery pass; the whole repository remains169pass/1fail on both runs. Retain controlled timing diagnostics and report the failure. Audit-only targets likewise stay unchanged for separate maintainers.

## D6 — Preserve evaluation honesty and handoff

Run a genuine visible-only solve after final generator verification; disclose earlier exposure and do not access references/private labels during that phase. One first hypothesis fit all four demonstrations, so no fictional failed revision was manufactured. Query correctness is withheld, not inferred. Keep reviewer notes separate from captured model traces.

Return only the source-bound delta built by the packet helper, with exact commands and all failures. Neither the repair nor the green battery changes training admission. Authoring review is complete; model-training gain, held-out broad-layout evaluation, masked-query scoring and the unresolved shared test remain explicit next evaluation boundaries.
