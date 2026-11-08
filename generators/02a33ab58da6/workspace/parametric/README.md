# Proposed ray-tail turn-policy family

The canonical default rotates each red tail perpendicular **toward** the canvas
center. This separate proposal adds one episode-fixed alternative,
`away_from_center`, while preserving the gray/bar/pivot/old-tail reasoning.

The sampler constructs each input without consulting the hidden setting and
reserves both perpendicular destinations. Every demonstration contains both a
clockwise and a counterclockwise center-directed move, so neither fixed-turn
shortcut can survive the labels. Counts are 2–6 demonstrations and 1–4 queries;
the fourth query is a substantive 30×30 scene with eight long motifs and source
contacts on all four boundaries. Canonical production remains unchanged and
continues to use its original 8–24 domain.

Use `adapter.py:program(settings)` and `adapter.py:generate(seed, settings,
demos, queries)`. A sequential controller reveals
`prototype.visible_turn(episode, i)`, which includes all demonstrations and only
the current query input. `verify.py` re-executes both admitted programs plus
fixed-clockwise, fixed-counterclockwise, and no-move rivals through protected
Racket and writes compact task-local evidence. This proposal is not training
admission or canonical approval.
