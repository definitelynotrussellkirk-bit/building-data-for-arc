# Working notes: b9e736518d82

## Review 2026-10-03 — repair from 3.0.1 to 4.0.0

### Lead and reproduced root cause

Prior return `review-77b34422f50e6b40:v0001` was used only as a lead. It said
ordinary draws were 300/300 marker-bearing simple Ls and omitted the canonical
no-marker branch. The pinned baseline SHA
`67323cc400abb92aec51a5930247903d03e04a2800ab23088a277e11d5d37dfc`
reproduced six blocking battery failures.

Independent canonical reconstruction showed that orange is not the selected
object. Orange is the wall around a latent 0/9 path. Exact walls are:

- every in-bounds cardinal neighbor of the channel not in the channel; plus
- for each turn, the outer corner `cur + incoming - outgoing`.

Canonical semantics have three branches: no marker, straight marker, turn
marker. The no-marker branch is intentionally row-major and not globally
dihedral.

### Implemented design

- Construct a monotone down/right base path and transform it dihedrally.
- Require 2–6 turns and two boundary endpoints.
- Derive exact walls from the path.
- Cycle `none`, `straight`, `turn` every three sample indexes.
- Weight 10×10 as a core profile while preserving exact 10–20 controls.
- Replace dead metadata with four observable axes.
- Add strict reconstruction-based `self_check` and `observe_overrides`.
- Add executable semantic witnesses/rivals and lesson identifiability.
- Keep canonical Racket `program_solution` unchanged.
- Synchronize only selected base `racket_target.target_code`; preserve archival
  `raw_code`.

### Tests and evidence

TDD red logs: `checks/tdd-red-canonical.log`, `checks/tdd-red-full.log`.
Final direct suite: 65 passed in `checks/tdd-green-full-attempt2.log`.
Portable task tests: 65 passed in `checks/task-tests/result.json`.
Final battery: 12/12 green in
`checks/after/checks/b9e736518d82_after_battery_summary.json`.
Independent audit: 1,000 samples, 0 structural failures, 58/58 Racket parity in
`checks/b9e736518d82_independent_audit.json`.

### Remaining limitation

The constructive family is monotone and therefore does not span every lawful
simple orthogonal channel. Expanding to non-monotone paths should only happen
with an explicit no-self-touch / no-band-merge proof and new rival probes.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `96b30f9f8584f8f2b8cc58f411fb9e9fb05f91b925fd83bbff9905fc456662d8`.

# Decisions for review `review-0f4542266a355ae8`

## D1 — Reject malformed public scalars exactly

**Choice.** Validate `seed`, `sample_index`, and `difficulty` before constructing
`gen_ctx`.  `seed` must be an exact `int`; `sample_index` must be an exact
nonnegative `int`; `difficulty` must be `None`, `easy`, `medium`, or `hard`.
Because Python bool is an int subclass, exact type checks are deliberate.

**Why.** The pinned source passed every battery stage except `defect_lint`, which
reproduced 39 accepted-invalid calls.  Silent coercion can merge supposedly
distinct reproducibility recipes or map misspelled difficulty values into a
valid band.

**Alternatives rejected.** Coercing strings/floats to integers would preserve the
defect.  Relying on `gen_ctx` alone would keep task-specific fallback behavior.
Validating only overrides would miss the three public positional/scalar fields.

**Evidence and failure modes.** Thirteen tests failed before the guard and pass
after it.  The change is intentionally narrow; it does not add new generation
branches or modify valid deterministic calls.

## D2 — Use `turn_half` as the sole rule parameter

**Choice.** Prototype exactly one parameter:
`turn_half ∈ {larger, smaller}` for the unequal halves created by a bend marker.
Canonical/default is `larger`.

**Why.** This changes a genuine relational decision while preserving the latent
channel, wall geometry, marker semantics, palette, and all other branches.  It
is small enough to teach within one episode and has an exact one-comparison
Racket delta.

**Alternatives rejected.** Palette swaps are mostly cosmetic and can encourage
color shortcuts.  Changing no-marker component selection would interact with the
authority's row-major asymmetry.  Adding path topology or marker placement as a
rule parameter would conflate input distribution with transformation law.

**Limit.** The probe tests only two settings and one retained episode seed per
setting; it is not a general parameter framework or approval claim.

## D3 — Keep the parameter prototype outside the selected execution path

**Choice.** Put the factory, tests, README, and public examples under
`workspace/parametric/`; do not add the parameter to production `AXES`, modify
`generate`, or edit canonical/base rule sources.

**Why.** The assignment asks for a runnable assessment, not automatic adoption.
Isolation lets maintainers inspect teaching quality without changing existing
data semantics.  The canonical instantiated program remains exact and normalizes
to `RULE_HASH=b8c560eed7ae`.

**Alternative rejected.** Wiring the variant into ordinary draws would silently
mix two laws under one task ID and invalidate the existing ordered lesson
contract.

## D4 — Make each prototype episode identify its fixed setting

**Choice.** Choose the setting once for the entire episode, provide four
demonstrations plus one query, and include two bend-marker demonstrations on
which `larger` and `smaller` disagree.  Strip the setting, Racket text, metadata,
and query answer from the public challenge.

**Why.** A parameter that changes only the query is not learnable.  Directly
executing both programs on every demonstration and the query proves that the
rival is ruled out before evaluation while the query remains discriminative.

**Alternatives rejected.** One bend witness is technically sufficient but more
fragile to future lesson filtering.  Sampling the parameter per pair would cease
to define one coherent ARC rule.

## D5 — Preserve the ordered production lesson contract

**Choice.** Keep the existing three-mode production schedule and report query
rotation as diagnostic, not supported behavior.

**Why.** The 300-lesson census has zero production ambiguity, while 600/1,200
rotations lose a necessary witness.  Repairing every arbitrary holdout would
require a different lesson cardinality or examples that jointly encode multiple
modes, a materially larger redesign unrelated to the scalar defect.

**Alternative rejected.** Claiming rotation support from the ordered pass would
be false.  Expanding production lessons solely for a downstream policy not used
by the current sampler would add cost and change the selected curriculum.

**Operational requirement.** Assemblers must preserve the three demonstrations
and designated query ordering; they must rerun a required-rotation gate before
enabling arbitrary holdouts.

## D6 — Do not alter the canonical Racket authority

**Choice.** Leave canonical program text, selected base target, and normalized
hash unchanged.

**Why.** The reproduced defect is entirely in Python public-call validation.
Rule smoke, execution parity, canonical outputs, semantic checks, and authority
sync already pass.

**Alternative rejected.** Reformatting or “cleaning up” the Racket program would
create needless source churn and a new authority-review burden without fixing a
measured problem.

## D7 — Retain exact large evidence losslessly but compressed

**Choice.** Store the 23 MB full lesson census as
`checks/lesson-census.json.gz`, with original size, SHA-256, and restoration
command in `checks/lesson-census.restoration.json`; retain the readable companion
summary uncompressed.

**Why.** The return has a 25 MiB expanded budget and otherwise includes complete
before/after, test, solve, prototype, and audit evidence.  Gzip is lossless and
the mapping makes byte-for-byte restoration verifiable.

## D8 — Leave audit-only targets unchanged

**Choice.** Record source-bound findings for `d04a3e7210f3` and
`d1dab66b0d54` without editing either target.

**Why.** The audit assignment requests adversarial findings, not repairs.  This
keeps the selected task patch isolated and lets each target owner address its
portable test or semantic distribution defect with its own TDD cycle.
