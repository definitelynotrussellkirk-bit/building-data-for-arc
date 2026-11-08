# Transfer the inferred D4 pose

`response_policy=label_query` preserves the exact selected canonical program.
`response_policy=transfer_pose` uses its matching label to recover the selected
prototype, infers the unique rotation/reflection that maps that prototype to
the query, then applies that same map to the **other** prototype. Render the
transformed other shape at the query bounding-box origin, in the other
prototype's label color, on the same output canvas as the canonical query panel.
The rule is fixed within an episode; no parameter is supplied in public inputs.

Every shape is newly grown as a connected polyomino around a random full-span
cross. Both prototypes have the same occupied area and ordered bounding-box
dimensions, but belong to different D4 orbits. Both have eight distinct D4 poses,
so transformation transfer is unambiguous. The first two demos use opposite
match sides, a quarter-turn, and a reflection. No extra demo is required to
reject fixed-pose, inverse-pose, matched-color, recolor-only or first-prototype
rules. Labels, geometry and placements vary by seed. This is a finite authored
rival check, not a claim that no other program could fit the demonstrations.

## Size and sequential-query contract
Counts are independent: 2-6 demonstration prefixes, and 1-4 query prefixes from
four private queries. Six demos/four queries are constructed from seed-only
streams, so requesting a shorter prefix or changing settings cannot alter the
first query or preceding demonstrations. `public_turn(episode,index)` exposes
only demonstrations and one current query input. Do not give a model the full
controller-side four-query file at its first turn.

The input width is **3*panel_width+2**. The maximum legal equal-panel width below
31 is 29, not 30. The substantive stress query is **30x29**, containing three
27x9 asymmetric shapes of 145 cells each, plus full-height separators. This
is not a padded small puzzle. Quarter-turns of these tall shapes do not fit a
nine-column panel, so the stress query uses dimension-preserving transformations;
all eight D4 operations occur on the smaller valid geometries and are executed
through protected Racket. The minimum query is 5x14. Neither production sampler
nor canonical program is modified or widened.

## Reusable bounded audit
From the outer packet directory:

```sh
python3 review.py run python3 generators/1ecf6add3fe7/workspace/parametric/audit.py --seeds 20 --racket-seeds 0 17 2 --out ../checks/1ecf6add3fe7/audit-new
python3 review.py task-tests 1ecf6add3fe7 --phase after --out ../checks/1ecf6add3fe7/tests-new
```

Use a fresh output directory. `audit.py` is a self-contained copy of the
contract-driven harness built during the first task, not an import from that
task or another checkout. It checks count boundaries, input equality between
settings, query-prefix identity, private/future-field noninterference, and
public-byte-hashed exports. It independently executes every declared Racket
hypothesis; a failed executable rival cannot count as elimination. Wrong fixed
poses that do not fit are explicitly clipped, like the Racket paint primitive,
not rejected as runtime errors.

`evidence/current-v2` contains the final 20-seed sweep and protected runs at
seeds 0,17,2, covering all eight orientation codes. `evidence/current` is the
prior passing audit limited to seven protected orientation codes; no broader
coverage was attributed to it. Python request checks and actual protected rule
applications are reported separately. Native qualification, exact-source owner
acceptance, and training admission are separate stages.
