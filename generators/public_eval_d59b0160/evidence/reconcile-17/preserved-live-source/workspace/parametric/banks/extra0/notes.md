# Public d59b0160 — current authoring decisions

First reproduce the key-directed deletion rule on all supplied labels. The
orange background (7), green key border (3), and black panel interiors (0)
retain their semantic roles. A panel is deleted when its palette CONTAINS
all colors in the key; positions, duplicates and additional colors are ignored.

Add `erase_policy=all_matches|area_relay`. After canonical deletion, measure
the largest erased panel; delete the unique surviving equal-area rectangle.
That survivor has a different aspect ratio. Largest-original, smallest-matched,
first-matched, key-cardinality, exact-palette and any-key shortcuts are audited.

Implement tests first, then the two programs and matched input sampler, audit,
protected original labels, authoring preflight and causal substitution. No
registration, owner qualification/acceptance or training admission is performed.

## Repairs and current result
Self-review exposed a genuine shortcut: the receiver was always the second-largest
survivor. Two old demonstrations fit it, but a lawful 30×30 case with another
large unmatched plate disagreed. That protected-Racket before case is retained.
The second demonstration now adds a repeated large unmatched area and reverses
which matched panel has more distinct colors. Three failing regression tests
preceded the repair. The source freezes with 28 isolated tests passing.

A 20-seed count sweep passed 800 requests / 5,200 repeated pair instances,
200 distinct inputs, 400 matched-setting checks and 2,000 public turns. All
11 programs were executed on six pairs at each of two seeds: 132 evaluations.
Preflight passed all four original labels and all four setting/seed jobs.
The 30×30 witness selects area 36 (6×6 source, 4×9 receiver). Substituting the
smallest matched area 16 or global maximum 64 changes the protected output.
A separate replay of the retained teaching case and repaired demos passed.
Evidence: `checks/public_eval_d59b0160/{audit-final,preflight,causal}` plus
`shortcut-before.json` and `shortcut-replay.json` in the return.

One combined shell call was interrupted after its staged tests had passed;
its incomplete audit was rerun from a fresh destination and passed. A one-shot
capture-script settings lookup was corrected before retaining its evidence.
No current source failure remains observed. Next: owner registration, exact
source review, native qualification and separate acceptance. No training admission.
