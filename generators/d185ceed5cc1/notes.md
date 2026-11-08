# Working notes: d185ceed5cc1

## Current selected design

Source SHA-256: `77ecaed15d25d11dba9d95a1857f98a28f229b4ad3023f69da354b874ed210de`
Pinned canonical rule: `a1ebff603893`
Selected version: `3.0.0`

The authority scans each row independently. Color `8` cells are fixed walls. Each maximal run of cells that are not `8`, including leading and trailing edge runs, is a segment. Within each segment, nonzero pebbles keep their left-to-right order and are packed against that segment’s right edge. The generator returns inputs only; labels remain owned by the canonical Racket rule.

## Baseline finding and reversal

The packet baseline (`v2.0.1`) used full-height color-8 left/right borders plus one full-height internal wall, so every lesson reduced to two fixed chambers. Its `self_check` rejected two canonical inputs whose edge columns were not walls, the generator omitted the canonical full palette, several declared axes were dead or unobservable, invalid control scalars were accepted, and no task-linked semantic contract challenged plausible shortcuts.

**Reversal:** replace the fixed two-chamber scene with row-local wall signatures and open edge segments. This is required by the canonical examples and by the actual rule, not merely by marginal profile checks. No prior reviewer return was used as a repair lead; `evidence/associated_notes.jsonl` was empty, so the packet source, canonical pairs, and fresh baseline receipts were the evidence base.

## Input distribution and controls

The public exact axes are deliberately small and observable from returned pixels:

- `grid_h`: 4..6
- `grid_w`: 10..13
- `walls_per_row`: 2..4
- `pebbles_per_row`: 2..4

Every generated grid uses colors `0..9`, places the exact requested wall and pebble count in each row, and contains at least two different wall signatures. Difficulty changes only the weighting over the same lawful domains. Unknown axes, non-integer exact controls, invalid seed/sample-index values, negative sample indices, and unsupported difficulty values fail loudly.

## Teaching obligations

Every draw constructs three counterexamples:

1. `segment_locality`: pebbles in separated segments refute packing the whole row while ignoring walls.
2. `order_preservation`: a descending adjacent pair refutes sorting colors before packing.
3. `edge_segments`: a moving pebble in an open leading or trailing segment refutes processing only intervals bounded by walls on both sides.

The same three deterministic rivals are declared in `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`, with source-bound witness claims. `rule_mirror` is an independent Python implementation used only for tests and rival comparisons; the Racket authority still derives labels.

## Validation behavior

`self_check` accepts all five canonical inputs and the generated manifold. It rejects malformed/ragged grids, non-ARC cells, dimensions outside the canonical envelope, missing palette roles, uninformative fixed wall signatures, rows without pebbles, lessons with no ordered pair, and rule no-ops. `strict_canonical_like` intentionally shares this structural predicate.

Focused tests cover all five canonical input/output pairs, exact boundary overrides in every band, invalid controls, replay determinism/fresh-grid behavior, full-palette/profile support, malformed inputs, and all three rival counterexamples.

## Verification snapshot

- After battery: 12/12 stages green.
- Task tests: 39/39 passed.
- Profile floor: five canonical inputs accepted; exact profile 23/60; envelope 60/60.
- Semantic gate: strict 600/600; three witnesses fire in every band; 12/12 sampled lessons and 48 diagnostic rotations show no declared-rival ambiguity.
- Lesson census: 300/300 lessons and 1,200/1,200 query rotations; all three rivals eliminated, zero production or rotation ambiguities.
- Override contract: 7,110/7,110 accepted draws across 79 cases with zero findings.

## Known limits and open questions

The finite rival set is strong evidence against three concrete shortcuts, not a proof of universal identifiability. A generic undeclared-shortcut gate would add protection against future rival classes. The full-palette requirement mirrors the canonical population and is intentionally stricter than the bare transformation. No canonical Racket change was justified.

## Episode-level gravity proposal

Prior assessment rejected left/right gravity to preserve canonical execution. Current decision: retain a separate once-per-episode `gravity=right|left` prototype under workspace/parametric/, while canonical execution stays rightward with wall color8. Demonstrations identify the setting. Exact Racket programs supply every retained label; a Python segment oracle independently checks walls and pebble order. Owner evidence covers two episodes, eight separating pairs, five canonical pairs,21 Racket evaluations and four focused tests. This is proposed and not a production parameter API or variant approval; see workspace/parametric/evidence/manifest.json.
## Current reviewer considerations

Source SHA-256: `77ecaed15d25d11dba9d95a1857f98a28f229b4ad3023f69da354b874ed210de`.

# Decisions — d185ceed5cc1

## D1. Preserve the canonical Racket rule

**Choice.** Keep the selected authority unchanged and pin `RULE_HASH = "a1ebff603893"`.

**Original rationale.** The old generator omitted the pin; why it was omitted is unknown. The baseline rule smoke nevertheless showed the authority itself executed correctly.

**Alternatives.** Rewrite the rule; encode labels in Python; alter the rule to match the old two-chamber sampler.

**Probe.** All five canonical pairs agree with an independent Python mirror, rule smoke applied 120/120 instances without a crash, and authority sync passed.

**Failure mode avoided.** Changing correct authority semantics to accommodate a narrow generator.

**Limitation.** Racket style lint still reports nonblocking style notices in the canonical source; exact authority binding is preferred to cosmetic rewriting.

## D2. Replace full-height chambers with row-local wall signatures

**Choice.** Every row independently chooses 2–4 color-8 wall columns; at least two row signatures differ.

**Original rationale.** The old fixed borders and one internal wall made placement simple, but that rationale was undocumented and contradicted canonical inputs.

**Alternatives.** Retain fixed chambers and loosen `self_check`; vary only the internal wall; replay canonical layouts verbatim.

**Probe.** Baseline `self_check` rejected two canonical inputs because edge columns were not walls. The new checker accepts all five canonical inputs, and 60/60 generated draws remain within the canonical envelope.

**Failure mode avoided.** A model learning “two vertical chambers” instead of “maximal non-wall segment in each row.”

**Limitation.** Wall counts are uniform within a generated grid for an exact observable control, although positions vary by row.

## D3. Keep open leading and trailing segments lawful and mandatory

**Choice.** Include a movable pebble in a leading or trailing segment on every draw.

**Original rationale.** The old sampler bounded every chamber on both sides, so edge-segment behavior was never demonstrated.

**Alternatives.** Treat edge segments as rare; omit them; create a separate texture mode.

**Probe.** The `edge_segments` witness fires on 600/600 semantic draws and refutes `bounded_segments_only` on every checked firing; the 300-lesson census eliminates that rival in all lessons and rotations.

**Failure mode avoided.** A solver that processes only intervals between two color-8 walls.

**Limitation.** Requiring this witness on every grid is pedagogically deliberate and somewhat denser than an unconstrained natural sampler.

## D4. Preserve pebble order explicitly

**Choice.** Force a descending adjacent pair in a movable segment on every input.

**Original rationale.** The old random placements could accidentally make sorting indistinguishable from stable packing; no explicit rationale was recorded.

**Alternatives.** Rely on random colors; use repeated colors only; add a separate diagnostic texture.

**Probe.** `order_preservation` fires on 600/600 semantic draws and every checked instance disagrees with `sort_then_pack`; canonical-pair and generated tests cover the stable-order rule.

**Failure mode avoided.** A model sorting colors before placing them at the segment’s right edge.

**Limitation.** The descending pair is a constructed teaching feature, not an estimate of a naturally occurring color distribution.

## D5. Make segment locality explicit

**Choice.** Place pebbles in separated segments so crossing a wall changes the answer.

**Original rationale.** Fixed chambers implied locality visually, but did not guarantee that ignoring walls produced a different output on every row/example.

**Alternatives.** Depend on random placements; use a single segment per row; only test the shortcut offline.

**Probe.** `segment_locality` fires on 600/600 semantic draws; `ignore_walls` is eliminated in every sampled lesson and every query rotation.

**Failure mode avoided.** Whole-row compaction that treats walls as immovable holes but not segment boundaries.

**Limitation.** This establishes evidence against one concrete crossing-wall algorithm, not every possible locality shortcut.

## D6. Use the canonical full palette

**Choice.** Every generated input contains colors `0..9`, with `8` reserved for walls and the other nonzero colors used as pebbles.

**Original rationale.** The old generator sampled a smaller palette; no reason was recorded. Canonical pairs use the full palette.

**Alternatives.** Vary palette size; match only marginal distinct-color counts; reserve a canonical-profile submode.

**Probe.** Distribution gate reports generated palette 10 matching canonical palette 10, profile floor reaches 23/60 exact and 60/60 envelope support, and `self_check` accepts all canonical inputs.

**Failure mode avoided.** Role/palette drift that lets the model identify generated rather than canonical examples.

**Limitation.** Full palette is stricter than the abstract transformation and reduces palette diversity by design.

## D7. Expose only four exact, observable axes

**Choice.** Publish `grid_h`, `grid_w`, `walls_per_row`, and `pebbles_per_row`; recover each with `observe_overrides`.

**Original rationale.** The old surface exposed texture, density, palette, wall, and other controls, several dead, clamped, or unobservable.

**Alternatives.** Repair every legacy axis; retain diagnostic texture aliases; expose internal witness-row choices.

**Probe.** The final override gate accepted 7,110/7,110 draws across 79 cases with zero provenance or observation findings. Unknown axes fail loudly.

**Failure mode avoided.** Callers believing an override changed training data when it was ignored or silently clamped.

**Limitation.** Fine-grained layout controls are intentionally internal; exact public controls are preferred over a larger misleading Cartesian product.

## D8. Validate controls strictly

**Choice.** Reject booleans, floats, and strings for integer controls; reject negative `sample_index`, unknown axes, and unsupported difficulties.

**Original rationale.** The old permissive behavior was inherited from generic Python coercion and `**overrides`; no intentional rationale was found.

**Alternatives.** Coerce values; rely on `gen_ctx`; validate only advertised axes.

**Probe.** A focused red test first reproduced invalid seed/sample-index/difficulty acceptance. The repaired tests pass, and strict defect lint reports zero findings or warnings.

**Failure mode avoided.** Different call sites silently generating the same or malformed provenance under noncanonical control types.

**Limitation.** Strict typing rejects values such as NumPy integer scalars unless converted by the caller.

## D9. Use an independent Python mirror only as an oracle

**Choice.** Implement `rule_mirror` for tests and rivals, while deriving dataset labels from Racket.

**Original rationale.** The prior generator had no independent executable oracle.

**Alternatives.** Call Racket in every unit test; duplicate expected outputs manually; have the generator return input/output pairs.

**Probe.** The mirror matches all five canonical pairs and all 120 rule-smoke comparisons.

**Failure mode avoided.** Tests validating only generator structure while missing semantic drift.

**Limitation.** Two implementations can share the same misunderstanding; canonical-pair and Racket crosschecks reduce but do not eliminate that risk.

## D10. Do not promote hidden rule parameters

**Choice.** Keep direction fixed to right and wall color fixed to `8`.

**Original rationale.** Both are part of the canonical authority. Their prior fixed status was correct, though undocumented.

**Alternatives.** Episode-level `{left,right}` gravity; alternate wall colors.

**Probe.** `workspace/parametric/ASSESSMENT.md` shows that neither parameter is encoded in the input; varying either would require a separately pinned rule/task identity.

**Failure mode avoided.** Hidden episode semantics and mixed labels under one task ID.

**Limitation.** Potentially useful transfer variants are deferred to separately identified tasks.

## D11. Declare three concrete rivals, but not universal identifiability

**Choice.** Use `ignore_walls`, `sort_then_pack`, and `bounded_segments_only` as semantic rivals and lesson competitors. Do not claim a universal `lesson_identifiable` proof.

**Original rationale.** The baseline had no semantic contract.

**Alternatives.** Declare no rivals; write a broad but unverifiable identifiability hook; enumerate many speculative solvers.

**Probe.** Semantic gate and the 300-lesson/1,200-rotation census eliminate all three without ambiguity.

**Failure mode avoided.** Green morphology checks masking lessons that permit obvious wrong rules.

**Limitation.** Undeclared rival classes remain possible; this is finite evidence, not proof.

## Native parametric promotion — current reviewer build

The current promotion candidate supersedes the historical isolated left/right
`gravity.py` proposal. `packing_rule=all_right` is the exact canonical source.
`packing_rule=densest_left` first derives the unique pebble-count argmax among
maximal color-8-bounded segments in each row, then packs only that selected
segment left while packing all others right. The four-query curriculum includes
a dense 30×30 case and uses a strictly wider non-winning distractor in every
row.

A finite protected-Racket audit covered seeds 0 and 17, demonstration counts
2, 3 and 6, both settings, and nine executable rivals: 12 cases and 264 Racket
evaluations, with unique declared-setting survival and no rival surviving the
visible demonstrations. A separate Python sweep covered 40 setting/count/seed
cases. The wrong-intermediate witness substitutes widest-segment selection for
count-argmax selection and changes 420 cells on the 30×30 query. These are
bounded claims, not universal uniqueness. Native owner acceptance and training
admission remain pending.
