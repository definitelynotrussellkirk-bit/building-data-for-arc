# Main-diagonal reflection — current generator decisions

Version 1.4.0; canonical rule hash 2b970065d6a3. Keep every nonzero source and add its transposed position. The canonical Racket rule is unchanged and supplies labels; generator.py only supplies inputs.

## Domain and repaired decisions

Ordinary inputs are square integer grids, side 4..18, background 0, nonzero colors 1..9. There is at least one source, no source lies on the main diagonal, and every reflected target is initially zero. Inputs may have sources above, below or on both sides. Collision precedence, diagonal-only, empty and already-symmetric cases remain outside the nontrivial teaching domain.

The previous above-only placement hid the lower-to-upper part of the rule: `upper_only` fits all 4 canonical labelled pairs. The new distribution adds below-only and mixed inputs. Distinct unordered transpose pairs prevent collisions by construction. The minimal saved counterexample is `counterexamples/upper_only_below_source.json`: a 5 × 5 grid with color 5 at (4,3), for which native Racket also adds 5 at (3,4). The repaired generator emits it with seed 0/index 0 and explicit size 5, cell_count 1, n_distinct_colors 1, position_bias=below_diagonal. The focused counterexample regression and workspace/probe_shortcut.py retain reproduction.

Four exact controls replace the previous ignored or truncated controls: size 4..18; cell_count 1..16; n_distinct_colors 1..9 foreground colors; and position_bias above_diagonal/below_diagonal/mixed. Every requested color appears. Unknown controls, scalar coercions and malformed seed/index/difficulty values are rejected. Joint infeasibility is reported with the actual conflicting caller axes. Unforced dimensions/counts adapt to valid forced requests. In particular, one forced source with unforced side selects a single side even in a normally mixed slot; forcing both one cell and mixed rejects.

The removed palette-kind, density and palette-size metadata did not implement the promised variation. Named diagnostic textures remain separate from exact production controls. The validator checks all cells, including zero-looking invalid scalar values. It accepts all 4 canonical inputs and the expanded collision-free teaching domain; strict_canonical_like does not mean a literal canonical shape match.

## Teaching and support

EXAMPLES_NEEDED=3. Default consecutive indices follow a seed-offset period 4 cycle: above, mixed, below, mixed. Every four-pair window has two mixed witnesses, so holding out any single query leaves a mixed demonstration; every three consecutive demonstrations contains a mixed witness. This guarantee concerns default sequential assembly. Explicit controls or independently sampled lesson elements require their own teaching check.

Five finite competitors are executable: upper_only, lower_only, transpose_only, anti_diagonal_echo and unchanged. The final strict semantic check accepts 600/600 sampled domain inputs. The larger source-bound census checks 300 lessons (100 per band), 1,200 pair positions/1,199 unique inputs and all 1,200 query rotations, with zero declared-rival ambiguity or execution/scoring warnings. The separate seed 0 period enumeration checks 12 lessons and 48 rotations from 15 unique inputs. These are bounded rival checks, not universal induction claims.

Every band retains weighted canonical-scale support while still offering all feasible sizes. The final 20 draws per band have exact profile hits of 7 easy, 7 medium and 11 hard; pooled 25/60 exact and 28/60 envelope. Original counts were 3/60 and 6/60, with no medium/hard exact hits. Mixture weights are an engineering choice, not a calibrated model-difficulty claim.

## Open limits and proposals

No unresolved task-local semantic defect is known from the retained checks. The period schedule, empty diagonal and collision-free domain are deliberate restrictions. No approval or training-admission record changed. The separate workspace/parametric prototype chooses main versus anti-diagonal reflection once per episode and produces Racket labels; it remains a proposed extension with its own conservative input domain and finite evidence. The workspace/review_tools packaging adapter is separately reviewed infrastructure, not production generator behavior. Full commands, failed iterations and counts are in the accompanying REVIEW.md, DECISIONS.md and checks/.
## Current reviewer considerations

Source SHA-256: `9ed6edce720cc2eb2adeb44ced6ce129345a1176f1fb43a3fcaa81ebfc9020c6`.

# Decisions — e58027e9749f

## D1. Preserve the fixed rule and repair the input distribution

The selected final generator is version 1.4.0, SHA-256
`9ed6edce720cc2eb2adeb44ced6ce129345a1176f1fb43a3fcaa81ebfc9020c6`.
The canonical Racket authority remains `2b970065d6a3`: overlay the original grid
with its transpose. Racket continues to produce labels. No canonical program,
catalog kind, shared runtime interface, or approval hash was changed.

The old sampler only placed sources above the main diagonal. Copying only those
upper sources therefore fit every canonical labelled pair while leaving the
lower-to-upper direction untested. The repair samples above-only, below-only,
and mixed-side sources. Each occupied cell belongs to a distinct unordered
transpose pair, and its reflected target begins as zero. This admits both source
directions while excluding color-collision precedence from the teaching domain.
`self_check` accepts lawful lower sources and checks every cell, including zero
background cells, for a genuine integer ARC color. Empty, diagonal-only,
already-symmetric and colliding patterns are outside ordinary generation.

The source-bound witness in `checks/shortcut/assessment.json` is a lawful 5-by-5
input with one color-5 source at `(4,3)`. The unchanged Racket rule also paints
`(3,4)`; the upper-only shortcut leaves that cell zero. The supported apply
receipt, rival output and generation provenance are retained beside it. Its
first resource-blocked apply attempt remains in
`checks/shortcut/initial-apply-enospc.log`.

## D2. Expose four exact, observable controls

| Control | Declared range | Meaning |
| --- | --- | --- |
| `size` | integer 4..18 | Square side length |
| `cell_count` | integer 1..16 | Exact occupied source count |
| `n_distinct_colors` | integer 1..9 | Exact number of foreground colors |
| `position_bias` | `above_diagonal`, `below_diagonal`, `mixed` | Actual occupied source side(s) |

Every control is recorded through the keyed generation context and can be
observed from the returned grid. Counts are neither truncated to capacity nor
silently coerced. Joint requests reject explicitly when colors exceed cells,
when one source is forced to be mixed, or when the requested size has too few
transpose pairs. The exception records the conflicting caller-specified axes.
When unspecified quantities can satisfy an exact request, generation chooses
feasible quantities instead of rejecting a lawful endpoint.

In particular, `cell_count=1` with no forced side must remain lawful even if the
current teaching slot normally requests mixed sources. It falls back to a
seed-selected single side. Explicit `cell_count=1, position_bias='mixed'` remains
an incompatible request. These custom controls can remove a default teaching
witness, so custom episode assembly must check the resulting lesson.

Dead palette-kind, density and texture-alias controls were removed from `AXES`
instead of advertising them as working variation. Distinct foreground color
count is now an actual control. The three named diagnostic textures remain
explicit probes and cannot be combined with production controls; they do not
count as helpful production variation.

The intermediate after run still accepted malformed identity scalars. The final
source now rejects Boolean or noninteger seeds, noninteger/negative sample
indices, and invalid difficulty values before constructing a generation context.
`checks/reflection-identity-red.log` retains the failing regression, and
`checks/reflection-tests-final.log` records the 15 tests then passing. The retained-counterexample regression raises the current main suite to 16 tests, all passing in `checks/reflection-tests-current.log` and the final isolated task stage.

## D3. Teach both source directions without fixing a privileged query slot

Default inputs follow a seed-offset period-four cycle:
`above_diagonal, mixed, below_diagonal, mixed`. Four consecutive labelled pairs
therefore contain two mixed witnesses. Three consecutive default demonstrations
contain a mixed witness; holding out any one of a four-pair window also leaves
one. The intended ordinary episode is three demonstrations plus a query.
The rule, sampling pattern and labels remain independent of which labelled pair
is later treated as the query.

The finite competitor set has five behaviors: upper-only echo, lower-only echo,
transpose without preserving originals, anti-diagonal echo, and unchanged input.
The upper-only behavior is also declared as a canonical shortcut. A mixed input
refutes either directional-only shortcut. Separate exact examples and executed
lesson checks assess the remaining rivals. This is evidence against those
specific competitors, not proof that every possible solver hypothesis is unique.
The deterministic teaching schedule is a deliberate restriction, not a measured
optimum or evidence of downstream training gains.

`checks/schedule-final-s0.json` and its companion summary bind the final source,
seed 0 and explicit period enumeration. Overlapping windows and rotated holdouts
reuse labelled pairs; their counts must not be described as independent draws.
The fixed-seed run materialized 12 lessons and 48 query rotations from 15 unique grids, with zero declared-rival ambiguities. The final larger census (`checks/lesson-census-final.json.gz`, companion summary and compression manifest) materialized 300/300 lessons, 100 per band, comprising 1,200 pair positions and 1,199 unique inputs. Both production and all 1,200 query rotations had zero ambiguities against the five actual declared rival behaviors, and no materialization/scoring errors or hook warnings. Exact instances and seeds remain in the lossless report. The first larger run stopped with ENOSPC after 224 lessons and 896 rotations; it is retained under `checks/lesson-census-final-enospc/`, separately from the successful serial retry. Neither census proves all-seed or unrestricted identifiability.

## D4. Preserve canonical scale in each difficulty band

The sampler retains broad legal sizes and counts while weighting sizes 5..7 and
foreground color counts 3..4, preserving the canonical size/palette neighborhood
in every band. This replaces the old band separation that gave medium and hard
no exact canonical-profile hits in the retained small census. No canonical input
is replayed, and the mixture weights are not claimed to be calibrated model
difficulty.

The profile-floor stage uses 20 draws per band, 60 in total:

| Evidence | Exact canonical profile | Canonical envelope | Exact hits by easy / medium / hard |
| --- | --- | --- | --- |
| Before | 3/60 | 6/60 | 3/20, 0/20, 0/20 |
| Final | 25/60 | 28/60 | 7/20, 7/20, 11/20 |

See `checks/before/checks/e58027e9749f_before_profile_floor.json` and
`checks/after-final/checks/e58027e9749f_after_profile_floor.json`. These are finite
profile measurements, not population frequencies or a guarantee for every seed.
The final check has no zero-support band in this sample and no profile warning.

## D5. Keep failed iterations and source-bound verification distinct

The before battery used generator SHA-256
`d2462d071ec53bcb2625ad1c02bd4e7f90956718221518a3053f94907430b34c` and
reported seven green, two advisory, and three failed stages. Its reports and logs
remain under `checks/before/`. Advisories are not described as passing evidence.
The intermediate source
`502fce32d205397ea4475a5ef306611ad7aa3c26a29865e39826c2f648e6c3f8`
reached eleven green and one failed stage; `defect_lint` found the identity-scalar
acceptance described above. See `checks/after-v1/`.

The final source's battery is retained under `checks/after-final/`, with result
and runtime manifests binding the exact source. All twelve stages exited zero
and are green: lint, selfcheck, rule smoke, defect lint, distribution gate,
profile floor, semantic gate, diversity, override, grammar, Racket lint, and
authority sync. The run required rotation identifiability and used the final
source-bound schedule census. This records performed checks; it does not grant
approval or training admission, replace fresh-return replay, or imply unrestricted identifiability.

## D6. Keep the rule parameter extension a separate proposal

The runnable **prototype** under
`generators/e58027e9749f/workspace/parametric/` introduces one bounded hidden
parameter, `reflection_axis`, with `main_diagonal` as the original setting and
`anti_diagonal` as an alternative. It chooses the setting once per seeded
episode. Both preserve source cells; only the executed reflection changes.
Neither the selected production generator nor the canonical rule is parametric.

`checks/parametric/episodes-s23/` retains a complete three-demo/two-query episode
for each setting, exact materialized Racket programs and hashes, actually
executed rival outputs, a differentiating single-source witness, and source/runtime
receipts. Public files contain only demonstration pairs and query inputs. Private
parameters, programs, query answers and provenance remain separate. Every retained
demonstration distinguishes the two declared settings before a query needs that
distinction. Labels are executed through the included real Racket bridge.

The prototype uses square grids of size 4..10 and avoids both diagonals' fixed
points and reflected-target collisions. Input rejection has a finite cap. The original six-test and two-episode receipts bind the prior prototype source; both emitted Racket program texts are unchanged. Official isolated staging then exposed a dependency-root mismatch. The added fresh-process regression reproduced it, and the prototype now uses the manifest-selected execution root when present. All seven current prototype tests pass together with the sixteen main-generator tests in `checks/task-tests-private-v2/`. Initial missing-implementation failures, the resolved raw-checkout import failure, the corrected CLI property bug, and the portability red/green evidence remain in `checks/parametric/`.
This bounded extension does not claim all-seed validation, arbitrary hypothesis
uniqueness, a production rule API, or approval of the alternative.

## D7. Constrained packaging and honest solve records

The task-workspace ZIP-backed original-file view is an optional packaging
prototype, described in F1 of `FEEDBACK_TO_CODEX.md`. It invokes the unmodified
official return builder and validators and authenticates original archive bytes,
physical overrides and a pinned historical extraction receipt. It does not alter
shared interfaces. Its current-bytecode guard avoids importing stale or poisoned
cache code in place of verified source. The original protected metadata and
selected baseline remain physical. Focused tests and failed fixture iterations
are retained under `checks/packaging-tool/`; final return construction/replay must
be reported from their actual receipts.

The first selected-task solve preparation recorded `status='blocked'`, zero attempts and `Episode generation blocked: OSError` in `checks/solve-prepare.log`. Its successful retry produced a challenge from the final generator bytes. One later checker invocation lost its captured output while evidence writing exhausted space; its child exit is unknown and the public revision count remained zero. The retained actual revision 1 then executed and matched 3/3 visible examples, and the solve was finished with earlier exposure=yes and reference-consulted-during-solve=no. Both query outputs remain privately scored by the maintainer; the reviewer sees correctness=unknown. The separate blind solve was finished before source inspection, also with 3/3 visible agreement and withheld query correctness. F2 proposes an actionable, sanitized resource-error report. Resource failures, natural solution attempts, and diagnostic alternatives remain distinguished.

## D8. Self-review and remaining domain limits

I checked whether the repair merely replaces the upper-only shortcut with another directional shortcut: mixed demonstrations refute both directional rivals, and the retained lower-source witness makes the original shortcut failure concrete. The schedule and collision-free domain remain deliberate distribution restrictions; generated labels and the five tested rival checks do not settle collision precedence, arbitrary independent episode assembly, or unknown hypotheses.

No composition curriculum is proposed: this is a single geometric reflection with preservation, not evidence of systematic generalization to composed operations. A second parameter was rejected as unnecessary for this review; the reflection-axis prototype supplies a meaningful, demonstrably distinct bounded extension.

## D9. Finish with exact-delta replay and fresh tests

The unchanged official builder/validator produced a candidate with a 13-file task patch. The public replay command extracted the declared runtime dependency closure (331 of 76,257 original files), initialized Git at the exact fresh WORK root, checked and applied every patch, and verified every changed path. All 36 focused tests passed from that fresh checkout: 16 main-generator tests, 7 current parameter-prototype tests and 13 packaging-helper tests. There were no errors, failures or skips, and every changed-file hash still matched after testing.

The official replay receipt remains unchanged with its truthful `patch_replay_passed_tests_pending` status; the separate driver receipt and JUnit output record the later successful tests. Both receipts and the extraction inventory are retained under `checks/replay-candidate/`. The tested patch SHA-256 is `e5b5a5f82d8e1e27e53cacdb1cea98305ee1083e722fa8992341ba1d52acf6f0`; only root reports and evidence were finalized afterward. `checks/packaging/replayed-source-identity.json` binds the final source delta and exposed solve to that tested generator. No task-local blocker remains. The parameter extension and shared API suggestions remain separately proposed.
