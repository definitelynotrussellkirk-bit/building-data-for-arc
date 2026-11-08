# Working notes: db63430eeffa

## 2026-10-23 request-contract repair

Assigned source SHA-256 was
`7c732860b8701c13d24771feba4fbaec9103d541a7c8c903ff42c16a596dd581`,
version 2.2.0, canonical rule hash `3e3bf77eb552`. The retained audit showed two
current-source defects: request scalars and unknown overrides were accepted too
permissively, and lawful degenerate textures were declared differently from the
actual degenerate domain.

Version 2.2.1 preserves the canonical Racket rule and rule hash. It now rejects
non-literal or negative `sample_index`, non-literal `seed`, unknown difficulty,
unknown override keys (including keys whose value is `None`), non-literal integer
axes, and invalid orientation/texture values before generation. It also makes
`LAWFUL_DEGENERATE_TEXTURES` exactly equal to `DEGENERATE_TEXTURES`. The canonical
source and all ordinary generation semantics are otherwise unchanged.

Focused staged tests pass eight task-local test methods plus 46 parameterized
subtests for the request contract. Defect lint passes. The full override checker passes its 119,700 planned
draws. The initial override invocation was killed only by an outer 120-second shell
wrapper shorter than the checker's native 580-second allowance; the clean rerun
used the native budget and passed.

## Proposed `path_mode` extension

A separate task-local prototype under `workspace/parametric/` adds one episode-
fixed parameter:

- `both` — exact canonical/default Racket source;
- `diagonal_first` — paint only the diagonal-then-straight path;
- `straight_first` — paint only the straight-then-diagonal path.

Each retained episode has three demonstrations and four distinct queries. Input
sampling is independent of the rule-setting stream. The first four profiles reuse
linked canonical geometry and the last three exercise gap/size boundaries; all
have unequal row/column gaps of at least two so the three settings remain
observably distinct. Demonstrations alone refute both alternate settings.

Prototype tests pass 22/22. Real-Racket evidence contains three episodes, 9 demos,
12 queries, 63/63 Racket/Python matches, 6/6 rivals refuted, and no public-export
finding. A 256-seed / 1,792-input adversarial sweep found no boundary, type,
content-ID, or public/private leakage failure. This is proposed evidence only: it
does not approve a variant, alter production sampling, or admit data to training.

## Supplementary bounded work

The adversarial-witness ticket for `eb3171637821` reproduced an existing lawful
thick-divider witness: the individual-divider-count shortcut fits 8/8 canonical
pairs but disagrees with real Racket on the retained input. The allocation ticket
sampled `7147e98f8173`, `747486860e56`, and `7195f447bb20`; equal catalog weights
masked materially different audit/prototype states. Its one Racket probe showed
that `703a842c8e24` can emit four distinct queries, while its retained
first-body-padding shortcut still fits all eight labels. No peer source was edited
and no new safety finding was asserted.

## Next useful action

For promotion, keep `path_mode` outside production until a fresh reviewer checks
the three exact programs and the public/private writer, then use the existing thin
adapter/promotion route. Separately, the packet tooling should pass a stage's native
time budget through to outer wrappers so a long but healthy check is not
misclassified as interrupted.
