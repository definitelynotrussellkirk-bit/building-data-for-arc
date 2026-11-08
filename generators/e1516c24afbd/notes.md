# Working notes: e1516c24afbd

## 2026-10-03 review-cb7732e175f05251

The v1.4.1 generator preserved the rule but did not reliably teach it. Its
validator checked only even height and absence of input color 2; destructive
mutation testing rejected 0/75 mutations. Degenerate negative fixtures were
advertised as ordinary texture values and all passed validation. The declared
`both_zero_target` axis was not probeable, `RULE_HASH` was absent, and independent
panel filling could omit one-sided or both-nonzero occupancy states.

Version 2.0.0 samples the four joint occupancy states directly. Every normal
example contains `00`, `10`, `01`, and `11`, uses one distinct foreground color
per panel, and exposes exact controls for dimensions, colors, positive count,
and layout. The first three lexicographic non-`00` states encode layout as a
reversible signature so override observability does not depend on heuristic
shape recognition. Negative fixtures remain callable for tests but are outside
the lawful teaching grammar.

The task now declares executable witnesses, seven Boolean truth-table rivals,
and a lesson-level survivorship check. Three-demo cyclic windows and a
300-lesson source-bound census found no declared ambiguity. The selected base
`target_code` was synchronized textually to canonical while preserving archival
`raw_code`; canonical behavior and rule hash were unchanged.

Limits: finite rivals are not a proof of unique induction; layout signatures are
an intentional metadata-bearing microstructure; default examples are stronger
than strictly necessary because each one contains the full truth table.
## Current reviewer considerations

Source SHA-256: `4164fbc5acf74fdada76f6e4f1c2ebb26458bb9ce7a5e5b273e12e0530a3f121`.

# Decisions for `e1516c24afbd`

## R1 — Fail closed on public call scalars and numeric overrides

**Choice.** Require literal Python `int` values for `seed`, `sample_index`,
`half_h`, `grid_w`, `both_zero_count`, `top_color`, and `bot_color`; reject a
negative sample index before schedule arithmetic.  Validate difficulty before
RNG construction and use strict draw helpers for exact integer/color controls.

**Rationale.** The baseline accepted coercible aliases and produced 138
strict-scalar warnings.  A boolean or numeric string silently changes or aliases
curriculum scheduling instead of surfacing bad caller data.  Failing at the API
boundary makes the contract deterministic and auditable.

**Alternatives rejected.** Normalizing with `int()` was rejected because it
conflates `True`, `1.0`, `"1"`, and `1`, and admits negative schedule positions.
Relying only on downstream range checks was rejected because `bool` is an `int`
subclass and coercive draw helpers accept values outside the intended type
contract.

**Probes.** `tests/test_strict_scalars.py`; red evidence
`checks/tdd-red-strict-scalars-stage/`; green evidence
`checks/tdd-green-strict-scalars/`; baseline/final defect logs under
`checks/before/` and `checks/after/`.

**Failure modes and limits.** This is intentionally stricter than legacy
coercion.  A caller depending on numeric strings or integral floats must convert
explicitly before calling.  Shared runtime enforcement is still absent, so
other generators may retain the same defect (see feedback F1 and audit A2).

## R2 — Make the canonical-profile-only shortcut executable and teach against it

**Choice.** Retain 3×3 half-panel anchors on fully-default even slots, force
fully-default odd slots off the 3×3 profile, and explicitly test the named
canonical-profile-only rival in `lesson_identifiable`.

**Rationale.** Every canonical pair is exactly 6×3, so a rule conditioned on
that full shape fits all canonical labels.  The default generator already could
emit larger lawful inputs, but the first new test proved that some three-demo
windows still used only canonical-profile examples.  Alternating anchor/witness
slots preserves canonical support and guarantees a shape counterexample in
every three-pair cyclic window.

**Alternatives rejected.** Removing all 3×3 examples would defeat the profile
floor and weaken canonical anchoring.  Leaving dimensions purely random would
make witness presence probabilistic.  Adding the rival to `CANONICAL_SHORTCUTS`
was not used because the inherited frozen fixture pins that mapping to `{}`;
the same executable check is instead applied directly in the lesson hook.

**Probes.** Exact counterexample
`generators/e1516c24afbd/counterexamples/canonical-profile-only.json`; focused
red/intermediate/final evidence under
`checks/tdd-red-canonical-profile-shortcut/`,
`checks/tdd-green-canonical-profile-shortcut/`, and
`checks/tdd-green-canonical-profile-shortcut-v2/`; reusable source-bound probe
`workspace/shortcut_probe.py` with `checks/shortcut/report.json`.

**Failure modes and limits.** Parity is a visible deterministic schedule
component.  The probe covers one strong shape-gated rival and finite starts;
other undeclared spatial or metadata shortcuts may exist.  Explicit dimension
overrides can still request 3×3 on any slot, so a downstream assembler that
uses only explicit canonical overrides must supply its own teaching witness.

## P1 — Keep the parametric family separate from canonical production

**Choice.** Prototype the Cartesian family
`target_state ∈ {00,11}` × `output_color ∈ {2,3}`, selected once per episode.
Keep the canonical default `00`/2 byte-identical to the selected authority and
store all code under `workspace/parametric/`.

**Rationale.** Both parameters preserve the original aligned two-panel Boolean
reasoning pattern and are small enough to distinguish explicitly.  Inputs with
all four occupancy states let every labeled pair identify the selected setting.
The task-local separation avoids silently changing the production generator or
approval state.

**Alternatives rejected.** Parameters that choose `10` or `01` as the target
were omitted to keep the family small and symmetric.  Varying panel composition,
geometry, or output position would change the reasoning structure rather than
parameterize it.  Wiring the family into production was rejected because the
assignment asks for assessment/prototype evidence, not selection approval.

**Probes.** `workspace/parametric/verify.py`, materialized manifest, focused
`tests/test_parametric_variant.py`, and
`checks/parametric-final/report.json`.

**Failure modes and limits.** Complete-state examples are deliberately strong
and may reduce difficulty.  Only four settings were exhaustively checked.  The
prototype has no production admission or long-run curriculum decision.

## C1 — Preserve canonical authority and frozen-fixture compatibility

**Choice.** Do not modify the Racket authority, `RULE_HASH`, inherited root test,
or catalog approval.  Leave `VERSION="2.0.0"` and the frozen rival mappings as
pinned, and identify the repaired artifact by final source SHA-256.

**Rationale.** Racket labels and canonical behavior were already correct.  The
repair concerns caller validation and lesson construction.  Editing a frozen
fixture to bless changed declarations/version is explicitly prohibited.

**Alternatives rejected.** A Racket rewrite would add risk without changing the
rule.  Bumping the version while knowingly breaking the inherited portable
fixture would turn a passing repair into a blocked return.  Omitting the
compatibility issue from the report would make intake ambiguous.

**Probes.** Rule smoke and authority sync in the final 12-stage battery;
canonical replay in the parametric verifier; source and rule hashes in all
retained reports.

**Failure modes and limits.** A future maintainer should decide whether this
source change warrants a formal version migration and whether semantic rival
registries should be extensible without exact-equality fixture churn (feedback
F2).

## E1 — Retain reproducible evidence and tools, not just conclusions

**Choice.** Keep red tests, the failed intermediate schedule attempt, exact
counterexamples, the shortcut probe, parametric verifier, and audit probes.

**Rationale.** The strongest result was found by a failing test: the first
schedule repair did not actually guarantee a witness.  Future agents can rerun
the same probes against later source without reconstructing hypotheses from
prose.

**Alternatives rejected.** Keeping only final green logs would erase the root
cause and make the schedule claim difficult to audit.  Copying complete runtime
trees into notes was rejected in favor of small source-bound reports.

**Failure modes and limits.** Large census evidence is finite and may be bundled
by the packager.  Historical evidence establishes what was tested, not universal
correctness.
