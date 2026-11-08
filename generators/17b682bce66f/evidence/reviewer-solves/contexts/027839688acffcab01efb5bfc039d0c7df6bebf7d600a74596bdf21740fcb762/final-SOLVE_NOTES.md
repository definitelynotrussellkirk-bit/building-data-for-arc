# Example-based solve: review-ef189c36f23d1a7e

## Exposure and scope

Earlier rule exposure: **yes**. Before preparing this episode, I reviewed the
selected generator and its Racket rule as required for the generator repair.
This is therefore an exposed-reviewer solve, not a blind evaluation.
During this solve I used only `challenge.json`, my own Python code/probes, and
public check feedback. I did not reopen the generator, Racket source, reference
solutions, prior solution explanations, or private query labels.

The challenge has three visible pairs and two masked inputs. Prepared challenge
SHA-256: `7712c9226c81736a5fccd04a4ac1657acbdfdf7af28f8e51c1b31ea05d7374fb`.

## Revision 1 — rotation and stamping

Observed transformation: the color-8 source is positioned relative to the single
color-9 marker. Copies are placed about markers 2, 3, 4, and 5, with respectively
0, 1, 2, and 3 clockwise quarter-turns. The copied cells receive color `marker+2`.
The source and reference disappear. The output canvas keeps its dimensions.

Implementation: `solution.py` reads no files, allocates a fresh output, and
processes markers in row-major order. That collision convention is an explicit
assumption influenced by earlier exposure, not a fact uniquely established by
these three examples. In-bounds writing is defensive; clipping behavior is not
identified by the visible examples either.

Experiments and retained results:

- `python3 -m pytest -q solve/test_solution.py` first failed all six tests against
  the provided `NotImplementedError` stub. This is a test-first scaffold failure,
  not a failed rule-inference attempt. The log is retained under `checks/logs/`.
- `python3 solve/public_probe.py` compared 24 assignments of quarter-turns to
  colors with four collision policies (96 declared hypotheses). Only the
  `(0,1,2,3)` rotation assignment survived, but **all four** collision policies
  matched all three demonstrations. These are controlled alternatives, not
  fabricated failed solver revisions.
- The surviving policies make one distinct prediction on masked query 1 and two
  distinct predictions on masked query 2. This is a direct witness of ambiguity
  within the tested hypothesis class. No query label was read or scored.
- The implemented revision passed all six local tests: three exact visible
  comparisons, one nonmutation check, and two dimension/palette execution checks
  on the masked inputs. The last two tests do **not** establish correctness.

`public_probe.py` and `public_probe.json` are retained so the next agent can
reproduce this limited identifiability check without task-source access.

## Stopping criterion and limitations

Submit this single implementation revision to the episode checker. Stop after
visible examples pass and masked queries execute; do not select a collision
policy using hidden feedback. Earlier exposure and the unresolved collision
ambiguity disqualify this episode as evidence of blind generalization. A future
lesson should contain a collision-disambiguating demonstration whenever a query
requires that behavior. No claim of Qwen accuracy or training benefit is made.
