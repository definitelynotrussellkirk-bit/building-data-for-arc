# Final-source round-two solve

This is an assistant-authored work log, not a token-level model trace.
Earlier rule exposure: **yes**. I reviewed this generator and wrote a solve on
an intermediate validation revision. That intermediate episode is preserved at
`checks/round2-initial-solve/`; round one's episode is at `checks/round1-solve/`.
Those prior results are not independent evidence for this episode. Prior material
is already in conversation context; this attempt must not be labeled blind.

After final-source preparation, I opened the new public challenge and used only
its visible pairs and new Python probes. I did not reopen generator code,
reference/Racket code, private labels, or earlier solution files during this phase.
The preparation/check tools invoke the reference privately as required.

The new examples have shapes 9x8, 9x9 and 8x12. They alter respectively 3, 3 and 5
zero cells. Every altered cell sits between equal nonzero neighbors on an axis.
Example zero includes both horizontal and vertical changes. The later examples
include boundary-row horizontal gaps. Existing colored cells and shapes stay
unchanged. `visible_probe.json` retains all observations from training pairs only.

Hypothesis: copy the grid, then fill zero cells from matching opposite nonzero
neighbors in the ORIGINAL input. Do not use new fills to generate further fills.
The examples do not identify a priority when both axes propose different colors;
this implementation rejects that unobserved ambiguity explicitly.

The three visible unit tests first failed against the preparation tool's
NotImplementedError scaffold. This is not a failed inferred rule or a teaching
negative. One actual Python revision was then written and checked. No fabricated
failed model attempt, token probability, or independent reasoning trace is claimed.

The official feedback covers visible examples and execution only. The two masked
queries remain unscored here and require independent maintainer evaluation.
