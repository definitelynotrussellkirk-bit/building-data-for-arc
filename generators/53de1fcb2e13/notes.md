# Working notes: 53de1fcb2e13

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `fd7b3e18205375617d0c7bf54cc35d155f2042286674ba15ff7ee1ab3f95a5b6`.

# DECISIONS — 53de1fcb2e13

## D1 — Preserve the selected authority; repair the sampler

**Choice.** Keep the Racket rule unchanged and bind the generator to
`RULE_HASH = "9c8ca59a982a"`.

**Rationale.** The selected rule solves all three canonical input/output pairs,
the canonical `program_solution` and bank `target_code` are synchronized, and two
distinct retained Racket source texts have execution parity on the canonical task.
The observed failures came from the generator contract and distribution, not from
the selected authority.

**Rejected alternatives.** Rewriting the Racket rule merely to remove its linter's
`dummy-let-binding` would change authority text without changing semantics. Using
the archival raw program as the selected rule would also create unnecessary
source churn.

**Failure mode / limit.** Canonical-pair parity cannot establish equivalence over
all lawful generated inputs. The independent probe therefore also compared 48
generated grids plus the 3 canonical inputs against real Racket.

## D2 — Five exact, pixel-observable axes

**Choice.** Advertise only `panel_n`, `transform`, `a_cells`, `c_cells`, and
`palette_id`. Every Cartesian combination is supported; unknown keys and invalid
types/ranges raise.

**Rationale.** Each value can be recovered exactly from the grid. This eliminates
baseline axes that were constants, dead aliases, or descriptions rather than
controllable variables. It also lets the shared override gate exhaustively verify
the contract.

**Rejected alternatives.** Keeping `grid_h`, `grid_w`, `palette_size`,
`position_bias`, `n_distinct_colors`, `density`, or `texture` would preserve an
API that did not correspond to independent generation choices. Declaring many
incompatibilities would hide the same inconsistency instead of fixing it.

**Probe.** `observe_overrides` and the independent `observed` implementation are
compared on generated grids; the final shared matrix tested 30,420 accepted draws
across 338 cases and three bands.

## D3 — Panel sizes 4–6 with canonical support in every band

**Choice.** Generate square panels of size 4, 5, or 6. Each difficulty schedule
contains size 4, the canonical scale.

**Rationale.** Size 4 anchors the exact canonical profile. Sizes 5–6 add spatial
variation without producing very large, sparse canvases that would change the
visual regime. Difficulty alters frequencies, not legal support.

**Rejected alternatives.** The baseline hard band never emitted a canonical-size
input. Fixing every panel at 4 would remove useful scale variation. Expanding much
beyond 6 would require revisiting density/count ranges and canonical morphology.

**Failure mode / limit.** The rule itself is not inherently limited to 4–6. This
is a conservative training manifold, not a semantic maximum.

## D4 — All eight D4 transforms in canonical Racket order

**Choice.** Use codes `0..7` as `id`, clockwise 90°, 180°, counter-clockwise 90°,
left/right flip, up/down flip, main-diagonal transpose, anti-diagonal transpose.

**Rationale.** This is the finite domain explicitly searched by the selected rule.
Fully D4-asymmetric A ensures even identity has exactly one matching code; fully
asymmetric C makes every nonidentity transform observable.

**Rejected alternatives.** The first repair used only seven nonidentity transforms.
A self-review rejected that restriction because identity is lawful and uniquely
inferable for asymmetric A. The baseline's 0–5 numbering was also rejected because
it did not match authority order and omitted branches.

**Probe.** `test_every_transform_uses_canonical_order` covers all eight codes. The
identity test was first observed failing in
`checks/tdd-red-identity/pytest-exact.log` before implementation.

## D5 — Deterministic eight-step teaching schedule

**Choice.** Default transforms follow `(1, 0, 4, 2, 6, 3, 5, 7)` by sample index.

**Rationale.** The canonical examples show only transforms `{1,4,6}`. No cyclic
window of three consecutive schedule values lies entirely in that set, so every
three-demo lesson refutes a solver that memorizes only canonical transform types.
Exact overrides remain available for every code.

**Rejected alternatives.** Independent random transform draws have a nonzero
chance of producing entire lessons that teach only the canonical subset. Forcing
all demos to noncanonical transforms would underrepresent canonical cases and
identity.

**Failure mode / limit.** The schedule is deterministic and tied to sample index.
This is intentional lesson coverage, but future samplers that assemble examples
nonconsecutively must rerun cyclic-window and production lesson tests.

## D6 — Asymmetric shapes, 3–8 cells, and independent query orbit

**Choice.** Sample A and C with 3–8 cells, require eight distinct D4 images for
each, and reject C if it belongs to A's D4 orbit.

**Rationale.** A must identify one transform exactly. C should make nonidentity
transforms visible and should not permit a shortcut that copies/transforms A
instead of reading C. Counts 3–8 provide sparse through moderately dense shapes
at every panel size while remaining easy to place.

**Rejected alternatives.** Symmetric A makes A→B ambiguous. Symmetric C can make
a nonidentity query appear unchanged. Allowing C in A's orbit introduces a strong
object-copy correlation unrelated to the rule.

**Failure mode / limit.** The canonical rule permits symmetric C and C in A's
orbit when output remains well defined. Excluding them narrows the training
manifold. The rejection sampler is bounded at 4,096 attempts and raises loudly
rather than silently falling back to a symmetric shape.

## D7 — Five source/target palette pairs

**Choice.** Use `(2,4)`, `(3,5)`, `(6,7)`, `(1,6)`, and `(5,2)`; reserve 8 for
separators and 0 for background.

**Rationale.** The first three reproduce canonical color roles. The extra two
break the shortcut that a fixed source color predicts a fixed query color, while
remaining within ARC colors and keeping source and target distinct.

**Rejected alternatives.** Arbitrary independent colors could accidentally use 8
inside panels or make source and target equal. Only canonical palettes would leave
color-role memorization unchallenged.

**Failure mode / limit.** This is still a finite palette set. A learner could in
principle memorize all five pairs; the structural transform remains independently
varied, and palette has no effect on transform scheduling.

## D8 — Strong validator and exact rule mirror

**Choice.** Centralize parsing in `_analyze_grid`; use it for `self_check`, strict
canonical validation, override observation, and the Python rule mirror.

**Rationale.** One structural interpretation avoids disagreement between hooks.
The validator checks dimensions, exact separator columns, color range and roles,
palette, cell counts, asymmetry, and a unique A→B transform.

**Rejected alternatives.** The baseline divider-only check accepted blank grids,
singletons, solid blocks, and missing panels. Treating those as lawful degenerates
would make the Racket rule ambiguous or inapplicable.

**Failure mode / limit.** Four of fifteen generic duplicate-first-row mutations
remained lawful after mutation, so the generic mutation score is 56/60 rather
than 60/60. Task-specific mutation fixtures are all rejected.

## D9 — One explicit canonical-fitting rival

**Choice.** Declare `canonical_transform_subset_only`: it exactly handles
transforms `{1,4,6}` and falls back to clockwise rotation otherwise. Register it
as a semantic rival, canonical shortcut, and lesson competitor.

**Rationale.** It fits every canonical pair, changes outputs on lawful generated
inputs, and represents the most immediate data-value risk: training only the
three observed transform branches.

**Rejected alternatives.** A rival that ignores A/B entirely is too easy and does
not fit all canonical pairs. Enumerating every conceivable wrong rule is neither
finite nor meaningful.

**Failure mode / limit.** Passing one declared rival proves only that one shortcut
is refuted. It does not establish universal identifiability. Cross-axis correlation
rivals are proposed as a shared automated gate in `QUESTION_ANSWER.md`.

## D10 — Independent reusable probe

**Choice.** Add `workspace/reference_probe.py`, separate from generator internals.

**Rationale.** Future reviewers can decode axes, verify canonical pairs, measure
per-band support/determinism, test the declared shortcut, and batch generated
inputs through real Racket without trusting the production mirror.

**Usage.** From packet root:

```bash
python3 run_with_racket.py python3 generators/53de1fcb2e13/workspace/reference_probe.py \
  --count 140 --out ../checks/reference-probe.json --racket
```

**Failure mode / limit.** The probe samples finite seeded draws and 51 Racket
inputs. It is independent in implementation, but it encodes the same understood
rule and therefore is not a proof against a jointly misunderstood specification.
