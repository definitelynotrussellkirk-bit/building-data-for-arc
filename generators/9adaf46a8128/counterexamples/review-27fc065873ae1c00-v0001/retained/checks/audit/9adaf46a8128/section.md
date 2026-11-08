## 9adaf46a8128

**Findings reproduced; target unchanged.** Source SHA-256:
`6ebe47df62eb74cf28b46409f0a96d9e5c6b8db81455cb79aa6019795b1ff845`.
Executed rule hash: `97f1e4b799fa`; full rule-text SHA-256:
`e13dd9ebbfc8969b5dc799ccf6e87df60b90d361ec30227d3449bacdc268c5d7`.

**A1 — declared color-count overrides are ignored.** With seed `0`, sample index
`0`, and either `palette_size=2` or `n_distinct_colors=2`, the generator returns
exactly the no-override input. The actual distinct-color counts for difficulties
`None`, `easy`, `medium`, and `hard` are respectively `4, 3, 4, 5`. All eight
inputs pass `self_check`, including when the requested override is supplied as
metadata. The source never consumes either control. Both axes advertise `2..5`,
although ordinary inputs necessarily contain background `0`, template `2`, and
separator `5`. Remove unsupported controls or define and enforce a realizable
contract without changing the command-color roles.

**A2 — documented dimension endpoints are unusable.** At seed `0`, index `0`,
each of `grid_h=8`, `grid_h=14`, and `grid_w=10` raises `ValueError` in all four
difficulty modes. These values are inside the declared `8..14` and `10..16`
domains. The per-band `draw_int` bounds exclude them everywhere. Correct the
declared domains or honor the declared endpoints independently of default band
sampling.

**A3 — existing teaching defect remains reproducible.** The current review index
already records the easy-seed-`6` marker-4 ambiguity; this audit independently
replayed it through public Racket-backed generation. Accepted sample indices are
`[0,1,2,3]`, with no rejections. Demonstration marker sets are `[2,3]`, `[1]`, and
`[1,3]`; the query contains `[4]`. The executable `marker4_is_identity` rival
matches all three demonstrations and disagrees with the query at `(0,0)` and
`(1,0)`, where the authority outputs `2` and the rival outputs `0`. This is a
recheck of an existing unresolved finding, not a new discovery. Lessons should
demonstrate an output-changing witness for every command role used in the query.

Evidence is under `checks/audit/9adaf46a8128/`: `audit.json`,
`override-cases.json`, `endpoint-cases.json`, `lesson-reproduction.json`,
`racket.json`, `reproduce.py`, and `commands.json`. The single retained reproducer
command exited `0`, meaning all stated counterexamples reproduced. Four canonical
pairs and four override inputs were also executed through the selected authority;
the canonical labels matched. No full battery or seed census was run, and no
target source, tests, notes, shared code, or catalog was edited.
