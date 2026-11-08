# Working notes: 39abddf600eb

## Review repair 2026-10-03

Baseline generator SHA `5f77c23cfa94456292533113ead81d027879bf707c68af09aaaa74dae6cbe4d3` failed five of twelve battery stages. Its validator rejected two canonical opposite-parity identity examples, `RULE_HASH` was absent, texture/axis metadata did not correspond cleanly to pixels, exact overrides were not reliable, and no executable semantic rival contract existed. No retained associated review note supplied a pending patch; diagnosis began from the current source and battery.

The selected generator was rebuilt as version `3.1.0` around one strict scene parser. The parser, public validator, override observer, independent tests, and Python rule mirror now agree on: one complete inset frame, two strict-interior seeds, and no other marks. Identity is intentionally lawful.

The strongest identified canonical-fitting shortcut is `diagonal_only`: leave aligned seed pairs unchanged. The final geometry schedule `axis, diagonal, axis, identity, axis, diagonal` guarantees at least two aligned pairs in every four consecutive draws. This matters because an earlier schedule passed production-order lesson sampling but failed 8/12 cyclic windows when its only aligned example became the query.

Final generator SHA: `420745b489f4080dca7e147cbf5882155aa610d4231aee0cf6303bccff731a06`.

Final measurements:

- battery: 12/12 green;
- portable selected tests: 96 passed;
- production census: 300/300 lessons, 1,200 unique inputs, no declared ambiguity;
- independent distribution: 1,000 unique draws, all five controls represented as applicable;
- cyclic query audit: 192/192 rotations identifying;
- independent Racket parity: 230/230;
- selected Racket authority: unchanged, hash `38c495fef5e9`.

Known limits: the generator intentionally bounds canvas and frame-margin ranges; schedule position could be metadata if leaked; and a finite named-rival contract does not prove universal induction. Future reviewers should run `workspace/reference_probe.py` after any schedule, axis, parser, or authority change.
## Current reviewer considerations

Source SHA-256: `420745b489f4080dca7e147cbf5882155aa610d4231aee0cf6303bccff731a06`.

# DECISIONS — 39abddf600eb

## D1 — Preserve the canonical Racket rule

**Decision.** Keep the selected authority unchanged and pin `RULE_HASH = "38c495fef5e9"`.

**Rationale.** An independent pixel oracle reproduced all 5 canonical pairs, and supported Racket execution matched it on 230/230 final cases. The defects were in the generator contract and distribution, not in the rule.

**Alternatives rejected.** Changing the rule to forbid identity outputs would contradict two canonical examples. Changing Manhattan distance to a diagonal-only construction would preserve a shortcut rather than the intended transformation.

**Failure mode / limit.** The Python mirror is supplementary. The Racket receipt remains the authority, and every selected-rule change must repin the hash and rerun authority sync.

## D2 — Treat opposite parity as a lawful identity branch

**Decision.** `seed_geometry="identity"` means the seed coordinate sums have opposite parity, so no integer cell has equal Manhattan distance. Identity output is explicitly allowed.

**Original rationale.** The baseline appears to have assumed every generated lesson must change, but that assumption is incompatible with canonical evidence. The original rationale for rejecting identity was not recorded.

**Probe.** Five canonical pairs include two identity pairs; all now pass `self_check`. Exact identity overrides produce lawful unchanged inputs in every difficulty band.

**Rejected alternative.** Filtering identity examples out of the grammar would make the validator reject canonical data and teach a false invariant. Emitting identity at one-third frequency was also rejected because it made demonstrations too often no-op; the final schedule emits it once per six draws.

**Limit.** A learner can still underweight the identity branch if episodes are sampled non-consecutively. Distribution consumers should not silently discard unchanged examples.

## D3 — Replace texture labels with five exact observable axes

**Decision.** Expose `grid_h`, `grid_w`, `frame_color`, `seed_geometry`, and `seed_color_relation`; declare no incompatible combinations.

**Rationale.** Each value is recoverable from pixels and all boundary combinations can be constructed on 8×8. This removes the baseline’s dead and overlapping texture knobs and makes typo rejection falsifiable.

**Probe.** The task tests exercise the full geometry × color-relation × difficulty cross-product at minimum dimensions, verify observed values, test numeric boundaries, and reject obsolete keys.

**Rejected alternatives.** `density`, `texture`, palette aliases, and singleton controls were removed because they did not map one-to-one to returned pixels. Hidden difficulty-local narrowing was rejected because it makes advertised global domains false.

**Limit.** The controls describe the generator’s selected teaching grammar, not all mathematical presentations of a Manhattan bisector.

## D4 — Use a strict pixel parser as the shared grammar boundary

**Decision.** Validate one complete inset rectangular frame, exactly two strict-interior seeds, no other marks, legal dimensions/colors, and a rectangular integer grid.

**Rationale.** The baseline self-check both rejected lawful scenes and admitted weak impostors. A single parser now powers validation, override observation, semantic classification, and the Python mirror, reducing contract drift.

**Probe.** Regressions mutate a lawful input into an open frame, extra mark, third seed, seed on frame, color-9 marker, bad dimension, malformed row shape, Boolean cells, and other invalid forms.

**Rejected alternative.** A generator-only assertion was insufficient because canonical, override, and adversarial inputs need the same public diagnostics.

**Limit.** `strict_canonical_like()` deliberately equals `self_check()` here. There is no smaller canonical-only submanifold beyond the declared lawful task grammar.

## D5 — Anchor four of every five shapes to canonical profiles

**Decision.** Use one of the five observed canonical `(height,width,palette-size)` profiles on indices not congruent to 4 modulo 5; draw the fifth from the complete declared size ranges.

**Rationale.** This guarantees profile-floor coverage while retaining broad size variation. Frame margins vary independently between one and two cells, and seed locations vary throughout the interior.

**Probe.** Each 120-draw band sees at least five distinct shapes, at least six frame colors, at least 116 unique inputs, and at least 72 exact canonical-profile hits. The independent 250-draw probe observed 39–42 distinct shapes per band and 171–176 exact profile hits.

**Rejected alternatives.** Always using canonical dimensions would create a size shortcut. Uniform broad sizes alone caused profile-floor failures in small samples.

**Limit.** The deterministic 4:1 anchor cadence is visible if raw sample indices are leaked; assembled lessons should not expose indices as semantic features.

## D6 — Choose a rotation-safe geometry schedule

**Decision.** Use `axis, diagonal, axis, identity, axis, diagonal`.

**Rationale.** The strongest rival fitting all canonical pairs is “apply the bisector only when seeds are not row/column aligned.” A three-demo lesson needs at least one aligned example after its query is removed. Every four consecutive examples therefore need at least two aligned cases.

**Probe.** The earlier schedule passed production-order lessons but failed 8/12 four-window cyclic query tests. The final schedule passes 12/12 local starts and 192/192 independent band/start/query rotations. The production census refuted the rival in 300/300 lessons.

**Rejected alternatives.** A simple `axis, diagonal, identity` cycle has only one aligned case in some four-windows and becomes ambiguous when that case is the query. A 50% or higher identity schedule was rejected as too no-op-heavy.

**Limit.** This contract names one strong rival. Future reviewers should add any newly discovered canonical-fitting competitor rather than infer universal identifiability from this finite set.

## D7 — Vary seed color relation independently

**Decision.** Emit same-colored seeds periodically (index 6 modulo 7), otherwise different colors; exact overrides support both.

**Rationale.** Seed colors are carried through unchanged and should not become a proxy for geometry or whether the rule fires. Periodic same-color cases break the assumption that two seeds must have distinct colors.

**Probe.** Every 250-draw band contains both relations and all frame colors 2–8. A first probe accidentally sampled only one residue class with `index*7+2`; that red test led to a consecutive-index sampling design and an explicit relation-coverage assertion.

**Rejected alternative.** Uniformly sampling relations was valid but made small deterministic coverage less predictable. Never emitting same-color seeds would leave an unnecessary shortcut.

**Limit.** Color relation is semantically irrelevant by design; it is a nuisance factor, not a new rule branch.

## D8 — Build and retain an independent reference probe

**Decision.** Add `workspace/reference_probe.py` and use it from task-local tests and review checks.

**Rationale.** Production helpers cannot independently validate themselves. The probe re-parses pixels, computes Manhattan outputs without importing production geometry functions, constructs the exact rival witness, measures distribution support, rotates queries, and optionally invokes the selected Racket authority.

**Probe result.** Generator SHA `420745b4…731a06`: 1,000 unique draws, zero validator/nondeterminism failures, 5/5 canonical matches, 230/230 Racket matches, and 192/192 identifying rotations.

**Limit.** It is task-specific and finite. Its counts depend on the recorded deterministic seed/index design in the report.
