# Visible-example Python solve

## Exposure and record type
I read this task's Racket rule, generator, canonical examples, and historical
notes during generator review **before** starting this solve. This is not a
blind evaluation. After `python3 solve_episode.py prepare`, I opened only the
public `solve/challenge.json` and my own new Python/work-log files. I did not
consult the generator, earlier Python mirrors, Racket source, reference solutions,
private labels, or previous explanations during the solve. The tool prepared the
challenge using its private reference automatically. These notes are an authored
work log, not a captured token-level model conversation or probability trace.

## Visible observations and hypotheses
There are four demonstration pairs and two answer-masked queries. Demonstration
0 removes colored walls and keeps a one-cell zero pocket plus a two-cell pocket,
painting the retained cells 8 on a fresh zero grid. Demonstration 1 includes a
bent three-cell pocket. Demonstrations 2 and 3 also retain nonrectangular zero
pockets. Large U-shaped regions remain empty in the answers even though colored
walls bound them on three sides. Different nonzero colors cooperate around a
pocket, and diagonal contact with exterior zeros does not empty the pocket.

Hypothesis: traverse zero cells through cardinal neighbors only; discard each
component touching any grid edge; paint all remaining component cells 8. Wall
color and wall-component membership do not determine the answer. Earlier rule
exposure strongly informed this hypothesis; the probes test visible consistency,
not independent discovery.

## Probes and rejected alternatives
`python3 solve/probes.py` compares the hypothesis against all four visible pairs.
The eight-neighbor and rectangular-only candidates are **intentional teaching
negatives**, not accidental failed attempts. Their exact mismatched-cell counts
are retained in `solve/probe_results.json`. No private query answer is read or
scored by these probes. No model-training gain is claimed from this exercise.

## Revision 1
`solution.py` implements component traversal, a border flag, and fresh output
allocation. It checks the input representation and does not mutate it. This is
the only submitted solver revision; no fabricated earlier revisions are implied.
The checker result is retained by `solve_episode.py check`. Stop after visible
exact matching and execution checks: the checker deliberately withholds query
correctness, and further tuning to private feedback would violate the protocol.
