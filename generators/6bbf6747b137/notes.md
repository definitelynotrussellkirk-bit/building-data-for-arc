# Working notes: 6bbf6747b137

## Current rule and sampler

The canonical Racket rule counts color-1 cells in row zero, removes that header,
and retains body components whose area equals the count. It remains the label
authority. The normal sampler produces three orthogonally separated,
monochrome body components with distinct areas, exactly one matching K.

K now uses the keyed, exact-integer override draw in 1..6, including the
canonical K=5 lesson and valid K=1 boundary. Previously the advertised K
control was ignored and every draw used only K=2..4. Distractor areas now sample
two distinct alternatives from 1..6; the previous fixed two smallest alternatives
restricted normal body area sets to {2,3,4}. VERSION is 1.2.0.

## Focused evidence

`tests/test_generator_6bbf6747b137.py` records exact K controls, invalid controls,
and varying target size rank. The unchanged baseline failed 11 tests and passed
1; repaired source passes all 12. `workspace/verify_repair.py` is a runnable
bounded probe: 72 generated scenes across K=1..6 and all difficulty bands,
three explicit degenerate fixtures, and all three canonical labeled pairs.
Actual Racket execution agreed with independently observed matching components
on all 78 cases; two same-body/header-ablation calls produced different labels.
A further 64-seed K=6 probe on the smallest supported 8x8 shape found no missing
body components. These finite checks do not prove all seeds safe.

## Remaining limits

This repair covers K and distractor areas. Other inherited axis declarations are
not a complete exact-control contract: grid_h/grid_w metadata advertises 7..14,
but actual per-band draws permit only 8..10 (easy height fixed at 8); palette,
palette-size and related controls remain unimplemented. Degenerate textures are
fixed fixtures and take precedence over normal K generation. `self_check` remains
a basic header/body check rather than a full three-component validator. The
existing placement failure branch can omit a component after growth exhaustion;
no such omission occurred in the bounded supported-shape probes, and it remains
a known unproven boundary. This work does not change approval or training status.
