# Working notes: 8a851bf5cdd7

## Canonical repair

The canonical generator is now version `3.1.0`, source SHA-256
`d5516a3806e79f385735b576162991e2c46c2ba1c2245a076d3752f4d87d96d6`,
with the original rule hash `d2ea4a091d55` unchanged. The invalid
`no_separator` branch and ignored palette/texture controls were removed. The
remaining `variant=0..2` axis changes real occupancy/edit-density profiles.
`self_check` now rejects ragged or malformed three-panel inputs without raising,
and every ordinary lesson makes at least one addition and one deletion visibly
change panel C.

Fresh packet-native tests passed 31/31 with protected Racket. The bounded
canonical audit retained at
`workspace/parametric/evidence/current/canonical-repair-audit.json` passed 96/96
ordinary draws across four difficulty bands; addition-only and deletion-only
rules disagreed with the canonical result on all 96.

## Native parametric family

`workspace/parametric/` retains the forward/reverse edit-stencil family. Forward
uses the exact canonical Racket program; reverse swaps the A/B orientation while
preserving both signed edit branches. Demonstrations identify the selected
setting against the declared finite rival family without query answers. The
contract supports 2–6 demonstrations and four distinct controller-side queries.
The equal-panel grammar has width `3w+2`, so its lawful maximum is 30×29 rather
than 30×30.

The refreshed bounded probe passed 20/20 episodes over seeds 0 and 17, all demo
counts 2–6, both settings, and four queries. It recorded 160 independent-oracle
matches, 8 boundary labels, 1,116 protected-Racket applications, and 4 direct
native-worker compatibility jobs. The source inventory is
`workspace/parametric/evidence/manifest.json`.

Authoring preflight passed at
`checks/8a851bf5cdd7/qualification/qualification.json`: 4 jobs, 2 settings, 24
parametric labeled pairs, 3 canonical pairs, and 32 protected-Racket evaluations.
The source-bound causal witness at `checks/8a851bf5cdd7/causal/witness.json`
shows that reversing the input-derived signed stencil changes the final label.
A fresh public projection produced 16 one-query views; verification and first-turn
privacy checks passed.

## Remaining owner action

This return does not approve the generator, accept a parameter family, or admit
training data. The owner must integrate these exact bytes, review the repaired
base, rerun native qualification, replay the witness, and separately accept the
family.

Current incoming duplicate: `workspace/proposals/review-f37a3de5a3dfe30b/decision.json` retains an alternative ordinary-generator contract. Its forward/reverse programs already match the selected family, but it changes `variant` from area-scaled profiles0..2 to exact edit counts1..3. The current API, scene profiles and accepted source remain selected pending reconciliation.
