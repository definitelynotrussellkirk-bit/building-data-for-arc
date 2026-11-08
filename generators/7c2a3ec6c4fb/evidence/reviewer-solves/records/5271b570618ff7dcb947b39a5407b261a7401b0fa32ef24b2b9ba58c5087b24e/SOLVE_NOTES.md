# Reviewer solve work log

## Provenance and access boundary

This is an assistant-authored, human-readable work log, not a captured model
conversation, token-level trace, or log-probability record. I saw the assigned
Racket rule and generator earlier while doing the generator review. This is
therefore **not a blind solve**. After `solve_episode.py prepare`, I read only
`solve/challenge.json` and the Python files and diagnostic output written in this
solve directory. I did not consult reference code, the generator, previous
solution explanations, or private query labels during the solve.

## Visible evidence and attempted rule

Each visible output is a tight colored crop already present in the input.
Treating edge- and corner-touching nonzero cells as one multicolor object gives
seven objects in every demonstration. Their exact crop multiplicities are
`[1, 2, 2, 2]`. The sole unpaired colored crop matches each visible output.
Keep internal zeros and color positions; do not rotate, sort colors, or reduce
an object to a color histogram. The first two visible outputs need diagonal
connectivity; a four-neighbor-only interpretation splits them.

## Probe and first revision

`python3 solve/visible_probe.py` independently compared four- and eight-neighbor
segmentation on the three visible demonstrations. The four-neighbor diagnostic
matched 1/3; the submitted eight-neighbor solution matched 3/3. Neither mutated
an input. The diagnostic is a deliberately chosen rival, **not a failed solve
attempt**. It was not submitted as a solve revision. Results are in
`solve/visible_probe.json` and `checks/solve-visible-probe.log`.

The first submitted implementation counts exact crops of eight-connected
multicolor components and returns the sole crop appearing once. It does not
hard-code the visible colors, dimensions, positions, or object count. It raises
on multiple singletons rather than inventing an arbitrary tie-break. No failed
implementation revision was manufactured.

## Limits

The visible data do not identify behavior when there are multiple singleton
crops or no singleton. Query inputs are public, but their reference outputs are
not. Query correctness must be independently scored by the maintainer.
