# Working notes: f1347e0836ec

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-03 review: dot-successor shortcut

The canonical pairs also fit `diagonal_orientation := (dot_color == background + 1)`. The version-2.0.0 four-profile schedule did not guarantee rejection: seed 18/start 1 yielded a four-demo survivor in all three bands.

Version 2.1.0 makes profile 1 an off-main-diagonal successor-dot case, declares the rival in all semantic mappings, and adds a witness plus regression tests. The ordinary background pool for that profile is `{3,5,7}` so the exact successor remains inside the ARC palette. Exact overrides remain authoritative and need not preserve the curriculum witness.

`workspace/lesson_probe.py` checks live declared rivals over every cyclic start. Final review evidence used seeds 0..99 per band and found zero survivors among 400 lessons per band. This is finite declared-rival evidence, not universal induction.

No Racket authority changed. Final generator SHA-256: `f60285f17ae2c2ecd7865939b076704b08a4f671f74fb0a6d701a2c4d803ecac`.
## Current reviewer considerations

Source SHA-256: `d11cf3efba53440d23c37196386a1ccfdb66e2fa3c3d20696bf7632c6632e76d`.

# Decisions for `f1347e0836ec`

## D1 — Repair the concrete strict-scalar defect narrowly

**Decision.** Validate `seed` and `sample_index` before deterministic-context construction. Accept only exact Python integers, reject booleans/floats/strings, and reject negative `sample_index`.

**Why.** The baseline battery’s only blocking stage was defect lint, with 33 coercive-call findings. Coercion aliases distinct API inputs and lets negative indices wrap the four-profile schedule. A pre-context guard removes that ambiguity without touching lawful generated data.

**Alternatives rejected.** Normalizing with `int(...)` preserves the defect. Accepting integer-valued floats keeps type-dependent replay behavior. Clamping negative indices hides caller errors and changes schedule meaning.

**Version decision.** Keep `VERSION="2.1.0"`: no valid call changes output, so changing the generation version would unnecessarily perturb all deterministic examples. Cost if this judgment is wrong: an integrator may prefer a patch-version bump for API-contract bookkeeping, but generator replay remains intentionally stable.

## D2 — Preserve canonical Racket authority and `RULE_HASH`

**Decision.** Do not change the canonical program, base solution, canonical labels, or `RULE_HASH=39c262fb60b4`.

**Why.** Canonical pairs, Python mirror, rule smoke, and selected Racket execution already agreed. The observed defect was argument validation, not transformation semantics. The after authority-set SHA-256 remains `89165aefa3732bcc7c01042b760757ed7b1038c18414f93aae2f73c9223ea3af`.

**Alternative rejected.** Editing the Racket rule merely to create a new version would add authority risk and no data-quality benefit.

## D3 — Build the rule parameter as an isolated prototype

**Decision.** Put the extension under `workspace/parametric/`; do not modify `generate`, canonical metadata, or production lesson hooks.

**Why.** The assignment asks for evidence about a rule-family extension but explicitly says proposed variants are not automatically approved. Isolation makes canonical acceptance independent of prototype acceptance and lets future agents replay the evidence without affecting training data.

**Alternative rejected.** Adding a public `trigger_diagonal` override to the selected generator would make a proposed rule look approved, enlarge the override contract, and mix two authorities in one production API.

## D4 — Vary the diagonal predicate, not cosmetic attributes

**Decision.** Define `trigger_diagonal ∈ {main, anti}`, with `main` canonical/default.

**Why.** This preserves the original object roles and output construction while changing the contextual condition a learner must infer. Both variants use the same unique dot, background, vertical line, and opposite boundary arms.

**Alternatives rejected.** Palette, dot color, grid size, and stroke color parameters are mostly cosmetic or distributional; they do not create a distinct rule hypothesis. Adding multiple simultaneous rule parameters was rejected because demonstrations would need substantially more coverage and attribution would be less clear.

## D5 — Choose the setting once per episode

**Decision.** Derive one setting from a strict integer episode seed, then hold it fixed for three demonstrations and one query.

**Why.** A rule parameter is meaningful only when examples jointly teach one latent rule. Per-example switching would turn the episode into label noise. Three demonstrations are sufficient for the retained main/anti schedule and keep the prototype compact.

**Implementation detail.** Lawful inputs come from the selected generator at sequential sample indices 0..3 with one derived input seed; labels come only from the selected materialized Racket program.

## D6 — Require demonstration-only identification and retain a negative control

**Decision.** Execute both declared Racket settings against demonstrations, require exactly the selected setting to survive, and omit the query from selection. Also retain a one-demonstration both-diagonals case where both settings survive.

**Why.** Using the query label would leak the answer into episode validation. The ambiguity control proves the checker does not simply echo private metadata.

**Alternative rejected.** Trusting profile names or a Python-only mirror would not establish that the exact exported Racket programs are distinguishable.

## D7 — Make public challenges solver-safe

**Decision.** Export only task ID, labeled demonstrations, and query input. Redact episode seed, parameters, parameter schema, Racket source, input-generation details, and query output.

**Why.** Retained private evidence must be rich enough to audit, while public challenges must not reveal the hidden rule or answer.

## D8 — Use both broad and schedule-exhaustive lesson evidence

**Decision.** Keep the production census at 100 lessons per band with all query rotations, and retain the task-local period-four cyclic-start probe.

**Why.** The shared census tests real production sampling and query permutation. The local probe covers all schedule starts that finite random starts might miss. Together they answer different failure modes.

**Limit.** Neither finite test proves uniqueness against undeclared hypotheses.

## D9 — Do not expand the grid domain

**Decision.** Leave production support at 5..16.

**Why.** The concrete blocker was scalar validation, and the requested creative work was a rule parameter. Enlarging size support would add distribution changes without evidence that current bounds damage training quality.

## D10 — Leave audit targets unchanged

**Decision.** Reproduce and report defects in `28119d6d0e10` and `0d9784b230ca`, but do not patch them.

**Why.** Audit duties require independence from selected-task edits. Exact reproducers and Racket receipts are retained under `checks/audit/`; proposed fixes are in `AUDIT.md` and shared-tool suggestions in `FEEDBACK_TO_CODEX.md`.

## D11 — Preserve interrupted evidence and rerun cleanly

**Decision.** Keep the interrupted portable-test/battery checkpoints and create completed final output directories rather than rewriting prior evidence.

**Why.** A foreground timeout is not a test failure and not a pass. Immutable separate evidence distinguishes interrupted controller execution from the later completed 37/37 and 12/12 runs.

## D12 — Report solve exposure literally

**Decision.** Record the blind task as no prior exposure, and the post-repair selected-task solve as prior exposure yes/reference consulted no.

**Why.** The selected rule had already been inspected during repair. Visible-example success is useful but must not be described as a blind independent solve.
