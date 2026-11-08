# Working notes: 9fc0b6db96fe

## 2026-10-03 review

Baseline generator SHA-256: `deb2203b28b3061524ffd2c6ef3e9231578069853f3ad15cb10042afb92b78ae` (version 2.1.1). Final generator SHA-256: `fe39314e07c4a466c482a6f37f052a404c7f11220840e998d8f748e02ad56c96` (version 3.1.0). No associated prior-review notes were present, so no earlier return was used as a repair lead.

The baseline generated lawful-looking examples but lacked `RULE_HASH`, advertised dead or overlapping texture/density controls, admitted weak impostors through `self_check`, and did not guarantee that legend order or transform key mattered. It also sampled dimensions/counts outside the exact canonical profile set.

The replacement is constructive and source-bound to the unchanged canonical rule. It uses the five observed `(height, width, legend-count)` profiles, three observable legend layouts, distinct legend colors, separated curated 3–5-cell motifs, and a body-color derangement. At least one motif is key-sensitive for every nonidentity transform. The strict validator enforces those claims, and executable rivals test body-scan order and ignoring the key.

A 12-lesson semantic smoke initially passed, but a 300-lesson source-bound census over all four cyclic query positions found 17/1,200 windows in which three identity demos allowed the `ignore_key` rival to survive and change the query. Version 3.1.0 therefore uses a seed-permuted four-cycle over `sample_index`; every four consecutive default examples expose keys `{1,2,3,4}`. The rerun found 0/1,200 unidentifiable windows, with 400/400 unique inputs in each band.

Known scope limits: this is deliberately a canonical-support sampler, not a claim that the five profiles or curated motifs exhaust every lawful input. The four-cycle is a curriculum constraint; its order is independently shuffled by seed and difficulty, and explicit key overrides remain available. A 100-seed-per-band cross-tab covered all 20 key/profile and all 12 key/layout combinations.
## Current reviewer considerations

Source SHA-256: `fe39314e07c4a466c482a6f37f052a404c7f11220840e998d8f748e02ad56c96`.

# Decisions for 9fc0b6db96fe

Final generator SHA-256: `fe39314e07c4a466c482a6f37f052a404c7f11220840e998d8f748e02ad56c96`. The canonical Racket source was not modified.

## D1 — Keep the authority; repair the sampler

**Baseline rationale.** The version 2.1.1 docstring said it replaced an older generic scatter generator because that generator lacked a key/legend and could crash or produce no meaningful output. No associated prior-review note supplied further rationale.

**Decision.** Keep the canonical crop/transform/pack rule unchanged and pin `RULE_HASH = "0235d1a8fb27"`. The observed defects were in input construction, declared controls, and teaching support, not in the authority.

**Alternatives rejected.** Rewriting the Racket rule to tolerate malformed inputs would have hidden generator defects and changed task semantics. Broadening the rule or canonical examples was unnecessary because all five canonical inputs already agree with an independent oracle.

**Probe and failure mode.** `reference_probe.py` mirrors the rule independently and the Racket-enabled task test checks all canonical pairs plus a cross-product of generated controls. A future rule edit must change the hash and rerun parity rather than silently inheriting this pin.

## D2 — Exact canonical profiles instead of free width/count axes

**Decision.** Replace `grid_w` and `n_colors` with one exact `profile` axis over:

- `h9_w15_n4`
- `h9_w14_n4`
- `h12_w15_n3`
- `h11_w13_n4`
- `h9_w15_n3`

Each name encodes the input height, width, and legend count. Every profile is reachable in every difficulty band.

**Rationale.** The canonical set contains only these linked combinations. Independent width/count sampling created combinations with no canonical support and made it easy to confuse marginal diversity with task support.

**Alternatives rejected.** A rectangular envelope of all heights, widths, and counts would be broader but would invent unsupported combinations. A single dominant profile would be safer but unnecessarily narrow.

**Probe, failure modes, limits.** The profile-floor gate hit exact canonical profiles 60/60. The limitation is deliberate: this is not a complete grammar for all inputs accepted by the Racket program.

## D3 — Difficulty changes frequencies, not legality

**Decision.** All three bands share the same five profiles, with different profile weights. Easy favors smaller three-legend cases, medium favors 9×14 and 11×13 four-legend cases, and hard favors taller/larger profiles.

**Rationale.** Difficulty should alter the distribution without creating a band-specific unsupported domain or making an exact override illegal.

**Alternative rejected.** The first repaired draft used the same profile draw in every band; `checks/difficulty-red.log` proved all sampled bytes were identical across bands. Completely disjoint profile sets would have made band a shortcut and would fail all-profile support.

**Probe and limit.** The regression requires at least 40/64 seed/index triples to differ across bands; final profile floor still finds all canonical support. Difficulty is only a sampling prior, not a measured cognitive-difficulty guarantee.

## D4 — Three exact, observable public controls

**Decision.** Advertise only `profile`, `key`, and `legend_layout`. `observe_overrides` recovers all three from returned pixels, and unknown or wrong-typed overrides fail loudly.

**Rationale.** The baseline `density` was a singleton and its texture/palette controls were aliases or dead branches. An advertised exact axis should be both honored and observable.

**Alternatives rejected.** Retaining diagnostic-only aliases would add API surface without independent behavior. Advertising component shape or color sequence as an exact axis would require a much larger stable domain and was not needed for this review.

**Probe and failure mode.** The final override gate accepted 5,400/5,400 draws over 60 cases and three bands. New axes should not be added unless they can pass the same provenance/observation contract.

## D5 — Distinct legend colors, separate from the key color

**Decision.** Sample three or four distinct colors from ARC colors 1–9 excluding the key value.

**Rationale.** This keeps the top-left transform code unambiguous and guarantees one color identity per legend/body component.

**Alternatives rejected.** Reusing the key as an object color is legal at the raw-cell level but makes parsing less clean and is absent from the canonical examples. Duplicate legend colors would destroy the one-entry/one-component mapping.

**Probe and limit.** `self_check` rejects key/legend collisions, duplicate legend entries, unknown body colors, and missing/duplicated components. Color choice remains semantically irrelevant by design.

## D6 — Three legend layouts

**Decision.** Support `contiguous`, `spaced`, and `mixed` row-0 legend positions for both three- and four-color profiles.

**Rationale.** The rule ignores zeros and reads nonzero legend entries left-to-right. Varying spacing prevents a solver from assuming the legend always occupies a fixed contiguous prefix while preserving the same semantic order.

**Alternatives rejected.** Arbitrary positions across the whole row would add little value and complicate exact observation. One fixed layout would permit a positional shortcut.

**Probe and limit.** All 12 key/layout cells appeared in each band's 100-seed schedule self-review. The three layouts are representative, not exhaustive.

## D7 — Curated connected 3–5-cell motifs

**Decision.** Use rotations/reflections of a small curated motif bank, with exactly one connected 3–5-cell monochrome component per legend color.

**Rationale.** These sizes match canonical morphology, fit all profiles without rejection-heavy packing, and preserve meaningful crops including internal zeros.

**Alternatives rejected.** Unbounded random walks can self-overlap, collapse after normalization, or create hard-to-place shapes. Single cells and rectangles make transforms frequently invisible. Large polyominoes would force profile-specific rejection loops.

**Probe, failure mode, limit.** `self_check` verifies one component and 3–5 cells per legend color. The motif bank is finite and therefore not a universal shape distribution.

## D8 — Make both semantic decisions answer-relevant

**Decision.** Body colors are placed in a derangement of legend order. For keys 2–4, the first motif is drawn from motifs whose transformed crop differs from the original.

**Rationale.** Without these constraints, a model can use body scan order or ignore the transform on symmetric shapes and still receive the correct answer.

**Alternatives rejected.** Merely measuring witness frequency after unconstrained sampling leaves avoidable nonteaching examples. Reject-and-redraw loops are less deterministic and can bias shapes unpredictably.

**Probe and failure mode.** The final semantic gate observed the legend-order witness 600/600 and the key-transform witness on every nonidentity draw (451/600 overall). The identity key correctly does not fire the transform witness.

## D9 — Constructive separated slots

**Decision.** Place four components in top/bottom × left/right slots; place three in top-left, top-right, and bottom-center slots. Positions jitter within bounded regions but are constructed not to overlap or touch across colors.

**Rationale.** The authority finds nonzero connected components. Orthogonal touching between colors would merge objects and change the rule's component interpretation.

**Alternatives rejected.** Global rejection sampling was more complex and could silently drop a component after too many attempts. Fully fixed coordinates would reduce diversity.

**Probe and limit.** The validator rejects orthogonally touching different colors and verifies component realization exactly once. Spatial layouts are structured and do not cover every lawful placement.

## D10 — Strong validator and independent oracle

**Decision.** `self_check` validates rectangular ARC grids, canonical profile, blank separator row, key and legend grammar, body colors, separation, component count/size, and body-order disagreement. `strict_canonical_like` delegates to it. `reference_probe.py` implements an independent oracle; Racket remains label authority.

**Rationale.** The baseline validator accepted minimal grids that did not support the intended task. A strong validator makes distribution claims falsifiable and lets mutation tests catch missing constraints.

**Alternatives rejected.** Calling the generator's own `reference_output` from every test would be self-confirming. Requiring Racket for every small structural test would be slower and obscure simple failures.

**Probe and failure mode.** The final self-check gate accepted 60/60 defaults plus 5/5 canonical inputs and rejected 60/60 destructive mutations. The independent oracle is parity-checked against Racket in the task suite.

## D11 — Executable rivals and lesson identifiability

**Decision.** Declare two named rivals: output components in body scan order, and ignore the transform key. `lesson_identifiable` fails only when a rival fits every demo but changes the query answer.

**Rationale.** Per-example witness frequency does not prove a complete 3-demo lesson rules out a shortcut.

**Alternatives rejected.** A prose-only semantic claim cannot be gated. Failing whenever a rival matches demos, even if it is answer-equivalent on the query, would create false positives.

**Probe and limit.** The built-in 12-lesson smoke passed, but the larger census found the real 17/1,200 failure. The rival set is explicit and useful, not exhaustive of every conceivable solver heuristic.

## D12 — Seed-permuted four-key schedule

**Decision.** Default keys follow a permutation of `[1,2,3,4]` keyed by `(seed, difficulty, version)`, indexed by `sample_index mod 4`. Explicit `key=` overrides still use the full domain.

**Rationale.** The actual trainer assembles three demos plus one query from consecutive indices. Random independent keys allowed three identity demonstrations and a nonidentity query; 17/1,200 cyclic windows were ambiguous under the declared `ignore_key` rival.

**Alternatives considered.** Resampling a whole lesson until it contains a nonidentity demo would couple generator and lesson builder and would not protect every cyclic query choice. Forcing only one nonidentity key per four would still leave some cyclic windows with weak transform diversity. A fixed global sequence would create a stronger position shortcut.

**Probe, failure mode, limit.** The order is seed- and band-permuted, every consecutive four indices contain all keys, all cyclic 3+1 partitions are identifiable, and the override gate passes. The schedule is periodic within one seed; a future lesson builder that uses nonconsecutive indices should rerun `lesson_census.py` rather than assume this guarantee transfers.

## D13 — Retain reusable review tooling

**Decision.** Add a focused task test suite, `reference_probe.py`, and `lesson_census.py` under the selected task.

**Rationale.** The general battery intentionally uses small smoke samples and does not automatically discover task-local tests. Future changes need cheap, source-bound reproductions of the exact failures found here.

**Limit.** `lesson_census.py` must run in a prepared runtime because it imports the shared sampler and uses canonical Racket outputs. Its report states the sampler and denominator so results are not mistaken for universal coverage.

## 2026-10-25 native parametric handoff

The production generator and canonical authority were intentionally left unchanged. The current generator SHA-256 is `fe39314e07c4a466c482a6f37f052a404c7f11220840e998d8f748e02ad56c96`; the exact canonical Racket program SHA-256 is `0235d1a8fb2788cc7403eedb924bd58c4c7f9cd039a7b1050548ca37c533719b`.

A task-local native family now exposes episode-fixed `transform_source`. `explicit_key` is byte-identical to the canonical rule. `first_component_size` selects the first legend component, measures its occupied size, derives transform key 2/3/4 from sizes 3/4/5, then applies that derived transform to every legend-ordered component before gallery packing. The sampler supports 2–6 demonstrations and four prefix-stable queries, including a distributed 30×30 case, while keeping inputs matched across settings.

Final retained checks: 284/284 staged tests; a 32-seed finite declared-rival audit covering 192 episodes and 1,472 labeled pairs with no harmful survivor; protected-Racket qualification at 2, 3, and 6 demonstrations (32 + 40 + 64 executions); 16 saved one-query public views; and a protected counterfactual replay whose wrong last-component-size intermediate changes 6 final cells. `checks/handoff-validation.json` independently rehashes and reconciles all bound artifacts.

Status is reviewer-ready only. The next action is exact-byte owner integration followed by fresh native qualification, causal replay, and owner acceptance; no training admission is implied.
