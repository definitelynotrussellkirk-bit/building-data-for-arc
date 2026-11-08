# Fresh visible-example solve log

This is a reviewer-authored experiment log, not hidden token-level reasoning.
Earlier generator/Racket-rule exposure: **yes**, from the repair phase. After
`solve_episode.py prepare` generated this fresh challenge, I used only
`solve/challenge.json`, the generated solve instructions, and new standalone
Python written in this solve directory. I did not reopen the generator, Racket
rule, reference solutions, private labels, or the superseded solve.

## Revision 0000 — required failing baseline

`solve/check_visible.py` was written before the implementation and run against
the generated `NotImplementedError` placeholder. It failed on all four visible
examples and both masked-query execution checks. The exact failure is retained
in `checks/round2-solve-visible-red.log`.

## Public structure analysis

`public-structure-analysis.json` records only facts extracted from the public
pairs. It found two blue rectangular frames in each demonstration. Every frame
has one marker immediately above it, and the input/output object bounding boxes
show these visible clockwise rotations:

- marker 2 -> 0 quarter turns;
- marker 3 -> 1 clockwise quarter turn;
- marker 4 -> 2 clockwise quarter turns;
- marker 5 -> 3 clockwise quarter turns.

Every output object is placed at the floor-centered position within its frame.
All four marker values occur in the visible demonstrations; the masked queries
use markers 3 and 4, so neither query requires an unseen marker extrapolation.

## Bounded hypothesis enumeration

`public_hypothesis_probe.py` enumerated 1,024 candidates: every independent
mapping from markers 2..5 to 0..3 clockwise quarter turns, crossed with
floor/ceiling choices for row and column centering. Exactly one candidate
matched all four visible demonstrations: `{2:0, 3:1, 4:2, 5:3}` with floor
centering on both axes. `public-hypothesis-probe.json` retains the full score
histogram. This establishes uniqueness only inside that declared family, not
among all imaginable ARC rules.

## Revision 0001 — standalone candidate

`solution.py` contains its own frame-component finder, keyed rotation, interior
clearing, and floor-centering logic. It imports no generator, Racket runtime,
ledger, reference solution, or project helper. The public regression check now
matches 4/4 demonstrations, preserves input bytes, and executes both masked
queries while preserving their dimensions. Their private answers remain unread.
