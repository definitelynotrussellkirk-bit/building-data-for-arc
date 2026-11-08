# Working notes: b8e2a07c1b6c

## Current decision

Retain production `generator.py` and its approved canonical authority unchanged.
Add a separate **proposed, unapproved** parameter component named
`extension_length` with values `1` and `2`.  Both settings preserve the same
reasoning chain—read the red/magenta arrow, follow its ray through the orange
rectangle, then act immediately after the body—while varying whether one
(canonical) or two consecutive exterior cells become orange.

The default program is byte-for-byte canonical (SHA-256
`7e6a7eb16a212d9b62fd6c9893ce27755d80db7cfb84bf7a75ef8af33f8f02e4`).
The alternate program SHA-256 is
`9e5aa64d865d7ae59f24d7742442efdead4a30250659d9a8f7bb35f2028ee22c`.
The input sampler is independent of the hidden setting, prefix-stable across
requested counts, and requires at least three exterior background cells so the
opposite setting, second-cell-only, and paint-to-edge rivals are all observable.

## Retained implementation and evidence

- Prototype: `workspace/parametric/prototype.py`
- Promotion adapter/contract: `workspace/parametric/adapter.py` and
  `workspace/parametric/promotion.json`
- Focused tests: `tests/test_parametric_extension_length.py`
- Source inventory: `workspace/parametric/evidence/manifest.json`
- Materialized protected-Racket evidence:
  `WORK/checks/parametric/extension-length-v1/` in the return packet

Two retained episodes use seeds 0 and 1, two demonstrations, four distinct
queries, and one fixed setting per episode.  Every selected label and finite
rival prediction was executed through protected Racket.  The canonical default
also replayed every labeled canonical pair.  Public files hash only visible
challenge bytes and exclude settings, seeds, programs, rivals, and query answers.

## Checks and limits

Six focused tests and ten staged task tests passed.  A bounded adversarial probe
covered seeds 0–15 at the maximum 8-demo/8-query request, 256 sampler grids,
48 Racket/Python semantic parity pairs, strict numeric rejection, visible-only
public IDs, and duplicate-output preflight.  This is finite authoring evidence;
it does not establish uniqueness against arbitrary programs, measured learning
benefit, variant acceptance, production approval, or training admission.

## Native qualification and supplementary disposition

The repository's native parametric qualification worker accepted the adapter
contract on four fresh jobs: both `extension_length` settings at seeds 0 and 17,
with two demonstrations and four queries each.  Across 32 protected-Racket
program evaluations, the selected setting was the only surviving declared
setting in every job.  Evidence is retained at
`WORK/checks/parametric/extension-length-qualification/`.  This is bounded
qualification evidence only: `training_admitted` remains false and no production
or allocation change was made.

The sampled `scene_family` API boundary on peer task `683b2102b08c` correctly
round-tripped the advertised `linked` override and rejected an unadvertised
value.  The sampled tool request for peer task `ebe910be6876` is now partly
obsolete: public `arc_repl.isolated_verifier.verify_candidate` successfully
executes complete materialized `(rule! ...)` programs for fail-closed labeled
qualification.  Retain only the narrower request for a persistent, low-overhead
unlabeled batch evaluator; no shared runtime change was made in this return.
