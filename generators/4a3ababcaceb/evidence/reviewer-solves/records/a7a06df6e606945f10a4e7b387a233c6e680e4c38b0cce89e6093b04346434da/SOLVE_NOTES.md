# Final-source visible-example solve work log

Task: 4a3ababcaceb. Final generator hash:
`b29280e7128efaaf0ebc04e84a4b0f2235075eca5ed17855d582981002b42b7f`.

This is a reviewer-written work summary, not a captured token-level model trace.
It is **not blind**: I saw the rule while repairing the generator and had already
completed an earlier episode against version 3.0. I did not open the generator,
Racket source, reference solution, earlier solution explanation, or private
answers during this final solve phase. Inputs to the solve were the newly
prepared `challenge.json` and my own Python candidate/probe.

## Why there is a second episode

The completed version-3.0 episode and all its revisions were preserved in
`checks/solve-3.0/`, with that generator's snapshot. An additional adversarial
review subsequently found purity/sparsity/position shortcuts and changed the
generator to version 3.1. Preparation was therefore repeated for the new source
identity, not to retry a failed or difficult challenge. The final preparation
seed is tool-assigned; it was not selected by me. Neither episode had a
manufactured failure or teaching-negative revision.

## Visible evidence and candidate

The three public demonstrations have full color-9 divider lines separating
same-size tiles. Exactly one tile contains a green marker. Its entire contents
are replaced; other tiles and divider lines remain unchanged. The replacement
is cyan at the offsets occupied by red in the tile with the greatest red count,
and zero at that tile's other offsets. Non-red source cells are not copied.

The first demonstration has a nearly full distractor with fewer red cells; total
occupancy does not determine the source. The second contains a sparser pure-red
alternative with four red cells, while the selected tile has five red cells and
one non-red cell. The third is a one-row layout with a clean marked target.
These observations distinguish occupancy/purity/overlay interpretations without
submitting deliberately wrong solutions.

## Implementation and probe

Wrote `solution.py` from these public examples. It detects full divider rows and
columns, counts red cells within each rectangular tile, identifies the distinct
marked target, and replaces that target with the red mask. It does not import
any project generator or reference code. Unsupported ambiguous layouts raise a
clear exception instead of silently choosing a tied source.

Ran `python3 solve/probe_visible.py`. The retained `visible_probe.json` records
all three exact output comparisons, red counts per tile, changed-cell counts,
and input-mutation checks. All three public examples match without mutation.
Only one genuine solver revision was needed; there was no failed program
revision to retain. The checker is then used for visible-example feedback and
masked-query execution, not private answer scoring.

## Stopping condition and limits

Stop after the visible checker confirms all three examples and execution
completes on the two masked inputs. Masked-query correctness is not available to
this reviewer and must be evaluated independently. This episode does not show
that an unexposed model could discover the rule, nor does it measure Qwen training
gains. Earlier rule exposure is declared `yes`; reference consultation during
this solve is declared `no`.
