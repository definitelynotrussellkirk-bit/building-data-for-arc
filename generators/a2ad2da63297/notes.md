# Working notes: a2ad2da63297

## Current decision

Retain the production generator and canonical Racket authority unchanged. Add a
separate **proposed/unapproved** `crossing_mode` prototype under
`workspace/parametric/`: canonical `cross_through` versus alternate
`compress_to_barrier`. Both modes find the dominant barrier, match opposite-side
dots by lane, move only complete pairs, and land them flush; only whether colors
cross sides changes.

The canonical/default program is exact source SHA-256
`937e30cc1e90881f7f01d4b05e8ec9bbb6a71432bfd75b8e7b744ccc9e2abf1c`.
The alternate uses four guarded destination replacements, covering horizontal and
vertical branches. Seeds `0` and `1` deliberately share visible inputs while
selecting opposite settings. Each retained episode has two identifying
demonstrations and four distinct queries; all labels come from protected Racket.

## Evidence and limits

Focused tests and retained evidence are under
`WORK/checks/parametric/crossing-mode-v1/`. The adversarial pass found no parity or
export-boundary defect across four irregular canonical inputs plus 24 generated
boundary inputs for each setting. Public files exclude settings, seeds, programs,
and query answers and reject non-literal color cells.

The prototype sampler still inherits the production generator's narrow straight-
barrier domain. A later canonical-generator repair should make the declared axes
honest and add irregular/thick barriers, variable dot distances, and unmatched-dot
distractors without changing the canonical Racket rule. Prototype acceptance,
production repair, source approval, and training admission remain separate.
