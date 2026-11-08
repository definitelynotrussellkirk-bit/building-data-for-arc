# Working notes: 7842d7d91514

## Intended rule

A four-connected color-5 component is the template. Each four-connected color-2 candidate is compared after translation normalization **without** rotation or reflection. Exact same-orientation matches become color 4; all nonmatches become color 1. Background and the template are preserved. Canonical rule hash: `9d86bc23e927`.

## Review finding

Imported version `1.1.1` did not bind itself to the canonical rule, used fixed slots plus sparse extra color-2 pixels, exposed dead or narrowed controls, leaked noncanonical structure/palette roles, accepted unknown overrides, lacked a semantic/lesson contract, and had a comment-only divergence between selected authority copies. The baseline battery consequently failed lint, defect lint, override coverage, and authority synchronization; canonical-profile support was 0/60 and the semantic gate reported no contract.

## Repair decisions

Version `2.0.0` uses a constructive six-slot layout with one color-5 template and isolated color-2 polyomino candidates. Every draw includes both exact matches and nonmatches, and at least one nonmatch is a same-size rotation/reflection of the template. All candidates have the same cell count, so neither size nor dihedral-invariant matching can solve the task. The public axes (`grid_h`, `grid_w`, `n_matches`, `n_distractors`, `shape_size`) are exact, observable, available across all difficulty bands, and validated strictly; unknown keys and malformed seed/index/difficulty values are rejected.

The generator declares `RULE_HASH`, an independent Python `rule_match`, lesson-identifiability hooks, four plausible rival rules, canonical shortcuts, semantic witnesses, canonical-like validation, and strict self-checks. The authority repair removes only the divergent comment so `target_code`, `raw_code`, and canonical source are byte-identical.

## Test-first record and reversals

The task-local suite was written before implementation and initially produced 29 failures / 7 passes. One apparent later failure was a **test-helper bug**: `_normalize` consumed an iterator twice; the production implementation was not changed for that. A lint warning on the local name `objects` was eliminated by renaming it to `items_to_place`; this was a nonsemantic source change, so the independent probe was rerun and rebound to the final generator hash.

An early quick multi-stage command was externally interrupted and left a `status: running` artifact; it is not used as passing evidence. The complete managed after-repair battery, the source-bound rotation gate, the 300-lesson census, and the final focused suite are the completion evidence.

## Retained evidence

- Final generator SHA-256: `f26db115c7c8f4efc378a62d2442d3785d9bad978b1ece9613976b2408888d7f`
- Focused tests: 38 passed.
- Full after-repair battery: 12/12 stages green.
- Independent probe: 300/300 lawful and unique; 82 canonical-profile hits; every draw contains a same-size dihedral witness and refutes all four declared rivals.
- Lesson census: 300 lessons, 1,200 labeled pairs, 1,200 query rotations, zero ambiguity or materialization/scoring errors.
- Concrete source-bound witness: `counterexamples/exact-vs-dihedral.json`.

No unresolved correctness issue is known for the selected generator. Catalog approval remains an external catalog decision rather than something this review changes.
## Current reviewer considerations

Source SHA-256: `f26db115c7c8f4efc378a62d2442d3785d9bad978b1ece9613976b2408888d7f`.

# Decisions for `7842d7d91514`

## D1 — Preserve the canonical operation

**Choice.** Keep the canonical rule: compare each four-connected color-2 component with the four-connected color-5 template after translation normalization only; exact same-orientation matches become 4 and all others become 1.

**Original rationale.** The canonical pairs and rule hash `9d86bc23e927` agree on this operation. The imported generator's shortcomings were distribution and contract defects, not evidence that the task operation itself was wrong.

**Rejected alternatives.** I did not make matching rotation/reflection invariant, add a second operation, or change output colors merely to increase complexity. Those choices would contradict canonical labels.

**Probe and failure mode.** Task tests compare an independent Python oracle with all canonical pairs and generated cases; a retained Racket-verified counterexample isolates exact matching from the dihedral rival. The Python mirror remains test support, not authority.

## D2 — Use constructive isolated components instead of retries and stray pixels

**Choice.** Build a six-slot scene containing one color-5 template plus isolated color-2 candidates. Shapes are connected 3×3 polyominoes of size 3–5 with a nontrivial dihedral orbit.

**Reason.** Direct construction guarantees parseable components, exact counts, and total behavior across the advertised joint domain. It removes the baseline's unrelated color-2 pixels and fallback ambiguity.

**Rejected alternatives.** Random placement with retries was rejected because failed placement can silently weaken controls. Fixed singleton pixels were rejected because they become unintended candidate components. Large free-form canvases were unnecessary for this local rule and would increase packing failure risk.

**Limit.** Slots are structured rather than uniformly random. This may create positional regularity, but position is not an advertised semantic axis; shape assignment varies, and every lesson is checked against declared rivals.

## D3 — Make cell count deliberately uninformative

**Choice.** Every candidate has the same number of cells as the template, while at least one distractor is a rotated/reflected orientation of it.

**Reason.** A generator for exact orientation-sensitive shape matching should not let the model succeed by counting cells or treating all dihedral transforms as equivalent.

**Rejected alternatives.** Mixing candidate sizes would add superficial diversity but make `match_by_cell_count` a high-value shortcut. Using only unrelated shapes would not teach the orientation boundary.

**Probe.** `workspace/shape_probe.py` found a same-size dihedral witness and disagreement from both size-only and dihedral rivals in all 300 final-source draws.

## D4 — Exact public controls

**Choice.** Advertise only five recoverable axes: `grid_h` 11–14, `grid_w` 12–16, `n_matches` 1–2, `n_distractors` 1–2, and `shape_size` 3–5. Keep the same legal domains in all difficulty bands.

**Reason.** Each control is observable from the final grid and jointly constructible. Difficulty may influence defaults but must not invalidate an exact user override.

**Rejected alternatives.** Palette, arbitrary position, orientation code, and per-object shape IDs were not exposed because they would either be fixed by the task grammar or require a more complex observation contract. Unknown keys and implicit coercion were rejected because they hide caller defects.

**Probe.** The full override stage completed 10,620 draws, including unknown-key rejection and complete supported-domain coverage.

## D5 — Exact palette grammar

**Choice.** Generated inputs use only background 0, candidate 2, and template 5.

**Reason.** These are task-defined roles in the canonical problem, not interchangeable cosmetic colors. Additional input colors create roles the authority does not define.

**Rejected alternative.** Palette randomization was rejected because the canonical rule is explicitly color-coded; permuting roles without an independently transformed authority would be invalid.

## D6 — Lessons and query policy

**Choice.** Production lessons contain three demonstrations and one query. The sampler accepts consecutive lawful draws; the contract requires every lesson to refute declared rivals. Downstream query rotation is supported and was tested by holding out each of the four labeled pairs in turn.

**Reason.** Three examples provide repeated positive and negative evidence without inflating lesson length. Every individual draw already contains both branches and an orientation near-miss, so the lesson does not depend on a fragile schedule residue.

**Evidence.** The census materialized 100 lessons per band: 300/300 production lessons and 1,200/1,200 rotations had no declared-rival ambiguity, with 1,200 unique inputs and no hook, scoring, or materialization errors.

**Limit.** The gate checks declared and bounded searched rivals. It cannot prove uniqueness against every computable rule.

## D7 — Authority synchronization without behavior change

**Choice.** Remove one comment from selected `target_code` so it exactly matches selected `raw_code` and canonical source.

**Reason.** Exact source binding was failing although executable behavior was unchanged. A comment-only repair is the smallest source-bound correction.

**Rejected alternative.** I did not alter canonical program behavior or rewrite archival evidence.

## D8 — Independent future-agent probe

**Choice.** Retain `workspace/shape_probe.py` plus tests.

**Reason.** Production helpers, tests, and semantic hooks can share the same mistaken parser. The probe separately implements components, normalization, the intended oracle, and four rivals and records a replayable first witness.

**Reversal recorded.** The first probe report was bound to a pre-final source hash because a later local-variable rename changed bytes without changing semantics. I reran the probe after that rename; `checks/shape-probe-final.json` is bound to final SHA `f26db115…`.

## D9 — Honest interrupted evidence

A quick multi-stage command was externally interrupted and left a `status: running` artifact. I retained it as intermediate evidence but did not count it as a pass. Completion claims rely on the finished full after battery, focused suite, required-rotation gate, final probe, and lesson census.

## 2026-10-24 parametric MAIN review (`review-7a4fc6efb1c1072c`)

### D10 — Preserve the exact default and add one input-derived sequential setting

The production generator and canonical authority remain byte-for-byte unchanged at
`f26db115c7c8f4efc378a62d2442d3785d9bad978b1ece9613976b2408888d7f` and rule hash
`9d86bc23e927`. A task-local native family now exposes `target_rule=exact` (default,
canonical program bytes unchanged) and `target_rule=selector_rotation`. In the new
setting, A counts the connected color-8 selector, the count determines
`quarter_turns`, and B rotates the normalized color-5 template before matching all
color-2 candidates. The retained wrong-intermediate replay changes the final chosen
candidate, so this is a causal input-dependent A-to-B dependency rather than cosmetic
code order.

The sampler is independent of the hidden setting, supports 2–6 demonstrations and
four queries, teaches both selector mappings at the two-demo minimum, and includes a
30×30 / 20-candidate transfer. Every scene carries all four rotations of a chiral
shape, same-size distractors, and both output branches. A reusable protected-Racket
audit rejects nine executable rule shortcuts plus a Python-only topmost-candidate
shortcut without consulting query answers.

Retained evidence: `checks/7842d7d91514/qualification/qualification.json` and sibling
`execution.json`, `checks/7842d7d91514/audit-final.json`, and
`checks/7842d7d91514/sequential-witness/witness.json`. Fresh checks passed 75 task-local
tests, requalification reproduced the same qualification and execution bytes, and the
causal witness replayed under protected Racket. Status is reviewer `ready` only: exact
live integration, owner qualification/acceptance, and any training admission remain
owner steps.

