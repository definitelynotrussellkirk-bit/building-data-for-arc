# Solve work log

I had not opened the task's generator, canonical rule, reference solution, audit evidence, or private labels before this solve. I used only the prepared visible examples and local tests over `challenge.json`.

## Revision 1 — cyan ray projector

Hypothesis: the cyan (`8`) rectangle is the source. Every source row projects left and right, and every source column projects up and down. Rays repaint black (`0`) and red (`2`) cells green (`4`). They stop immediately before any other color. This explains the partial erasure of red rectangles, the stopping at blue/green/other objects, and boundary-reaching rays in all three demonstrations.

Probe: added `test_visible.py`, which loads `solution.py` and compares all visible training outputs exactly. The initial template failed with `NotImplementedError`, establishing the test. Implemented the minimal ray-casting rule using the cyan bounding box and the original input as the blocker map.

Remaining uncertainty: visible examples always contain one rectangular cyan source. The implementation conservatively uses the bounding box of all cyan cells; unusual disconnected cyan sources were not demonstrated.
