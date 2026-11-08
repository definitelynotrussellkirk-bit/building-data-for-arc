# Fresh visible-example solve log

## Exposure and boundaries
This is a reviewer-authored work log, not a token-level model trace, captured model conversation, or log-probability record. Earlier exposure: **yes**. I inspected this task's generator and rule during the repair phase, so this attempt is **not blind**. After preparing this episode I read only `solve/challenge.json`, my new visible-only probe and its results. I did not reopen the generator, Racket, reference solution, previous explanations, private labels, or answer files during the solve.

## Visible evidence and experiment
The challenge contains three labeled demonstrations and two unlabeled test inputs. In each demonstration the nonzero frame and source cells persist, while interior zero cells acquire source colors; exterior zeros remain zero. Existing interior 7 cells also persist. The frame is translated, so the solution should not assume fixed offsets or grid sizes.

I compared 18 deliberately parameterized diagnostic hypotheses on the visible demonstrations: three distance measures, three tie policies, and preserve/repaint interior 7. These comparisons are **diagnostic probes**, not accidental failed solve attempts. `visible_probe.py` reads only the visible challenge. Exact mismatch counts and the surviving hypothesis are retained in `visible_probe_results.json`.

The taxicab/lowest-color/preserve-7 candidate is the unique exact match among those tested. I implemented that candidate as a standalone `solve(grid)` using only the input, preserving nonzero cells and filling interior zeros from the original source locations. It copies the input and does not let newly filled pixels become sources.

## Revision record
Revision 1 is a genuine solution attempt. There were no earlier submitted solution revisions and no invented failed attempt. The diagnostic candidate sweep was completed before this submission; its rejected variants were not presented as submitted mistakes.

## Limits
The visible candidates are a finite family. Matching the demonstrations does not prove that the unseen outputs are correct, and the earlier exposure prevents any claim of independent blind induction. Hidden-query correctness is reserved for the maintainer's scoring. Stop after visible-example/execution checks succeed and no exception remains; do not read a private answer to decide whether to revise.
