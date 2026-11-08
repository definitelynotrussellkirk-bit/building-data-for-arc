# Fresh visible-example solve work log

This is a reviewer-authored summary of observations and executed experiments,
not a captured model conversation, token-level trace, or log-probability record.
Earlier rule exposure: **yes**, during the preceding generator review. Therefore
this is not a blind solve. During this solve phase, I consulted only
`challenge.json`, my new `solution.py`, and the visible-only test feedback. I did
not reopen the generator, Racket source, reference solutions, or private labels.

## Revision 1 — proposed generalization

The visible examples preserve canvas dimensions and foreground colors. The first
has two colors with two distant markers each; the second has one color with
three markers; the third has three colors with three markers each. In the shown
outputs, each color occupies the four edges of its own input extrema rectangle;
the interior remains background. The first and third examples also exhibit
rectangles on canvas boundaries. These observations motivated one candidate:
group nonzero input cells by color and draw the perimeter of each group's
axis-aligned bounding box onto a blank output of the original size.

## Executed experiment

`python3 solve/probe_visible.py` reads only visible demonstrations and this
candidate. It records per-color marker counts and bounds, exact matches, cell
mismatches, and input-purity results in `visible_probe.json`. Then the provided
`solve_episode.py check --intent solve` evaluates the same candidate under the
visible-only policy. No deliberately wrong rule or artificial failed attempt
was submitted. This is the first actual attempted solution.

## Scope and stopping criterion

Stop after the first candidate matches all visible demonstrations and the
provided checker can execute it. Hidden-query correctness is not disclosed by
this protocol and is not claimed. The examples do not establish how overlapping
or degenerate rectangles should be treated. The candidate is intended for the
visible task's nonoverlapping, nondegenerate scenes.
