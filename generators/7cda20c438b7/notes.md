# Working notes: 7cda20c438b7

## Canonical repair

The canonical generator is now version `2.2.0`, source SHA-256
`9894e0464073c13694653fcdc77a49968cff7d52bcfc776065ad2b53731ddd9f`,
with the original rule hash `ac623b9aa2f6` unchanged. Ignored palette/texture
axes and the identity-producing `no_xs` branch were removed. The declared
`grid_h`, `grid_w`, and `centers` controls are exact and observable. Ordinary
lessons now construct spacing-2 chains of two or three valid X centers, ensuring
that neighboring motifs share arm cells and defeating the isolated-X-only
shortcut.

Fresh packet-native tests passed 27/27 with protected Racket. The bounded
canonical audit retained at
`workspace/parametric/evidence/current/canonical-repair-audit.json` passed 96/96
ordinary draws across four difficulty bands, rejected isolated-only behavior on
all 96, and observed all 24 declared dimension/count override combinations
exactly.

## Native parametric family

`workspace/parametric/` supplies the diagonal/orthogonal center-filling family.
The diagonal setting is the exact canonical Racket authority. Episode inputs are
matched across settings; constructive demonstrations include overlap, partial
motifs, occupied centers, and wrong-color distractors. The contract supports
2–6 demonstrations and four distinct controller-side queries, including
substantive 30×30 cases.

The refreshed bounded probe passed 20/20 episodes over seeds 0 and 17, all demo
counts 2–6, both settings, and four queries. It recorded 882 protected-Racket
applications and 4 direct native-worker compatibility jobs, plus a retained
shared-arm witness distinguishing the canonical rule from isolated-only. The
source inventory is `workspace/parametric/evidence/manifest.json`.

Authoring preflight passed at
`checks/7cda20c438b7/qualification/qualification.json`: 4 jobs, 2 settings, 24
parametric labeled pairs, 4 canonical pairs, and 32 protected-Racket evaluations.
The source-bound causal witness at `checks/7cda20c438b7/causal/witness.json`
uses an orthogonal two-center case with a shared arm and shows that substituting
the diagonal-derived center set changes the final label. A fresh public projection
produced 16 one-query views; verification and first-turn privacy checks passed.

## Remaining owner action

This return does not approve the generator, accept a parameter family, or admit
training data. The owner must integrate these exact bytes, review the repaired
base, rerun native qualification, replay the witness, and separately accept the
family.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/7cda20c438b7/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
