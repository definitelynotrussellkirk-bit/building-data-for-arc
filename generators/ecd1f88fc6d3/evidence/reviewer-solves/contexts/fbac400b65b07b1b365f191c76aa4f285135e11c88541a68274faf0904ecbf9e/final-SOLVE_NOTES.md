# Fresh solve work log — review-201ae2dcbb09941c

## Provenance and boundary

This is an assistant-authored engineering work log, not a captured token-level model conversation and not a blind benchmark. Earlier rule exposure: **yes**. Before this phase I reviewed the generator and its Racket authority and repaired the generator. During this phase I use only `challenge.json`, new Python experiments, and the visible-only check feedback. I do not reopen the generator, reference source, private labels, or previous explanations. Prior knowledge cannot be erased; the experiment is explicitly rule-informed.

The public episode has three demonstrations and two masked query inputs. No query answers or private score files are read. A visible pass is not a masked-query correctness claim.

## Revision 1 — intentional teaching negative

I will deliberately test a code-blind adjacency heuristic: for each color-1..4 marker, any adjacent color-5..9 cell supplies a ray pointing from the seed through that marker, irrespective of the marker's numerical value. This is an **intentional teaching negative**, not an accidental model failure. Its purpose is to preserve an executable contrast against the directed-code hypothesis.

The visible examples include seed/marker pairs, line expansion, disappearance of an extra marker, and replacement of another color along a line. Merely extending every adjacent seed-marker pair should fail when a marker is beside a seed but its number points elsewhere. I will retain the check result and then use a finite mapping search over the visible demonstrations to justify the final code-to-direction mapping.

## Observation from revision 1

The check completed: **2/3 visible demonstrations passed**, and the attempt was labeled locally bad. The first two demonstrations support the adjacency heuristic; the third refutes it. Both the submitted source and the work-log snapshot are retained by the checker under `attempts/0001/`.

## Visible mapping experiment

Command: `python3 solve/probe_visible.py` from the packet root. The script reads only `solve/challenge.json` and searches all 256 assignments of four cardinal directions to codes 1..4; it does not assume a bijection. Within the explicitly stated seed-to-boundary, fresh-output hypothesis class, the visible examples leave one mapping: 1 up, 2 down, 3 left, 4 right. Full search counts are in `visible_probe.json`.

This is a finite-class identifiability check, not a proof that no other program fits the demonstrations. The hypothesis class is informed by my earlier exposure. No reference or private query answers were consulted for this experiment.

## Revision 2 — code-aware rule

Use the surviving mapping. A code fires only when the cell immediately behind it is a seed color. Paint starting at that seed through the marker to the edge on a fresh zero canvas. Other input cells are not copied. This explains both the vanished wrong-side code and the color overwritten along a ray in the third example.

The implementation validates the rectangular ARC grid and does not mutate its input. It scans markers in row-major order, a deterministic convention; overlap precedence is not independently identifiable from these nonoverlapping demonstrations. No claim of learning overlap precedence is made.

## Stopping result

Revision 2 completed and passed **3/3 visible demonstrations**. The checker retained both program revisions and their notes. Masked-query correctness remains withheld for independent maintainer scoring. I stopped because the selected finite hypothesis class has one surviving mapping, the visible examples pass, and no additional public feedback justifies another change. The first revision remains labeled an intentional teaching negative.
