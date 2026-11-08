# Working notes: 56072bfdb820

## 2026-10-04 review — assignment `review-103a4bf5ca70847e`

The selected 4.1.0 baseline encoded the broad visual idea but not a reliable
training contract. It lacked a pinned `RULE_HASH`; advertised mostly dead or
singleton axes; silently clamped or ignored controls; sampled duplicate inputs
and dead difficulty bands; drifted from canonical palette/shape support; and
claimed that every valid pair completed to four diamonds even though the
canonical authority clips proposals at the 3×3 boundary. The baseline also had
no executable witnesses or rivals, and selected solution copies were textually
divergent from the canonical authority.

Version 5.0.0 keeps the canonical Racket behavior unchanged and rebuilds the
input side around its finite semantic domain:

- `pair_index` exactly selects one of all `C(9,2)=36` color-2 placements.
- `bad_mask` exactly selects no contamination, color 5, color 8, or both.
- `self_check` validates literal dividers, tiles, diamonds, symbol counts, and
  reconstructable controls rather than trusting generation metadata.
- The valid-pair census is 20 placements adding zero inferred diamonds, 12
  adding one, and 4 adding two. Exact overrides therefore cover 144 inputs and
  37 authority outputs (36 valid outputs plus one shared rejection output).
- The default sampler deliberately uses only nonidentity valid placements plus
  contamination examples. A 24×6 probe reaches its declared 17-output default
  codomain while preserving all three contamination branches.
- A seed- and index-mixed six-profile schedule supplies full completion, two
  clipped completions, both-bad contamination, and each single-bad color. Any
  five examples from every cyclic six-position block refute all declared
  competitors, regardless of which pair is held out as the query.
- `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`,
  `WITNESS_RIVALS`, `lesson_identifiable`, `rule_mirror`, and
  `observe_overrides` make the semantic contract executable.

The selected `racket_target.target_code` fields in the two active solution JSON
files were synchronized byte-for-byte to the canonical `program_solution`.
Their archival `raw_code` fields were retained, so the authority-sync report
correctly describes selected sources as synchronized and archival copies as
divergent. No rule behavior or canonical output changed.

### Verification snapshot

Final generator SHA-256:
`4a4299703663fd5333de2f1b1413393595619d6e88389e098496cad540500166`.

- Before battery: 5 blocking stages failed (`lint`, `defect_lint`, `dist_gate`,
  `override`, `authority_sync`).
- Final after battery: 12/12 stages green.
- Task-local regression suite: 35 tests, including all 36×4 exact overrides in
  every difficulty band, canonical replay, malformed inputs, output codomains,
  six-profile cyclic starts, every query rotation, and shared-gate seed cohorts.
- Racket-backed lesson census: 300/300 lessons materialized (100 per band),
  1,800 labelled pairs/query rotations, 0 ambiguous lessons, 0 hook/scoring
  errors, and 124 unique production inputs.
- Independent workspace probe: 576 banded exact-override cases, 144 unique
  inputs, 37 exact-domain outputs, 17 default-probe outputs, 20/12/4 clip census,
  and zero mismatches. All 144 inputs were also run through the canonical Racket
  authority in 64/64/16 chunks with zero mismatches.
- Post-repair visible-example solve: 5/5 demonstrations passed; prior rule
  exposure was declared `yes`, reference consultation during the episode `no`.

### Reusable tool

`workspace/reference_probe.py` independently enumerates the full exact override
domain and can emit apply-compatible 64/64/16 input chunks. It does not read
canonical answers or private labels. See `workspace/README.md`.

### Known limits

The default curriculum is intentionally finite and schedule-shaped. Passing the
three declared rivals over every tested rotation is strong evidence against
those shortcuts, not a proof of unique induction over all imaginable rules.
Exact overrides include valid identity/no-op placements for domain completeness,
but the production schedule excludes them because they weaken lesson value.
The catalog still reports the task as unapproved/unsafe for training; this review
does not change approval policy.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `04e256923e2d2d9b7acdec52ce7f78203b5d58c1b5a526830b8cb1caf8c3a488`.

# Decisions — review `review-8021fde006e6aeaa`

## D1 — Preserve the canonical production authority

**Decision.** Keep task `56072bfdb820` at rule hash `5eec51381abd` and canonical Racket program SHA-256 `4f4b849dba39af1d07282464f19d643f3fe587b105813a0d8fdc8ada2d92e9a0`.

**Rationale.** The baseline defect was in Python call validation, not transformation semantics. Canonical replay, rule smoke, and authority sync already bound lawful outputs to the selected Racket rule.

**Rejected alternative.** Folding the proposed wrap behavior into production would change labels and silently turn a validation repair into a new task family.

**Probe/failure mode.** The after battery reruns rule smoke and authority sync; the parametric evidence separately asserts that the `clip` program is byte-for-byte canonical. Any canonical-rule change would alter those hashes and fail the source-bound receipts.

## D2 — Reject invalid scalar types instead of coercing them

**Decision.** Require `type(seed) is int`; require `type(sample_index) is int and sample_index >= 0`; validate in both `schedule_profile` and `generate` before any generator context is built.

**Rationale.** The baseline accepted booleans because Python booleans are integer subclasses, accepted floats/strings through `int(seed)`, and accepted negative indices. These inputs contradict the strict generator API and made behavior depend on accidental coercion.

**Rejected alternatives.** `isinstance(value, int)` would still admit booleans. Coercing integral floats or numeric strings would preserve the defect. Validating only `schedule_profile` would leave `generate` dependent on call order and hidden context behavior.

**Probe/failure mode.** Eleven parametrized regressions cover boolean, float, string, and negative cases on both entry points. The failing-first and passing receipts are retained under `checks/tdd-red/` and `checks/tdd-green/`.

## D3 — Keep the repair minimal

**Decision.** Do not change the six-profile curriculum, pair scheduling, override axes, input grammar, Racket mirror, or metadata.

**Rationale.** The prior 5.0.0 source already had strong canonical coverage and lesson contracts. A narrow patch lowers acceptance risk and makes the before/after defect-lint delta attributable to one cause.

**Rejected alternative.** Refactoring schedule code while fixing validation would broaden the patch and make distribution or lesson changes difficult to distinguish from the defect repair.

**Probe/failure mode.** The full battery, profile floor, semantic gate, 64 task tests, and 300-lesson census all bind to final generator SHA `04e256923e2d2d9b7acdec52ce7f78203b5d58c1b5a526830b8cb1caf8c3a488`.

## D4 — Use boundary handling as the bounded parametric axis

**Decision.** Prototype `boundary_mode ∈ {clip, wrap}`, selected once per episode, with `clip` as the default exact canonical program.

**Rationale.** Boundary handling changes executed semantics while preserving the original task family, palette, and input grammar. It also corresponds to a named plausible rival already present in the canonical lesson contract, so it is easy to make the distinction explicit and testable.

**Rejected alternatives.** Palette changes and layout-only knobs would vary presentation rather than rule semantics. Per-pair parameter redraw would make the episode incoherent. Adding more than two boundary modes would increase ambiguity without evidence that the extra complexity improves training value.

**Probe/failure mode.** The prototype rejects unknown and non-string settings, materializes the exact program for each setting, and checks outputs through protected Racket execution plus an independent Python mirror.

## D5 — Emit only parameter-identifying episodes

**Decision.** Build each prototype episode from four boundary-sensitive placements: three demonstrations and one query. Require every demonstration to contradict the opposite setting and require the query predictions to differ.

**Rationale.** A parameterized task is harmful when both settings fit its visible support. Selecting only sensitive pairs makes the intended latent choice recoverable from every demonstration rather than merely from aggregate statistics.

**Rejected alternatives.** Random placement sampling can produce boundary-insensitive episodes. Allowing just one refuting demonstration makes the lesson fragile under dropped examples or query rotation. Reusing the production five-demo scheduler would add complexity without improving the bounded two-episode assessment.

**Probe/failure mode.** `checks/parametric/summary.json` records the per-demo refutation vector, opposite-setting Racket outputs, and query distinction for both complete episodes.

## D6 — Mask public challenges and retain private executable evidence

**Decision.** Public prototype payloads omit `boundary_mode`, Racket program text, and query outputs; private evidence retains instantiated programs, exact hashes, all labels, and rival outputs.

**Rationale.** This preserves a usable model-facing challenge while giving maintainers enough source-bound evidence to replay every label.

**Rejected alternative.** Publishing the chosen setting or program would reduce the task to execution rather than induction. Omitting private labels would make the prototype unverifiable.

**Probe/failure mode.** Focused tests validate masking recursively, and the evidence builder compares stored outputs with both exact Racket programs.

## D7 — Classify the parametric work as proposed, not approved

**Decision.** Keep all rule-changing code under `workspace/parametric/`; do not alter `generator.py` semantics, `RULE_HASH`, canonical rows, or catalog status.

**Rationale.** Two successful episodes establish feasibility, not production distribution quality. The evidence intentionally covers two settings and one shared witness rather than all seeds or every plausible rival.

**Failure mode/limit.** A future promotion would need a production sampler, broader per-band coverage, rotation checks, catalog review, and an explicit new authority/hash. This return makes no such approval claim.

## D8 — Leave adversarial audit targets unchanged

**Decision.** Report and reproduce the two drawn teaching ambiguities without patching `5faf9d5e3e6d` or `04a27ff51304`.

**Rationale.** The assignment defines these as findings-only audits. Editing them would exceed the allowed patch scope and obscure the exact source hashes on which the counterexamples were measured.

**Probe/failure mode.** Each audit stores the authoritative Racket outputs, rival outputs, agreement vector, validator results, and target source hash. The combined isolated checks retain their expected nonzero exits.

## D9 — Treat lesson-identifiability evidence as finite

**Decision.** Report both ordered-production and all-query-rotation results, but qualify them as checks against declared rivals on the sampled curriculum.

**Rationale.** Zero ambiguity over 300 lessons and 1,800 rotations is strong operational evidence, not a mathematical proof against every conceivable program.

**Rejected alternative.** Calling the task universally identifiable would overstate what a finite rival set and finite sampler establish.
