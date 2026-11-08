# Direct versus running-parity local-frame readout

This opt-in family preserves the source puzzle's local coordinate-frame search.
The canonical `direct` setting returns the four occupancy bits unchanged. The
`running_parity` setting computes the same input-dependent occupancy vector and
then emits its cumulative XOR from left to right. The first two demonstrations
use masks `0001` and `0110` in the task's canonical bit order, which distinguish
both declared programs and the finite shortcut family retained in evidence.

`generate(seed, settings, demos, queries)` supports 2–6 demonstrations and 1–4
queries independently. Input sampling is setting-independent. Query profiles are
11×17, 21×29, 30×30, and 6×16; the 30×30 case contains distributed irrelevant
components in colors 1, 5, 6, 7, and 9, while the canonical program continues to
locate the unique 2/3/4 frame and its local color-8 motif.
