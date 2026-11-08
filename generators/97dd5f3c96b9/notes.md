# Review notes: 97dd5f3c96b9

## Lead and baseline

The accepted audit `review-ac4e298e7e8909d2:v0001` was used only as a lead. It
reported that baseline version `1.1.1` could emit overlapping aligned-pair
segments. The immutable baseline source hash was
`e3e1084832bdd36d6db99b7bc21dc276027fe1dbcaad3e9048cc21000e602dad`.
A current self-contained replay of seed `0`, sample index `1`, difficulty
`easy` is retained at `checks/repro/97dd5f3c96b9/case.json`: the selected rule
paints color 7 over an original color-4 marker at `(3,5)`, while a natural
marker-preserving rival restores that endpoint.

The before battery measured 7 green, 2 advisory, and 3 failed stages. Besides
the overlap lead, it found no pinned `RULE_HASH`, a permissive validator that
accepted blank/degenerate scenes, nine advertised controls that were mostly
aliases or not observable from pixels, weak canonical-profile support, and no
executable semantic teaching contract.

## Root cause

The old sampler checked only that two endpoint cells were empty. It did not
reserve the inclusive segment between endpoints, so two independently sampled
pairs could cross or overlap. The Racket authority paints colors in its own
order, making those generated labels paint-order-dependent even though every
canonical example preserves all original markers.

The old source also tried to expose broad combinatorial variety through
`grid_h`, `grid_w`, `n_pairs`, palette aliases, and deliberately degenerate
textures. Most of those controls were not exact/observable, and the
self-checker's permissiveness made the declared domain much wider than the
canonical task grammar.

## Selected repair

Version `2.0.0` keeps the Racket authority unchanged and narrows the sampler to
an unmistakable lawful curriculum:

- exactly three distinct nonzero colors, matching all three canonical pairs;
- canonical profiles `8×10`, `9×11`, and `8×12`;
- mixed horizontal/vertical orientations in every grid;
- at least one interior zero between each pair's markers;
- pairwise-disjoint inclusive spans selected constructively by backtracking;
- one honest, pixel-observable exact override, `scene_profile`;
- strict parsing shared by `self_check`, `strict_canonical_like`, the audit
  mirror, witnesses, and competitors;
- one-demo semantic witnesses against identity, horizontal-only,
  vertical-only, and first-pair-only rivals.

Difficulty changes candidate ordering only: easy prefers shorter spans, hard
prefers longer spans, and medium/default retain shuffled order. It does not
change the grammar. Colors are still drawn without replacement from 1–9.

## Test-driven evidence

A task-local regression suite was written before the repair. Against the old
source it produced 17 expected failures (`checks/task-tests-red.txt`), including
the retained overlap fixture, missing authority metadata, canonical mismatch,
fake override behavior, and absent semantic contracts. The first repaired
source passed 19 tests, after which the shared defect lint exposed
`PYTHONHASHSEED`-dependent replay caused by iterating a set while consuming a
shared RNG. A subprocess regression failed first (`checks/hashseed-red.txt`);
using a fixed orientation order then made the final suite pass 20/20.

Final source hashes:

- `generator.py`: `8626cabe946ae140676985a8fae154be1dff2e910cc89b8ebce7b62ed6d9be31`
- `tests/test_generator.py`: `5a551001247e6082cc2905c020b6b1c820ff824e52c4ad95350d788cba75a2b1`

The final fresh battery is all green (12/12) at
`checks/after/checks/97dd5f3c96b9_after_battery_summary.json`. The explicit
portable task-test stage passes 20/20 at `checks/task-tests-final/result.json`.
The source-bound lesson census materialized 100 lessons per band: 300/300
lessons, 600 labelled pairs, and 600 query rotations, with 0 production or
rotation ambiguities, 0 materialization errors, 0 hook warnings, and 0 scoring
errors (`checks/lesson-census.json`).

## Limits

The selected manifold is intentionally narrower than version `1.1.1`: it no
longer trains one- or two-pair scenes, arbitrary canvas sizes, adjacent pairs,
diagonal non-pairs, or overlapping spans. Those cases either do not occur in
the canonical task or create weak/ambiguous lessons, but a future expansion
would need new witnesses and source-bound tests rather than silently widening
`self_check`.

The census is finite and tests only the declared rivals. It does not prove
universal identifiability, enumerate every possible scene, or exclude an
undeclared shortcut. The selected authority is synchronized and unchanged;
the battery's archival-bank divergence is pre-existing and nonblocking.
## Current reviewer considerations

Source SHA-256: `8626cabe946ae140676985a8fae154be1dff2e910cc89b8ebce7b62ed6d9be31`.

# Decision ledger — 97dd5f3c96b9

Finding IDs refer to `REVIEW.md`.

## D1 / R1 — Keep the selected Racket authority unchanged

- **Original rationale:** the authority exactly matches all three canonical
  pairs and expresses the written task: connect each color's two aligned cells.
- **Decision:** pin `RULE_HASH = "8d1d1f690046"`; repair only the generated input
  manifold and its executable contract.
- **Alternatives considered:** change paint order; restore all markers after
  painting; define crossings as illegal in Racket. The first two would silently
  change selected semantics, and the third is unnecessary when the sampler can
  enforce the intended canonical manifold.
- **Probe:** canonical exactness test plus final rule-smoke/authority-sync stages.
- **Failure mode/limit:** the unchanged rule still has paint-order semantics for
  arbitrary overlapping inputs; those inputs are now outside the declared
  generator domain rather than redefined.

## D2 / R1 — Reserve complete spans, not only endpoints

- **Original rationale:** baseline sampled each pair independently and checked
  only endpoint emptiness, presumably to maximize placement success and variety.
- **Decision:** enumerate all legal gapped spans and use backtracking to choose
  three whose inclusive cell sets are pairwise disjoint.
- **Alternatives considered:** rejection sampling after drawing endpoints; allow
  perpendicular crossings; sample then repair collisions. Rejection sampling
  has unbounded/seed-sensitive retry behavior, crossings retain paint-order
  ambiguity, and repair can distort requested controls.
- **Probe:** historical overlap fixture, 48 draws per difficulty setting, marker
  preservation assertions, and strict mutation fixtures.
- **Failure mode/limit:** disjointness removes crossing examples. This is a
  deliberate curriculum restriction, not a claim that the Racket program cannot
  execute crossings.

## D3 / R2 — Exactly three pairs

- **Original rationale:** baseline varied `n_pairs` from 2–3 (and advertised
  1–4) to increase surface diversity.
- **Decision:** use exactly three colors/pairs because every canonical pair uses
  three and one demonstration can then refute “first pair only” while carrying
  both orientations.
- **Alternatives considered:** retain 2–3; expose exact 1–4; curriculum-order
  sparse scenes before dense scenes. Two-pair scenes can still teach the rule,
  but increase lesson scheduling/rival burden without canonical support; one-pair
  scenes are especially weak.
- **Probe:** all canonical pairs accepted; `multiple_pairs` witness and
  `first_pair_only` rival refuted in every sampled lesson.
- **Failure mode/limit:** no evidence is produced for induction from one- or
  two-pair scenes.

## D4 / R2 — Canonical canvas profiles only

- **Original rationale:** baseline varied heights 7–10 and widths 9–12, likely to
  encourage size generalization.
- **Decision:** exact profiles `8×10`, `9×11`, and `8×12`, one per canonical pair,
  represented by the sole override `scene_profile`.
- **Alternatives considered:** independent `grid_h`/`grid_w`; broad rectangular
  ranges; a free `(h,w)` tuple. Independent axes create combinations absent from
  canonicals and made exact-control coverage harder; a profile is directly
  observable and guarantees the profile floor.
- **Probe:** all profile overrides in every difficulty band, canonical acceptance,
  and battery profile-floor/override stages.
- **Failure mode/limit:** size extrapolation outside the three profiles is not
  trained or claimed.

## D5 / R2 — Mixed orientations in every scene

- **Original rationale:** baseline chose each pair orientation independently;
  all-horizontal or all-vertical examples were possible.
- **Decision:** choose either H,H,V or H,V,V so one demonstration always contains
  both orientations.
- **Alternatives considered:** leave orientation random and rely on multi-demo
  schedules; advertise an orientation-mix axis. The production contract uses one
  demo, so random homogeneous scenes would allow an orientation-only shortcut;
  an extra axis offered no needed curriculum value.
- **Probe:** `mixed_orientations` witness; horizontal-only and vertical-only
  competitors; 300-lesson census and every query rotation.
- **Failure mode/limit:** the generator does not provide homogeneous scenes for
  evaluating whether a learner can transfer from mixed to single-orientation
  cases.

## D6 / R2 — Require a real gap

- **Original rationale:** baseline endpoint sampling already tended to use
  separation, but also exposed an `all_adjacent` degenerate texture that produced
  little or no visible transformation.
- **Decision:** every span has length at least 3, giving at least one interior
  cell to paint.
- **Alternatives considered:** permit adjacency as a lawful edge case; keep it as
  a negative texture. With one demo, an all-adjacent scene supports identity and
  contributes no positive evidence for line filling.
- **Probe:** `gapped_pairs` witness, identity rival, adjacency mutation.
- **Failure mode/limit:** adjacency behavior remains executable under the general
  rule but is intentionally absent from training data.

## D7 / R2 — One honest exact axis; remove aliases and degenerates

- **Original rationale:** version `1.1.1` advertised nine controls to describe
  dimensions, palette, count, density, position, and texture. Several were
  metadata aliases, ignored by generation, or deliberate invalid/weak cases.
- **Decision:** expose only `scene_profile`; reject unknown axes and invalid
  values/types. Palette remains stochastic because color identity is not a
  semantic role in this task.
- **Alternatives considered:** implement every old axis exactly; preserve aliases
  for compatibility. That would retain unsupported combinations and make the
  public contract much larger than the evidence warrants.
- **Probe:** `observe_overrides`, exact override tests in every band, and final
  override gate.
- **Failure mode/limit:** callers using old private aliases receive an explicit
  error and must migrate.

## D8 — Difficulty changes span length preference, not grammar

- **Original rationale:** baseline easy/medium/hard changed dimensions and pair
  counts, entangling difficulty with distinct domains.
- **Decision:** all bands share one strict grammar; easy sorts shuffled candidates
  shortest-first, hard longest-first, medium/default retain shuffled order.
- **Alternatives considered:** no difficulty effect; increase pair count or grid
  size by band. A length preference gives a visible complexity gradient without
  undermining profile/semantic coverage.
- **Probe:** 48 lawful draws in each of `None`, easy, medium, hard and the
  100-lessons-per-band census.
- **Failure mode/limit:** candidate ordering is a soft distributional bias, not a
  guaranteed exact span-length range.

## D9 / R3 — Fixed orientation iteration order

- **Original rationale:** constructing candidate lists from a set looked concise;
  order appeared semantically irrelevant.
- **Decision:** build horizontal then vertical candidate lists in a fixed tuple
  order because both shuffles consume one shared deterministic RNG stream.
- **Alternatives considered:** independent per-orientation RNG streams; sort set
  values. Independent streams would change established replay more broadly;
  explicit order is the smallest root-cause fix.
- **Probe:** subprocess generation under `PYTHONHASHSEED=1,2,3`, first observed
  failing in `checks/hashseed-red.txt`, now part of the 20-test suite.
- **Failure mode/limit:** future code must avoid all unordered iteration that
  consumes shared RNG, not only this specific dictionary construction.

## D10 — One demonstration, one query, rotations required

- **Original rationale:** unknown in the imported generator; there was no prior
  executable lesson contract.
- **Decision:** `EXAMPLES_NEEDED = 1`, with each scene constructed to refute
  identity, horizontal-only, vertical-only, and first-pair-only rivals. Production
  uses one demo and one query; every materialized pair is also tested as query.
- **Alternatives considered:** require 2–3 demos; ordered curriculum with a fixed
  witness position. More demos would be safe but spend training context on
  redundant evidence because every single generated scene already carries all
  declared witnesses.
- **Probe:** task-local one-demo test, semantic gate, and 300-lesson/600-rotation
  census.
- **Failure mode/limit:** declared rivals are finite; an undeclared shortcut can
  still survive, so these results are not a proof of unique induction.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-bc2e64a9e7d5c628:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `8626cabe946ae140676985a8fae154be1dff2e910cc89b8ebce7b62ed6d9be31`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/97dd5f3c96b9/generator.py, unchanged SHA256 8626cabe946ae140676985a8fae154be1dff2e910cc89b8ebce7b62ed6d9be31. Bounded clean audit:20 portable tests,12 strict lessons with required rotations and0 ambiguity,600 strict samples. Exactly3 disjoint gapped aligned pairs with mixed orientations and canonical canvas profiles only; no certification for overlaps/adjacency, no approval update or owner rerun. Quoted basenames mean these target-local paths: `checks/audit/97dd5f3c96b9-semantic-current-command.exit` `checks/audit/97dd5f3c96b9-semantic-current-command.log` `checks/audit/97dd5f3c96b9-semantic-current/RUNTIME_MANIFEST.json` `checks/audit/97dd5f3c96b9-semantic-current/checks/97dd5f3c96b9_audit_battery_summary.json` `checks/audit/97dd5f3c96b9-semantic-current/checks/97dd5f3c96b9_audit_commands.jsonl` `checks/audit/97dd5f3c96b9-semantic-current/checks/97dd5f3c96b9_audit_semantic_gate.json` `checks/audit/97dd5f3c96b9-semantic-current/checks/97dd5f3c96b9_audit_semantic_gate.log` `checks/audit/97dd5f3c96b9-semantic-current/checks/97dd5f3c96b9_audit_semantic_gate.ok` `checks/audit/97dd5f3c96b9-semantic-current/checks/97dd5f3c96b9_audit_semantic_gate.receipt` `checks/audit/97dd5f3c96b9-semantic-current/progress.log` `checks/audit/97dd5f3c96b9-semantic-current/result.json` `checks/audit/97dd5f3c96b9-task-tests-current-command.exit` `checks/audit/97dd5f3c96b9-task-tests-current-command.log` `checks/audit/97dd5f3c96b9-task-tests-current/RUNTIME_MANIFEST.json` `checks/audit/97dd5f3c96b9-task-tests-current/checks/task_tests.xml` `checks/audit/97dd5f3c96b9-task-tests-current/progress.log` `checks/audit/97dd5f3c96b9-task-tests-current/result.json` `checks/audit/97dd5f3c96b9/verification-summary.json`

### Assessment or prior finding

## 97dd5f3c96b9

**No issue found in the assigned current source.** The audited generator remains SHA-256 `8626cabe946ae140676985a8fae154be1dff2e910cc89b8ebce7b62ed6d9be31`, version `2.0.0`, with `RULE_HASH = 8d1d1f690046`; no target file was changed.

I inspected the current generator, tests, span construction, validator, exact controls, declared rivals, and lesson contract. I specifically checked for recurrence of the historical overlapping-span marker overwrite, homogeneous-orientation lessons, adjacent identity-like pairs, dead controls, and one-demonstration shortcuts.

Fresh measurements:

- portable task tests: 20/20 passed;
- strict semantic gate with required query rotations: 12/12 lessons identifiable, 0 unidentifiable, and 0 ambiguous rotations;
- 600 strict-canonical samples were measured by the semantic gate without the inspected shortcut classes surviving.

Evidence:

- `checks/audit/97dd5f3c96b9/verification-summary.json` — compact verdict and hashes;
- `checks/audit/97dd5f3c96b9-task-tests-current/result.json` — test receipt;
- `checks/audit/97dd5f3c96b9-semantic-current/checks/97dd5f3c96b9_audit_semantic_gate.json` — required-rotation semantic report.

The sampled manifold is intentionally narrow: exactly three disjoint, gapped, aligned pairs with mixed orientations and canonical canvas profiles. This clean audit does not certify overlapping or adjacent scenes that the sampler explicitly excludes.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

## Proposed connector-color parametric extension (review-b74787e066759306)

The current production generator was rechecked and left unchanged: version
`2.0.0`, source SHA-256
`8626cabe946ae140676985a8fae154be1dff2e910cc89b8ebce7b62ed6d9be31`, and
canonical `RULE_HASH = 8d1d1f690046` remain authoritative.

A separate task-local prototype under `workspace/parametric/` varies one
hidden episode setting while preserving the same object roles and spatial
reasoning. `pair_color` returns the canonical Racket source byte-for-byte;
`fixed_8` and `fixed_9` preserve each marker endpoint and recolor only the
interior connector cells. Inputs are generated independently of the setting,
all settings are total over the selected generator's strict grammar, and demo
and query counts are independently supported from 1 through 16.

Focused prototype tests pass 37/37, and the complete staged task suite passes
57/57. The shared promotion worker checked all three settings with two
demonstrations and four queries, found the selected setting as the sole finite
demonstration-only survivor in every episode, and performed 30 protected Racket
evaluations. A second boundary qualification covered 1 demo/16 queries, 16/1,
and 16/16 with 132 protected Racket evaluations and 17, 17, and 32 distinct
inputs respectively. Retained evidence at
`checks/parametric/connector-color-v1/manifest.json` contains three complete
episodes (one per setting), four distinct queries each, visible-byte-derived
public names, exact rule sources, protected-Racket labels, query answers kept
private, and all-rival query disagreement checks.

Prototype source hashes:

- `workspace/parametric/prototype.py`: `78ac70ef2d37f54c345b81bcb8ca52eca8b5b546ddce83c842637a932e95592a`
- `workspace/parametric/adapter.py`: `068a7b330d0e2283245baace4232749174bb8d549c45108ae43db45ea9908647`
- `workspace/parametric/promotion.json`: `608c23b6d52fe6b4189fe3750f94fbcc5d82c49e65aa1cfcddbec97f6bdef7ea`

This is proposed authoring evidence only. It does not update production
approval, the canonical rule, accepted parametric catalog state, allocation, or
training admission. Its identifiability claim is finite and limited to the three
declared settings and retained seeds.
