# Recolor, recompute connectivity, select border components

Native settings are `preprocess=none` (the exact selected canonical program) and
`preprocess=gray_to_blue`. The latter recolors every 5 to 1, recomputes monochromatic
4-connected components, and keeps only components that touch both a horizontal
and a vertical border. Literal corner occupancy is not required.

A is the recoloring-induced merge. Its intermediate is a new component partition
with newly combined border contacts. B tests those contacts on the new partition.
Filtering before recoloring is not equivalent: the bridge-connected pieces were
individually one-axis objects and were already erased. This is a sequential-state
dependency, not simply a per-cell palette substitution.

`generate(seed, settings, demos=3, queries=4)` supports 2–6 demonstrations and
1–4 queries. All four queries are constructed before slicing, and are independent
of demo count and setting. Geometry, corner placement, other colors, bridge cuts,
object density and size vary without changing the episode rule. At 30x30 the
scene contains 295 nonzero cells: dense noncorner and gray corner objects,
successful and failed bridges, a diagonal-only blue distractor, and foreign-color
contact. Production still has its original compact domain; this is a separate
rule-supported native grammar extension.

The first two lessons rotate role locations and expose successful versus
ineffective recolors, same-color disconnected objects, diagonal versus cardinal
connectivity, literal/nonliteral corner cases, more than two kept objects, and
foreign-color contact. A 36-policy finite audit filters from demonstrations only,
then compares surviving predictions with each query. These policies are not a
complete hypothesis class and no universal identifiability is claimed.

Self-review found that the initial grammar never placed a foreign color beside a
kept object after recoloring. A color-blind component finder was then equivalent
on the whole sampled grammar. The revised scene adds an adjacent foreign-color
cell which must be discarded; the old/new source-bound protected-Racket example
and failing/passing regression are retained. The minimum remains two demos.

Use the existing `preview-public export` helper for private seeded shuffling of
the complete four-query bank. `public_turn` projects exactly one selected query;
it neither performs a shuffle nor leaks other turns, settings, code, answers or
query-count hints. Bundle listings and private manifests are controller-only.

From the outer packet root:

```sh
python3 review.py task-tests 515cca15a0b7 --phase after --out ../checks/515cca15a0b7/new-tests
python3 review.py run python3 generators/515cca15a0b7/workspace/parametric/audit_native.py --seeds 16 --out ../checks/515cca15a0b7/new-audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify 515cca15a0b7 --out ../checks/515cca15a0b7/new-qualification --summary
```

All evidence is bounded and reviewer-reported. Native qualification is not owner
acceptance, measured learning benefit or training admission. No production or
shared runtime source is changed. Final code review is author self-review.
