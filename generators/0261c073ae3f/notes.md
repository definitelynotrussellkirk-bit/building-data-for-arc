# Working notes: 0261c073ae3f

## Review decision

The production generator and canonical XOR rule were retained unchanged at
version `1.3.2`; no base-label or sampler defect was found in the bounded review.
A full native family was added separately under `workspace/parametric/`.

## Native family

The episode-fixed parameter is `boolean_op={xor,or}` with canonical `xor`.
Step A finds the full-height color-5 separator, crops each panel to its nonzero
bounding box, and converts both crops to binary masks. Step B top-left aligns
those masks and applies the selected Boolean operation, painting occupied output
cells with color 7. The full six-demo/four-query bank is generated before
slicing, giving matched inputs and prefix stability for 2–6 demonstrations and
1–4 queries. The fourth query is a substantive 30×30 split-panel case whose
normalized output is 26×13.

The first two demonstrations contain overlap plus cells exclusive to each side
and unequal translations. They refute XOR/OR confusion, AND, one-sided,
complement, and raw-panel rivals. The protected-Racket counterfactual applies OR
to uncropped panels and differs from OR on the correct normalized intermediates.

## Preflight compatibility and limits

This packet's shared authoring preflight assumes a canonical `test` split is a
list; this task's canonical record stores its single test pair as an object.
`preflight_compat.py` is a task-local compatibility entry point that normalizes
only this iteration while retaining the canonical record hash, source binding,
and standard receipt schema. It is reusable until the shared preflight is fixed.

Focused tests: 24 passed. The 32-seed audit covered 192 episodes, 160 protected-
Racket evaluations, 32 counterfactual checks, and 320 distinct inputs with no
observed failure. Authoring preflight, causal replay, 16 sequential public
projections, and first-turn privacy checks passed. These are finite authoring
checks, not owner acceptance or training admission. The next owner action is
source review followed by fresh native qualification and acceptance on the
exact integrated bytes.
