# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Distribution-contract probe

Run `python3 generators/3977ec54e4a0/workspace/distribution_contract_probe.py`
from the repository root. It independently checks the two geometry defects
repaired in version 4.1.1:

1. `asymmetric_arms` matches exact left/right arm masks over 128 exact-axis draws.
2. Two chevrons at Chebyshev distance 2 remain placeable when the Racket
   authority's aligned-near relation keeps their marker components separate.

## Lesson-contract probe

Run `python3 generators/3977ec54e4a0/workspace/lesson_contract_probe.py`
from the repository root. It imports the generator's actual
`LESSON_COMPETITORS`, checks 12 cyclic lesson starts per difficulty, verifies the
three declared schedule profiles, and reports any incomplete-rule rival that
survives all three demonstrations. Scheduled anchors require exclusive painted
support, so geometric presence alone cannot satisfy the probe. The JSON output is bound to the generator
source hash. This finite rival family is a regression contract, not a proof of
universal induction.
