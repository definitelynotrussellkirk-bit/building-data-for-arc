# e942ce41cbf5 control-4 policy family

`canonical` is the selected Racket rule byte-for-byte. `rank_control4` first
applies the visible transform to the red mask, then compares the occupied-cell
counts of intersection and XOR. Control `4` chooses the smaller result; union
control `3` and XOR control `6` remain canonical.

The transformed red mask and the resulting intersection/XOR counts are the
input-dependent intermediate. Control `4` cannot select its final operation
before that intermediate exists. Inputs are matched across settings,
deterministic, prefix-stable, support 2–6 demonstrations and 1–4 queries, and
retain a genuine 30×30 fourth query. The first two demonstrations show both
possible control-4 outcomes, so an always-intersection or always-XOR shortcut
cannot fit the minimum lesson.
