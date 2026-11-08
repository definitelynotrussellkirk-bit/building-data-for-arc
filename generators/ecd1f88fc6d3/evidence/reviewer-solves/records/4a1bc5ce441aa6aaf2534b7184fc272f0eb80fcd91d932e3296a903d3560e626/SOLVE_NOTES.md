# Fresh solve work log — review-201ae2dcbb09941c

## Provenance and boundary

This is an assistant-authored engineering work log, not a captured token-level model conversation and not a blind benchmark. Earlier rule exposure: **yes**. Before this phase I reviewed the generator and its Racket authority and repaired the generator. During this phase I use only `challenge.json`, new Python experiments, and the visible-only check feedback. I do not reopen the generator, reference source, private labels, or previous explanations. Prior knowledge cannot be erased; the experiment is explicitly rule-informed.

The public episode has three demonstrations and two masked query inputs. No query answers or private score files are read. A visible pass is not a masked-query correctness claim.

## Revision 1 — intentional teaching negative

I will deliberately test a code-blind adjacency heuristic: for each color-1..4 marker, any adjacent color-5..9 cell supplies a ray pointing from the seed through that marker, irrespective of the marker's numerical value. This is an **intentional teaching negative**, not an accidental model failure. Its purpose is to preserve an executable contrast against the directed-code hypothesis.

The visible examples include seed/marker pairs, line expansion, disappearance of an extra marker, and replacement of another color along a line. Merely extending every adjacent seed-marker pair should fail when a marker is beside a seed but its number points elsewhere. I will retain the check result and then use a finite mapping search over the visible demonstrations to justify the final code-to-direction mapping.
