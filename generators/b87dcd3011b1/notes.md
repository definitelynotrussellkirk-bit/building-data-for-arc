# Review notes: b87dcd3011b1

## Canonical rule and repaired generator

The canonical rule is shortest-path search from the single color-2 start to the
single color-3 goal. Color 8 is blocked. Entering either member of an exactly
paired portal color 4, 5, or 6 immediately moves to its mate. Background cells
on the recovered route become color 7.

The original generator had weak/dead control behavior and no explicit semantic
contract. The repaired `2.1.0` generator now has five strict, observable axes:
`grid_h` 8–30, `grid_w` 8–30, `n_portals` 1–3,
`barrier_orientation` vertical/horizontal, and `extra_walls` 0–8. Unknown,
wrongly typed, Boolean-as-integer, out-of-range, and incompatible calls are
rejected. Every generated scene places start and goal on opposite sides of a
complete barrier, so portals are necessary rather than decorative.

A broader gate exposed a curriculum regression: medium and hard default draws
had stopped revisiting the exact canonical size/palette profiles. The default
schedule now inserts source-task anchors in every difficulty band while leaving
all explicit overrides exact. The semantic checker also now accepts the crossed
separator used by the authority examples rather than enforcing the generator's
narrower one-barrier construction.

## Parametric family

The episode-fixed parameter is `portal_policy`:

- `all_pairs` is the byte-exact canonical Racket program and remains default.
- `widest_pair_only` computes the Manhattan separation of every paired portal,
  selects the greatest span with lower-color tie breaking, and enables only that
  pair during BFS.

This is a real sequential dependency. Step A derives an active portal color from
the input; step B uses that value to change the BFS successor graph. The retained
protected-Racket witness selects color 5 with spans `{4: 18, 5: 20, 6: 13}`;
substituting fixed color 4 changes the final grid.

The native adapter supports 3–6 demonstrations and 1–4 queries, always stores
four distinct controller-side queries for qualification, preserves matched
inputs across settings, includes thin dimension-8 and substantive 30×30 cases,
and never changes the canonical default.

## Teaching and adversarial review

The first minimum lesson admitted `max_horizontal`, `nearest_goal`, and
`last_scan` shortcut selectors. The lesson constructor was repaired instead of
raising the demonstration count. Its first canonical example now requires two
different portal pairs in sequence; the next two examples rotate the true widest
color through 5 and 6 while crossing metric, proximity, axis-only, scan-order,
fixed-color, rank, and no-portal shortcuts.

The final finite audit used 48 seeds × 2 settings = 96 episodes, three demos,
four queries, and 15 plausible rival selectors. No rival survived the demos or
changed a query after surviving. This is finite evidence, not a proof of unique
human interpretation.

A final source review found one defect in the reusable audit helper: a one-shot
seed iterator was consumed before its count was reported. A failing regression
test reproduced `0` instead of `2`; the helper now materializes the iterable
once and reports the correct count. The complete task suite is 30 tests.

## Final evidence on current bytes

- Generator SHA-256: `f41168a17b07a916c8417e07b76701749246fa722c157445a427a11b01bf6843`
- Source inventory SHA-256: `26318d13daeba70ff565d25313d28ba06bdd10a9785cb523db9d154c6c4a1e40`
- 30 focused task tests pass.
- Strict override matrix: 11,880/11,880 accepted, no findings.
- Rule smoke: 120/120 applied and fired; 119 distinct outputs; no mutation,
  crash, identity, or out-of-bounds result.
- Semantic gate: 600/600 strict draws; all four authority inputs accepted;
  60/60 no-portal rival claims; 12/12 lessons identifiable; 0/48 ambiguous
  rotations.
- Native authoring preflight: 4 jobs, 2 settings, 28 parametric pairs, 4
  canonical pairs, and 40 protected-Racket evaluations.
- Public projection: 16 independent one-query views; 24 first-turn invariance
  checks and 4 positive controls.
- The verifier accepted the baseline and rejected four copied-bundle mutations:
  leaked answer with forged public hashes, forged source binding, stale program
  receipt with rehashed envelopes, and an unexpected public file.

## Status and limits

The artifact is reviewer-ready. The preflight is explicitly not owner
qualification. Owner source review, fresh native qualification/acceptance, and
training admission remain pending. The final whole-source review was performed
by the implementing reviewer because this harness has no independent subagent;
that is weaker than a separate fresh-context review.
