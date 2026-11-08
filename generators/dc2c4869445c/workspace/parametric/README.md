# Native reflection-selection parametric family

This directory contains the native, source-bound parametric adapter for
`dc2c4869445c`.  It is reviewer-ready evidence only: owner integration, fresh
live-byte qualification/acceptance, and any training admission remain pending.

## Settings

`copy_selection` is fixed for one episode:

- `all` — exact canonical default.  Every cue-directed reflected copy is painted.
  `program({"copy_selection":"all"})` returns the selected canonical Racket
  source byte-for-byte.
- `nearest_after_reflection` — first construct every canonical reflected copy,
  then paint only the copy whose **transformed** bounding-box centre is nearest
  the canvas centre.

The alternate preserves the original reasoning: multicolor 8-connected groups,
strict-plurality main-color selection, singleton directional cues, reflection,
and cue-color painting.

## Required sequential dependency

1. **A:** reflect each main shape using each cue's above/below/left/right relation.
2. **Intermediate:** transformed cells and transformed bounding box for every cue.
3. **B:** rank transformed box centres against the canvas centre and paint only
   the nearest copy.

B cannot be chosen before A.  The declared wrong-intermediate rule ranks the
original cue coordinates instead.  On the retained 30x30 protected-Racket case,
that selects a different cue and changes 10 output cells.

## Native contract

- Adapter: `adapter.py`
- Implementation: `prototype.py`
- Promotion contract: `promotion.json`
- Canonical source: `canonical.rkt`
- Source inventory: `evidence/manifest.json`
- Finite audit / export builder: `audit_family.py`
- Cross-artifact validator: `validate_handoff.py`

The adapter supports 2–6 demonstrations and 1–4 query prefixes.  Every full
episode stores exactly four distinct controller-side queries.  Query count is
prefix-stable: generating one query produces the same first visible turn as the
four-query episode.  Public turns contain only demonstrations and the current
query; settings, program, answers, future queries, seed and total query count
stay private.

## Generation and teaching

Inputs are shared byte-for-byte across settings.  The query profiles are
14x18, 20x24, 24x30 and 30x30.  The last query contains three groups, nine cue
candidates, broad occupied row/column spread and boundary-relevant placements;
it is not a padded small puzzle.

The first two demonstrations are selected constructively from a bounded pool so
that all declared rivals are refuted without using query answers.  Rivals cover:
ranking cue positions before reflection, farthest selection, fixed color ranks,
topmost/leftmost selection, selecting the nearest original main shape, row-major
cue selection, direction-only rules, and per-group rather than global selection.
Additional demonstrations preserve that two-example teaching prefix.

## Reproduction

From the packet root:

```bash
python3 review.py run python3 \
  generators/dc2c4869445c/workspace/parametric/audit_family.py \
  --out generators/dc2c4869445c/workspace/parametric/evidence/new-audit

python3 review.py run python3 -m arcpuzzles parametric qualify dc2c4869445c \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/dc2c4869445c/qualification --summary

python3 review.py run python3 \
  generators/dc2c4869445c/workspace/parametric/validate_handoff.py \
  --qualification ../checks/dc2c4869445c/qualification/qualification.json \
  --witness ../checks/dc2c4869445c/sequential-witness.json \
  --manifest generators/dc2c4869445c/workspace/parametric/evidence/manifest.json \
  --audit generators/dc2c4869445c/workspace/parametric/evidence/current/audit.json \
  --task-tests ../checks/dc2c4869445c-tests/result.json \
  --out ../checks/dc2c4869445c/handoff-validation.json
```

Choose new output directories when rerunning immutable evidence builders.

## Current bounded evidence

- 26 focused native tests pass.
- 169 complete staged task tests pass.
- 198/198 deterministic sampled episodes pass over both settings, demo counts
  2/3/6, seeds 0–31 and the maximum accepted seed.
- 12 complete episodes and 56 finite rival cases execute through protected
  Racket: 206 evaluations total.
- Native qualification passes two settings × seeds 0 and 17: four jobs, 40
  protected-Racket evaluations.
- The qualification projection verifies 16 one-query turns.
- The 30x30 causal witness changes 10 final cells under the wrong intermediate.
- The handoff validator checks 19 manifest files and replays two witness programs.

The finite rival set does not prove universal uniqueness or measured learning
gain.  `gap_variant.py` is retained only as an earlier experiment and is not the
promotion contract used here.
