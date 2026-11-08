# Parametric family: inferred-lattice expansion route

The exact canonical default (`fill_route=below_right`) reconstructs the 5x5
0/8 lattice, finds every anomaly, and paints inferred-zero cells in its clipped
4x4 below-right window.

`fill_route=phase_diagonal` uses the reconstructed clean value at the anomaly as
an input-derived routing cue: inferred zero selects the above-left window;
inferred eight selects below-right.  Both settings share identical inputs.
The first two demonstrations cross inferred phase with binary/colored anomaly
type and are selected only after the declared shortcut bank is eliminated.
Four queries are privately shuffled before prefix selection; the full bank
contains 10x10 and substantive 30x30 scenes.

`adversarial_probe.py` is the bounded reviewer tool for later agents.  It
replays both settings in protected Racket, deduplicates identical program/input
evaluations, periodically restarts the persistent evaluator, attacks the
declared shortcut bank and validator, and retains crossed phase/dimension
controls.  Its finite checks are evidence, not a universal uniqueness proof.
