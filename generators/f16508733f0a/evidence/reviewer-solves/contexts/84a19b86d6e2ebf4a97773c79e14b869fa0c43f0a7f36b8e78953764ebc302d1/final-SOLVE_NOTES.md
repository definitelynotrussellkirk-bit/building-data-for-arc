# Fresh episode work log

## Exposure and scope
This is an assistant-authored work log, not a verbatim model conversation, token trace, or log-probability record. I previously read the canonical Racket rule and the generator while performing the required generator review. This is therefore **not a blind solve**. After `solve_episode.py prepare`, I read only `solve/challenge.json` and wrote/ran independent Python code. I did not consult the generator, Racket source, reference solutions, private labels, or earlier solution explanations during this solve phase.

## Visible evidence and hypothesis
The three demonstrations keep dimensions and pre-existing nonzero cells unchanged. Added cells complete small same-colour corners. The first demonstration is especially informative: its connected shape gains some cells but leaves an adjacent zero unchanged. I proposed one simultaneous pass over 2x2 windows, filling the sole zero only when the other three cells agree in colour.

## Experiments
`python3 solve/probe_visible.py` evaluates only the three visible training pairs. It compares the proposed solution with two explicitly labelled diagnostic alternatives: ignoring colour agreement and repeating completion to a fixed point. These are hypothesis probes, not failed submitted solve attempts. The exact matching results and mismatch coordinates are retained in `visible_probes.json`.

## Revision 1
`solution.py` independently implements the proposed one-pass rule using the original input for every decision and a separate output copy. It validates rectangular ARC grids and does not mutate its argument. This is the first actual submitted solution; no unsuccessful attempt was fabricated.

## Stopping criterion
Stop after checking all three demonstrations and successful execution on the two masked queries. Query correctness is withheld by the checker and must not be inferred from successful execution. Prior exposure is declared; reference consultation during this phase is declared no.
