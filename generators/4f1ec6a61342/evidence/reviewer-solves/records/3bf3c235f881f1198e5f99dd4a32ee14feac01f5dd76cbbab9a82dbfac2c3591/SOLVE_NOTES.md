# Observable solve notes

## Information boundary

This fresh solver read only `solve/challenge.json` for puzzle information. It did not inspect the generator, Racket rule, canonical ledger, reference solution, private labels, previous solve explanations, reports, or `solve-blind`. The parent reviewer previously saw the rule during repairs; the fresh solver did not. Therefore the finish record conservatively declares earlier exposure **yes**, and reference consulted **no**.

These notes are an authored summary of observations and actions, not a full model trace.

## Visible observations and hypothesis

Gray (5) walls divide the interiors into rooms. The upper-left value is an integer target. In the three visible demonstrations, the selected rooms contain respectively 4, 2, and 6 red (2) cells, matching the upper-left values. Python component enumeration confirmed the room red counts:

- Demonstration 1, target 4: counts 2, 4, 5; the count-4 room becomes 8.
- Demonstration 2, target 2: counts 2, 5, 3, 1, 4, 3; the count-2 room becomes 8.
- Demonstration 3, target 6: counts 1, 1, 6, 7; the count-6 room becomes 8.

The output preserves gray walls, resets the marker to zero, fills the matching room with 8, and clears all other interiors to zero. The visible query inputs have room counts [1, 2, 0, 3] for target 1 and [0, 4, 5, 0] for target 4. These observations use inputs only and do not establish query correctness.

## Actual revision history

1. Initial implementation: flood-fill orthogonally connected non-gray cells, excluding the upper-left marker; count red cells per component; fill components with the target count using 8 and clear other non-wall cells. No preceding implementation or failed hypothesis was attempted.

## Verification

Pending visible-example checker execution. Query correctness is withheld by the checker and must remain unknown.
