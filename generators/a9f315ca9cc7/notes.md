# Current notes: a9f315ca9cc7

## Selected canonical generator

The selected rule remains the canonical self-tiling authority:

```racket
(rule! (lambda (g) (self-tile g)))
```

For a lawful 3×3 input, each nonzero input cell selects an exact 3×3 copy of
the whole input in the corresponding output block; each zero cell selects a
blank block. The input is therefore both mask and copied template. `RULE_HASH`
remains `813a5290113c`; this review did not change the Racket authority or the
selected generator version (`2.1.0`).

The production grammar is intentionally bounded to 3×3, background 0, exactly
one foreground color, and 3–7 foreground cells with nontrivial row/column
patterns. Default samples alternate canonical D4-orbit masks and lawful unseen
masks. This preserves strong canonical support while ensuring every ordinary
three-demonstration consecutive window contains a generalized mask that refutes
public-mask memorization.

## 2026-10-22 repair decisions

1. **Strict external scalars.** The previous implementation delegated coercion
   to downstream helpers. It now rejects non-exact-integer `seed` and
   `sample_index`, rejects negative `sample_index`, validates `difficulty`, and
   strictly validates `scene_profile` and `fg_color` overrides before generation.
   This reverses the prior permissive behavior because defect lint showed that
   booleans, floats, strings, and negative indices were accepted.
2. **Canonical-shortcut declaration.** `CANONICAL_SHORTCUTS` now contains only
   `memorize_public_masks_else_pixel_scale`, the one declared rival that really
   fits all six labeled canonical pairs. Pixel scaling, repetition, one-copy,
   and inverted-mask rules remain in `LESSON_COMPETITORS`, where they are useful
   teaching rivals but are not falsely advertised as canonical-fitting.
3. **Frozen fixture preserved.** The packet's baseline
   `tests/test_generator_a9f315ca9cc7.py` remains byte-identical. New coverage
   lives in separate task-local test files.

The retained counterexample
`counterexamples/memorize-public-mask-shortcut.json` is a lawful generated
unseen mask. Canonical Racket execution matches the intended self-tile output
and differs from the memorizer's pixel-scale fallback. The reusable probe is
`workspace/probe_shortcuts.py`.

## Proposed parametric extension

`workspace/parametric/` contains a **proposed task-local prototype**, not a
selected rule change. It chooses `selector_role` once per episode:

- `foreground` (canonical default): copy at nonzero mask cells;
- `background`: copy at zero mask cells.

Both settings preserve the same reasoning structure: read the input as template
and mask, evaluate a cell role, and place full copies only in selected blocks.
Each retained episode has three demonstrations and one query; all labels were
executed with the complete setting-specific Racket program, and every demo/query
distinguishes the alternate setting. The production generator and catalog
approval path remain fixed to the foreground rule.

## Measured support and limits

- Final battery: all 12 stages green for generator SHA-256
  `2ec19009db044755a3e5ef171d9386bcb97aa446e5f0bb6ab59617775d1581a4`.
- Required lesson census: 300/300 production lessons and 1,200/1,200 query
  rotations identifiable against all declared rivals; 811 unique inputs.
- Finite rival checks do not establish identifiability against arbitrary
  programs.
- The proposed background-selector variant is evidenced only for two retained
  seeds and is not production integration or training approval.
- Foreground color is deliberately a nuisance variable; changing it alone is
  not a meaningful rule parameter.
## Current reviewer considerations

Source SHA-256: `2ec19009db044755a3e5ef171d9386bcb97aa446e5f0bb6ab59617775d1581a4`.

# Decisions for a9f315ca9cc7

## D1 — Preserve the canonical self-tiling authority

**Choice.** Keep the canonical Racket program
`(rule! (lambda (g) (self-tile g)))`, rule hash `813a5290113c`, the 3×3 input
contract, and generator version `2.1.0` unchanged.

**Rationale.** The baseline already produced lawful labels and maintained strong
canonical support. Its failures were contract/declaration defects, not evidence
that the underlying transformation was wrong. The final `rule_smoke` and
`authority_sync` stages bind the repaired Python generator to the unchanged
canonical authority.

**Alternatives considered.** Expanding production to arbitrary input sizes or
editing the Racket rule would have changed the family and invalidated existing
approval evidence. Neither was needed to repair the measured failures.

**Probe/evidence.** Baseline and final battery summaries under `checks/before/`
and `checks/after-final/`; exact default parametric program match in
`checks/parametric/selector-role-v2/report.json`.

**Failure modes/limits.** A fixed 3×3 core is intentionally narrow and does not
cover generalized N×N self-tiling. That is a documented family boundary, not a
claim of broad compositional coverage.

## D2 — Reject malformed external scalars instead of coercing them

**Prior choice.** The baseline delegated scalar handling to downstream draw
helpers, which accepted some booleans, floats, strings, and negative indices or
allowed malformed values to reach internal assertions.

**New choice.** Require exact integer `seed` and `sample_index`, require a
nonnegative sample index, restrict `difficulty` to the declared values, require
`scene_profile` to be an exact declared string, and require `fg_color` to be an
exact integer in `1..9`.

**Rationale.** Advertised controls should either be honored exactly or rejected
at the public boundary. Silent coercion makes source-bound reproduction
unreliable and produced the baseline defect-lint failure.

**Alternatives considered.** Coercing numeric-looking values with `int(...)` was
rejected because `True`, `1.0`, and `"1"` would then silently alias valid seeds or
colors. Catching only the original float/bool foreground-color case was rejected
because the same defect existed at the call-argument boundary.

**Probe/evidence.** Red/green task-test iterations are retained under
`checks/task-tests-red/`, `checks/task-tests-strict-call-red/`, and their green
successors. Final focused coverage is in
`tests/test_review_repairs_a9f315ca9cc7.py`; final defect lint is green.

**Failure modes/limits.** This is intentionally stricter than permissive Python
numeric conventions. Existing callers that relied on coercion must send the
contracted exact types.

## D3 — Separate canonical-fitting shortcuts from lesson competitors

**Prior choice.** `CANONICAL_SHORTCUTS` aliased all five semantic rivals, even
though four already disagreed with public canonical examples.

**New choice.** Declare only `memorize_public_masks_else_pixel_scale` as a
canonical shortcut. Keep `pixel_scale_3`, `repeat_template_everywhere`,
`single_copy_top_left`, and `copy_on_background_cells` as lesson competitors.

**Rationale.** A canonical shortcut declaration is a factual claim that the
rival fits every usable canonical pair. The reusable probe checks this directly:
the memorizer fits 6/6, while the other four do not. Keeping all five as lesson
competitors retains useful teaching pressure without corrupting canonical-fit
semantics.

**Alternatives considered.** Removing the four rivals entirely was rejected
because they remain plausible local hypotheses and are cheaply refuted by
ordinary lessons. Declaring no canonical shortcut was rejected because the
public-mask memorizer genuinely fits all six pairs.

**Probe/evidence.** `workspace/probe_shortcuts.py`,
`checks/question/generator-shortcuts-final/probe.json`, and
`tests/test_shortcut_probe_a9f315ca9cc7.py`.

**Failure modes/limits.** Declarations cover only named deterministic rivals.
Unknown programs may still fit the public examples.

## D4 — Retain the alternating canonical/generalized lesson schedule

**Choice.** Keep the six-position deterministic schedule that alternates
canonical-orbit and unseen generalized masks. Keep the production lesson shape
at three demonstrations and one query.

**Rationale.** This preserves canonical support while guaranteeing that every
ordinary three-demo consecutive window contains a generalized mask, which
refutes the strongest canonical memorization shortcut. The measured census found
300/300 production lessons and every one of 1,200 held-out query rotations
identifiable against all declared rivals.

**Alternatives considered.** Pure canonical sampling was rejected because the
memorizer would remain viable. Pure generalized sampling was rejected because it
would discard exact canonical-profile support. Random independent profile draws
were rejected because some three-demo windows could contain only public masks.

**Probe/evidence.** `checks/lesson-census.summary.json`, full
`checks/lesson-census.json`, and final semantic-gate evidence under
`checks/after-final/`.

**Failure modes/limits.** The census does not enumerate arbitrary schedule seeds
or arbitrary rivals. It holds out each materialized pair once but does not prove
semantic uniqueness.

## D5 — Prototype `selector_role`; do not integrate it into production

**Choice.** Build a task-local proposed parameter with values `foreground`
(canonical default) and `background`, chosen once per complete episode. Keep the
selected production generator and canonical authority fixed to foreground.

**Rationale.** This is a small, meaningful rule change that preserves the
original object roles and reasoning: the input remains both mask and copied
template, while only the selected mask-cell role changes. It is more substantive
than palette, size, position, or sampling changes.

**Alternatives considered.** Foreground color was rejected as a meaningful rule
parameter because it is only a nuisance/input variable. Arbitrary rotations,
scaling, or unrelated output transforms were rejected because they would compose
a new puzzle rather than expose a nearby family behavior. An N×N size parameter
was rejected for this packet because it changes the fixed core representation and
would need broader authority/runtime design.

**Probe/evidence.** `workspace/parametric/prototype.py`, `verify.py`, and
`README.md`; `checks/parametric/selector-role-v2/report.json`. The verifier uses
complete setting-specific Racket programs, checks all six canonical pairs for
the default, and retains one three-demo/one-query episode per setting with every
pair distinguishing the alternate setting.

**Failure modes/limits.** Only two retained seeds and the two declared settings
are evidenced. Hidden-rule inference depends on distinguishing demonstrations.
The prototype is not production integration, catalog approval, or training
admission.

## D6 — Preserve the frozen fixture and add separate tests

**Choice.** Restore and retain the packet-owned root fixture byte-for-byte; put
all new tests in separate files.

**Rationale.** `DUTIES.md` explicitly assigns migration ownership of the frozen
fixture to the library maintainer. Editing it to remove its legacy import warning
would invalidate the baseline contract.

**Alternatives considered.** Rewriting the frozen fixture was briefly explored
and then reversed before finalization. The final SHA-256 exactly matches the
assignment baseline.

**Probe/evidence.** Baseline and current fixture SHA-256 are both
`cd988c6c9bbbdd9abce166bad6aa9568688bd4cb56dc3eccfa1f301ad743b43e`;
`checks/task-tests/checks/task_tests.xml` records 18 passing tests.

**Failure modes/limits.** The legacy import still emits a warning in portable
execution. This does not hide a failed test, but future packet construction
should migrate it before freezing a new baseline.
