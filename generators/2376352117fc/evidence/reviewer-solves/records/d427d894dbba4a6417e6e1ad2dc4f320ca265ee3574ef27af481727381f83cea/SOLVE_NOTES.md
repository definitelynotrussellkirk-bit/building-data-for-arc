# Fresh visible-example solve: review-d348b5aca78b1513

## Provenance and boundary

This is a reviewer-authored work log, not a captured model conversation,
token-level trace, or log-probability record. Earlier rule exposure: **yes**,
during the generator review. This is not a blind capability measurement.
After preparation I read only the public `solve/challenge.json` and my own Python
solution/probe while solving. I did not reopen generator code, the Racket rule,
reference solutions, previous solution explanations, or private labels. The
preparation controller ran its reference automatically; that is not a consulted
solution source. Hidden query correctness is withheld.

## Candidate 1

Implemented one direct candidate in `solution.py`: locate the blue and red
markers, use their displacement to translate green cells, and produce a fresh
zero grid containing only in-bounds cyan targets. The implementation validates
rectangular input and unique markers, preserves its argument, and uses no
repository code or external dependencies.

Visible checks performed by `visible_probe.py`:

- Demo 0: displacement (-3, +4), three source cells, three cyan targets. A target
  occupies the original blue-marker location, so input occupancy is not an
  output obstacle.
- Demo 1: displacement (+3, +3), eight source cells, three surviving targets.
  Per-cell clipping is visible; discarding the entire motif would not fit.
- Demo 2: displacement (+6, +3), six source cells, six cyan targets. This also
  paints a cyan cell at the former blue-marker location.

The probe checks exact output equality and non-mutation on all three visible
demonstrations. It separately evaluates **intentional teaching negatives**:
reversing the displacement, preserving the input, discarding any clipped motif,
and painting only input-background cells. These are deliberate alternative-rule
probes, not accidental failed solution submissions. All-or-nothing is refuted by
demo 1; the obstacle rule is refuted by demos 0 and 2. Full per-demo results are
in `visible_probe.json`.

There is one submitted program revision. No failed solve revisions are invented.
The public checker is the next step; its feedback must be reported as visible
accuracy and execution status only, not hidden-query accuracy.
