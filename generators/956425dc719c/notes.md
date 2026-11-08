# Working notes: 956425dc719c

## Current decision

Keep the reviewed canonical generator `2.0.0` unchanged and promote the three-setting `post_select` family (`none`, `largest`, `smallest`). Stage A is always the canonical exactly-one-border filter. Stage B ranks only the orange components that survive stage A.

## Repairs and reversals

The first sampler used fixed survivor sizes 2/4/7, allowing a fixed-size shortcut. It now cycles rank profiles `(2,4,7,10)`, `(3,6,9,12)`, `(1,5,8,11)`, and `(4,7,10,13)`, where the final value is the unique original largest component removed by stage A. The minimum two-demo lesson therefore changes both selected sizes while preserving unique ranks.

A broad seed sweep then found a deterministic visible collision at seed 6, medium difficulty: training slot 4 and query slot 100 aligned on every periodic feature. The sampler now maps the six training and four query slots to disjoint episode indices and assigns the distractor from at least ten clear deterministic positions. The exact collision has a regression, and the 64-seed × four-difficulty sweep passes.

## Current evidence

- `checks/956425dc719c-tests-final/result.json`: 11 task-local tests passed.
- `workspace/parametric/evidence/self-audit.json`: 184 protected-Racket evaluations; 46/46 setting distinctions and 46/46 wrong-order differences.
- `checks/956425dc719c/adversarial-self-review.json`: 256 seeded episodes, 1,536 setting comparisons, and 56 unseen-seed protected-Racket evaluations passed.
- `checks/956425dc719c/qualification/qualification.json`: authoring preflight passed with 42 parametric labels, five original canonical pairs, and 78 protected-Racket evaluations.
- `checks/956425dc719c/causal/witness.json`: ranking before stage A changes the final protected-Racket output.
- `checks/956425dc719c/first-turn.json`: six first turns, 36 private-field invariance checks, and six visible-change controls passed.

## Next owner action

Review the exact integrated source, rerun native qualification and acceptance on that binding, and separately decide training admission. No owner acceptance is claimed here.
