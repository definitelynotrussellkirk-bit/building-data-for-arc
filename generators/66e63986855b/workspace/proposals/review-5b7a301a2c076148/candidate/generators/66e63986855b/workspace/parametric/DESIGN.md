# Reflection-extent prototype design

## Intent

Add a task-local, unapproved parametric prototype for ARC family `66e63986855b`
without changing the production generator, canonical Racket authority, rule hash,
or approval state. The hidden rule setting is chosen once per episode and inferred
from labelled demonstrations; every query in that episode uses the same setting.

## Parameter

`reflection_extent ∈ {1, 2}` controls how far each interior row is filled after
finding that row's right frontier `rc` and the outline's global right frontier
`maxc`.

- `2` — canonical/default. Fill `rc+1 .. rc + 2*(maxc-rc)`, equivalently through
  the frontier reflected across `maxc`. The materialized program is byte-for-byte
  the canonical ledger program.
- `1` — proposed alternative. Fill `rc+1 .. maxc`, stopping at the global frontier.

The object roles and reasoning remain unchanged: find the single foreground color,
contiguous occupied row run, endpoint rows, per-row right frontier, and global
frontier; clear the source; skip endpoint rows; fill an interval determined by the
frontier gap. Only the small extent multiplier changes.

Input constraints do not depend on the setting. The selected production generator
already guarantees every interior frontier is left of `maxc`, at least one gap is
at least two, and the canonical extent fits. Therefore the same lawful inputs work
for both settings, and each retained input yields different outputs for the two
settings.

## Approaches considered

1. **Reflection extent `{1,2}` — selected.** It is a bounded count parameter,
   preserves the exact row-front reasoning, uses an already documented plausible
   rival (`fill_only_to_axis`), needs no new input grammar, and has a guarded
   one-site Racket substitution.
2. **Fill direction `{right,left}` — rejected.** Leftward reflection would require
   new margin constraints and input resampling, weakening same-input comparison
   and moving farther from the canonical family.
3. **Source composition `{replace,overlay}` — rejected.** Retaining the outline is
   executable but mostly changes output composition rather than the central
   frontier/reflection operation.

## Episode and export contract

- `reflection_extent` is selected once from deterministic seed parity unless
  explicitly pinned.
- Demo and query counts are independent CLI/API arguments; defaults are three
  demonstrations and four distinct queries.
- Inputs are sampled from the selected generator independently of the hidden
  setting, with duplicate visible inputs rejected.
- All selected-setting and counterfactual labels execute exact materialized Racket.
- Each query is checked against the other declared setting using demonstrations
  only. Query answers are used only after that assessment to verify disagreement.
- Public files contain only labelled demonstrations and unlabeled query inputs.
  Their identifiers are SHA-256 hashes of exact visible bytes and do not depend on
  seed, setting, program text, private metadata, or query answers.
- Private evidence retains settings, accepted indices, exact programs/hashes,
  labels, rival checks, source hashes, runtime identity, and a shared-input witness.

## Non-goals and limits

This does not add a production parametric API, alter canonical bytes, approve the
variant, or admit generated trajectories to training. Evidence covers two declared
settings and bounded seeds; it does not establish unique induction against all
possible programs.
